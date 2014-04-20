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

from flask import Flask
from flask.config import Config
from flask._compat import string_types

from flask.ext.script import Server
from flask.ext.script.commands import ShowUrls
from . import Manager,Command,Option
from .. import ROOT_NAME
from ..core.db import db
from ..core.models.site import Site,Blueprint
from ..app import create_site, list_apps

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
		from .app import AppCommand
		from .site import AddSiteCommand,SitesCommand
		from .populate import PopulateCommand
		from .content import ContentManager

		coremanager = Manager()
		coremanager.__doc__ = "Examine and change Pybble's internal data"
		coremanager.command(check)
		coremanager.command(config)
		coremanager.add_command("data",ContentManager())

		self.add_command("urls",ShowUrls())
		self.add_command("new",AddSiteCommand())
		self.add_command("sites",SitesCommand())
		self.add_command("populate",PopulateCommand())
		self.add_command("app",AppCommand())
		self.add_command("blueprint",BlueprintManager())
		self.add_command("run",SubdomainServer())
		self.add_command("core",coremanager)
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

