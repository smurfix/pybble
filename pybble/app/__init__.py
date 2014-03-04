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
from time import time
from importlib import import_module

from flask import Flask, request, render_template, render_template_string, g, session, Markup, Response
from flask.config import Config
from flask.ext.script import Server

from hamlish_jinja import HamlishExtension
from jinja2 import Template

from .. import ROOT_NAME
from ..core.db import db
from ..core.models import Site,ConfigVar,register_changed
from ..manager import Manager,Command

logger = logging.getLogger('pybble.app')

###################################################
# web server setup

class BaseApp(Flask):
	config = None

	def __init__(self, site, test=False, **kw):
		self.site = site
		self.read_config(test)

		template_folder = self.config.get("TEMPLATE_ROOT",None)
		if template_folder is None:
			template_folder = os.path.join(os.getcwd(),'templates')
		static_folder = self.config.get("STATIC_ROOT",None)
		if static_folder is None:
			static_folder = os.path.join(os.getcwd(),'statics')

		super(BaseApp,self).__init__(site.name, template_folder=template_folder, static_folder=static_folder, **kw)
		self.wsgi_app = CustomProxyFix(self.wsgi_app)
		register_changed(self)

	def create_jinja_environment(self):
		"""Add support for .haml templates."""
		rv = super(HamlQuokka,self).create_jinja_environment()
 
		rv.extensions["jinja2.ext.HamlishExtension"] = HamlishExtension(rv)
		rv.hamlish_file_extensions=('.haml',)
		rv.hamlish_mode='debug'
		rv.hamlish_enable_div_shortcut=True

		rv.filters['datetime'] = datetimeformat
		return rv

	def select_jinja_autoescape(self, filename):
		"""Returns `True` if autoescaping should be active for the given template name.
		"""
		if filename is None:
			return False
		if filename.endswith('.haml'):
			return True
		return super(HamlQuokka,self).select_jinja_autoescape(filename)

	def init_manager(self, mgr):
		pass
	
	def make_config(self, testing=None):
		if self.config is not None:
			return self.config
		cfg = self.site.config

		# override with ext_config settings, no matter what
		cfg.disarm()
		if testing is None:
			testing = self.testing
		if not testing:
			cfg.from_object("local_settings")
		else:
			cfg.from_object("pybble.test_settings")
		cfg.arm()
		return cfg

	def read_config(self, testing=None):
		self.config = None # force re-read
		self.config = self.make_config(testing)

	def setup(self):
		"""
		Do everything necessary to get the app into a state where it can
		serve requests.
		"""
		pass

	# Note that there is no `teardown` call.
	# Your app needs to be able to restart after being forcibly terminated.

def datetimeformat(value, format='%d-%m-%Y %H:%M %Z%z'):
	if isinstance(value,(int,float)):
		value = datetime.utcfromtimestamp(value)
	return value.astimezone(TZ).strftime(format)

class CustomProxyFix(object):
	def __init__(self, app):
		self.app = app
	def __call__(self, environ, start_response):
		host = environ.get('HTTP_X_FORWARDED_HOST', '')
		if host:
			environ['HTTP_HOST'] = host
		return self.app(environ, start_response)

#from flask.ext.collect import Collect
#from quokka import create_app
#from quokka.core.db import db
#from quokka.ext.blueprints import load_blueprint_commands

#collect = Collect()
#collect.init_script(manager)

# global default config
cfg_app = None

class _fake_app(Flask):
	"""
	This class is only used to load the configuration
	and for initial database access
	"""
	pass

def create_app(app=None, config=None, site=ROOT_NAME, logging=None, test=False):
	"""\
		Setup an app instance. Configuration is loded from
		* local_settings
		* PYBBLE_SETTINGS
		* the database

		:param site: The site name. The default is '_root'; there may be
					more than one one root site
		:param config: A configuration file to load. Default is
					`local_settings` in production or `pybble.settings`
					in test mode.
		:param init: A flag to initialize a root.
					Non-roots are created by explicit command.
		"""

	global cfg_app
	if cfg_app is None:
		cfg_app = _fake_app(os.path.abspath(os.curdir))
		ext_config = cfg_app.config

		if config:
			ext_config.from_object(config)
		else:
			ext_config.from_object("pybble.settings")

			if not test:
				ext_config.from_object("local_settings")
			else:
				ext_config.from_object("pybble.test_settings")

			envvar = "PYBBLE_SETTINGS" if not test else "PYBBLE_TEST_SETTINGS"
			if envvar in os.environ:
				ext_config.from_envvar(envvar)
	
	db.init_app(cfg_app)
	for k,v in cfg_app.config.items():
		try:
			ConfigVar.get(k)
		except IndexError:
			logger.warn("Adding config default: %s = %s", k,repr(v))
			ConfigVar.exists(k,"Default")

	try:
		site = Site.objects(name=site)[0]
	except IndexError:
		if site != "_root":
			raise RuntimeError("The site '%s' does not exist yet."%(site,))
		logger.warn("Creating a new root site")
		site = Site(name=site, domain="localhost")
		site.save()

	app_module = import_module("pybble.app."+site.app)
	app = app_module.App(site)

	if logging:
		logging.basicConfig(
			level=getattr(logging, app.config['LOGGER_LEVEL']),
			format=app.config['LOGGER_FORMAT'],
			datefmt=app.config['LOGGER_DATE_FORMAT']
		)

	return app

#@manager.command
#def populate():
#   """Populate the database with sample data"""
#   from quokka.utils.populate import Populate
#   Populate(db)()
#
#
#@manager.command
#def show_config():
#   "print all config variables"
#   from pprint import pprint
#   print("Config.")
#   pprint(dict(app.config))
#
#manager.add_command("run0", Server(
#   use_debugger=True,
#   use_reloader=True,
#   host='0.0.0.0',
#   port=8000
#))

#load_blueprint_commands(manager)

