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
import logging
from importlib import import_module

from flask import Flask
from flask.config import Config

from flask.ext.script import Server
from . import Manager,Command,Option
from .. import ROOT_NAME
from ..core.db import db
from ..core.models import Site

#from flask.ext.collect import Collect
#from quokka import create_app
#from quokka.core.db import db
#from quokka.ext.blueprints import load_blueprint_commands

#collect = Collect()
#collect.init_script(manager)

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
	from flask import current_app
	app = current_app
	for k,v in app.config.items():
		print("%s=%s" % (k,repr(v)))

class AppCommand(Command):
	capture_all_args = True
	add_help = False
	def __init__(self):
		super(AppCommand,self).__init__()
		self.add_option(Option("-h","--help", dest="help",action="store_true"))

	def __call__(self,app,args, help=False, **kwargs):
		mgr = Manager(app)
		app.init_manager(mgr)
		mgr.handle("manage.py app",args)

class RootManager(Manager):
	def __init__(self, app=None, *a,**kw):
		super(RootManager, self).__init__(*a,**kw)
		self.add_root_options()
		self.add_root_commands()
		self.app = app

	def add_root_options(self):
		self.add_option("-c", "--config", dest="config", required=False, default=None, help="Config file to use")
		self.add_option("-s", "--site", dest="site", required=False, default=ROOT_NAME, help="which Site to run on")
		self.add_option("-v", "--verbose", dest="logging", action="count", default=0, required=False, help="Enable verbose logging")
		self.add_option("-t", "--test", dest="test", action="store_true", required=False, default=False, help="Use the test database")

	def add_root_commands(self):
		self.command(check)
		self.command(config)
		self.add_command("app",AppCommand())
		self.shell(make_shell_context)

	def create_app(self, app=None, **kw):
		if self.app is not None:
			# this can't happen in production
			assert getattr(self.app,'TESTING',False),self.app
			return self.app
		from ..app import create_app
		return create_app(app=app, **kw)

