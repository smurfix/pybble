#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, division, unicode_literals
##
## This is part of Pybble, a WMS (Whatever Management System) based on
## Jinja2/Haml, Werkzeug, Flask, and Optimism.
##
## Pybble is Copyright © 2009-2014 by Matthias Urlichs <matthias@urlichs.de>,
## it is licensed under the GPLv3. See the file `README.md` for details,
## including an optimistic statements by the author.
##
## This paragraph is auto-generated and may self-destruct at any time,
## courtesy of "make update". The original is in ‘utils/_boilerplate.py’.
## Thus, please do not remove the next line, or insert any blank lines.
##BP

import os
import sys
import logging
from importlib import import_module
from gevent.wsgi import WSGIServer

from flask import Flask
from flask.config import Config

from flask.ext.script import Server
from flask.ext.script.commands import ShowUrls

from werkzeug.exceptions import NotFound
from werkzeug.wsgi import responder

from . import Manager,Command,Option
from .. import ROOT_SITE_NAME
from ..core.db import db
from ..core.session import SubdomainDispatcher
from ..core.models.site import Site,Blueprint
from ..core.signal import all_apps,app_list
from ..app import create_site, list_apps

logger = logging.getLogger('pybble.manager.main')

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
		self.add_option("-s", "--site", dest="site", required=False, default=ROOT_SITE_NAME, help="which Site to run on")
		self.add_option("-S", "--no-site", dest="site", action="store_const", const=None, required=False, help="Do not choose a site")
		self.add_option("-v", "--verbose", dest="verbose", action="count", default=0, required=False, help="Enable verbose logging")
		self.add_option("-t", "--test", dest="testing", action="store_true", required=False, default=False, help="Use the test database")

	def add_root_commands(self):
		from .blueprint import BlueprintManager
		from .app import AppCommand
		from .populate import PopulateCommand
		from .schema import SchemaCommand
		from .mime import MIMEManager
		from .descr import DisManager
		from .obj import RESTManager
		from .site import SiteManager
		from .user import UserManager

		coremanager = Manager()
		coremanager.__doc__ = "Examine and change Pybble's internal data"
		coremanager.command(check)
		coremanager.command(config)
		coremanager.add_command("descr",DisManager())
		coremanager.add_command("mime",MIMEManager())

		#self.add_command("urls",ShowUrls())
		self.add_command("site",SiteManager())
		self.add_command("populate",PopulateCommand())
		self.add_command("schema",SchemaCommand())
		#self.add_command("app",AppCommand())
		self.add_command("blueprint",BlueprintManager())
		self.add_command("obj",RESTManager())
		self.add_command("run",SubdomainServer())
		self.add_command("core",coremanager)
		self.add_command("user",UserManager())
		self.shell(make_shell_context)

	def __call__(self, app=None, **kw):
		if self.app is not None:
			# this can't happen in production
			assert self.app.testing, self.app
			return self.app
		from ..app import create_app
		return create_app(**kw)

############################### Accessing sub-sites by domain

class SubdomainServer(Server):
	"""Actually run the server"""
	def __call__(self,app, host,port,**opts):
		dispatch = SubdomainDispatcher(app.site)
		server = WSGIServer((host,port), dispatch)
		db.commit()
		db.close()
		server.serve_forever()
		
class DeadApp(object):
	def __init__(self, exc,msg):
		self.exc = exc()
		self.msg = msg
	@responder
	def __call__(self,environ,start_response):
		e = self.exc
		e.description = self.msg
		return e

