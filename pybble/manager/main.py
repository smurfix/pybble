#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, division
##
## This is part of Pybble, a WMS (Whatever Management System) based on
## Jinja2/Haml, Werkzeug, Flask, and Optimism.
##
## Pybble is Copyright © 2014 by Matthias Urlichs <matthias@urlichs.de>,
## it is licensed under the GPLv3. See the file `README.md` for details
## as well as hopeful statements by the author.
##
## This paragraph is auto-generated and may self-destruct at any time.
## Please do not remove the next line, or insert any blank lines before it.
##BP

import os
import sys
import logging
from importlib import import_module
from threading import Lock
from gevent.wsgi import WSGIServer
from mongoengine.errors import DoesNotExist

from flask import Flask
from flask.config import Config
from flask._compat import string_types

from flask.ext.script import Server
from flask.ext.script.commands import ShowUrls
from . import Manager,Command,Option
from .. import ROOT_NAME
from ..core.db import db
from ..core.models import Site,Blueprint
from ..app import create_site
from ..blueprint import create_blueprint,drop_blueprint

class _fake_app(Flask):
	"""
	This class is only used to load the configuration
	and for initial database access
	"""
	pass

def make_shell_context():
	" Update shell. "
	from flask import current_app
	return dict(app=current_app, db=db)

def check():
	"""Prints app status"""
	from flask import current_app
	app = current_app

	from pprint import pprint
	print("App:",)
	print(str(app))
	print("Extensions:")
	pprint(app.extensions)
	print("Modules:")
	pprint(app.blueprints)
    
def config():
	"""Dumps configuration data"""
	from flask import current_app
	app = current_app
	for k,v in app.config.items():
		print("%s=%s" % (k,repr(v)))

############################### Apps

class AppCommand(Command):
	"""Runs app-specific commands"""
	capture_all_args = True
	add_help = False

	def __init__(self):
		super(AppCommand,self).__init__()
		self.add_option(Option("-h","--help", dest="help",action="store_true"))

	def __call__(self,app,args, help=False, **kwargs):
		mgr = Manager(app)
		app.init_manager(mgr)
		mgr.handle("manage.py app",args)

def list_apps():
	path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"app")
	dir_list = os.listdir(path)
	for fname in dir_list:
		if os.path.exists(os.path.join(path, fname, '__init__.py')) and \
				not os.path.exists(os.path.join(path, fname, 'DISABLED')):
			yield fname

############################### Sites

def list_sites(site,level=0):
	if level:
		prefix=u"  "*((level-1)*2) + u"↳ "
	else:
		prefix=""
	
	print(prefix+site.domain,site.app,site.name)
	level += 1
	for s in site.children:
		list_sites(s,level)

class AddSiteCommand(Command):
	"""Add a new sub-app"""
	add_help = False

	def __init__(self):
		super(AddSiteCommand,self).__init__()
		self.add_option(Option("-?","--help", dest="help",action="store_true",help="Display this help text and exit"))
		self.add_option(Option("name", nargs='?', action="store",help="The new site's name"))
		self.add_option(Option("app", nargs='?', action="store",help="The Pybble app module to install"))
		self.add_option(Option("domain", nargs='?', action="store",help="The domain to listen to"))

	def __call__(self,app_, args=(), domain=None,app=None,name=None, help=False):
		if help or domain is None:
			self.parser.print_help()
			print("Available apps: "+" ".join(list_apps()),file=sys.stderr)
			sys.exit(not help)
		create_site(app_.site,domain,app,name)
		
class SitesCommand(Command):
	"""Show a list of known sites"""
	add_help = False

	def __call__(self,app):
		list_sites(app.site)
		
############################### Root

class RootManager(Manager):
	def __init__(self, app=None, *a,**kw):
		super(RootManager, self).__init__(*a,**kw)
		self.add_root_options()
		self.add_root_commands()
		self.app = app

	def add_root_options(self):
		self.add_option("-c", "--config", dest="config", required=False, default=None, help="Config file to use")
		self.add_option("-s", "--site", dest="site", required=False, default=ROOT_NAME, help="which Site to run on")
		self.add_option("-v", "--verbose", dest="verbose", action="count", default=0, required=False, help="Enable verbose logging")
		self.add_option("-t", "--test", dest="test", action="store_true", required=False, default=False, help="Use the test database")

	def add_root_commands(self):
		from .blueprint import BlueprintManager

		self.command(check)
		self.command(config)
		self.add_command("urls",ShowUrls())
		self.add_command("new",AddSiteCommand())
		self.add_command("sites",SitesCommand())
		self.add_command("app",AppCommand())
		self.add_command("blueprint",BlueprintManager())
		self.add_command("run",SubdomainServer())
		self.shell(make_shell_context)

	def create_app(self, app=None, **kw):
		if self.app is not None:
			# this can't happen in production
			assert self.app.testing, self.app
			return self.app
		from ..app import create_app
		return create_app(**kw)

############################### Accessing sub-sites by domain
## (need

class SubdomainServer(Server):
	"""Actually run the server"""
	def __call__(self,app, host,port,**opts):
		dispatch = SubdomainDispatcher(app.site)
		server = WSGIServer((host,port), dispatch)
		server.serve_forever()
		
class SubdomainDispatcher(object):
	"""
	This code creates individual app instances (one per site) and sends
	requests to the correct one.

	:param root: Only dispatch to sites within this sub-hierarchy
	"""
	def __init__(self, root=ROOT_NAME):
		if isinstance(root,string_types):
			root = Site.objects.get(name=root)
		self.root = root
		self.lock = Lock()
		self.instances = i = {}
		for r in root.children_tree:
			i[r.domain] = r
			# This pre-loads the instances with the sites necessary to
			# later instantiate the apps.

	def get_application(self, host=None, site=None):
		if site:
			assert host is None
			host = site.domain
		else:
			host = host.split(':')[0]
		with self.lock:
			app = self.instances[host]
			if isinstance(app,Site):
				# first request: create an instance and re-save in
				# `self.instances` for convenience
				from ..app import create_app
				self.instances[host] = app = create_app(site=app)
			app.pybble_dispatcher = self
			return app

	def __call__(self, environ, start_response):
		"""Standard WSGI"""
		app = self.get_application(environ['HTTP_HOST'])
		return app(environ, start_response)

