#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

VERSION = (0, 1, 0)

__version__ = ".".join(map(str, VERSION))
__status__ = "Alpha"
__description__ = "Smurf's Magic All-In-One CMS"
__author__ = "Matthias Urlichs"
__email__ = "matthias@urlichs.de"
__license__ = "None. All rightes reserved. For now."
__copyright__ = "Copyright © 2014, Matthias Urlichs"

import os
#from pybble.core.admin import create_admin
#from quokka.core.app import QuokkaApp
	# from .core.middleware import HTTPMethodOverrideMiddleware

try:
	admin = create_admin()
except:
	# Fix setup install:
	# If new environment not return error
	pass

ROOT_NAME = '_root'

import logging
logger = logging.getLogger('pybble.init')

from flask import Flask, request, render_template, render_template_string, g, session, Markup, Response
from flask.config import Config
from pybble.core.db import db
from time import time
import os

from hamlish_jinja import HamlishExtension
from jinja2 import Template

###################################################
# web server setup

class HamlPybble(Flask):
	def __init__(self, name, config=None, **kw):
		template_folder = config.get("TEMPLATE_ROOT",None)
		if template_folder is None:
			template_folder = os.path.join(os.getcwd(),'templates')
		static_folder = config.get("static_ROOT",None)
		if static_folder is None:
			static_folder = os.path.join(os.getcwd(),'statics')

		super(HamlPybble,self).__init__(name, template_folder=template_folder, static_folder=static_folder, **kw)
		self.config = config
		self.wsgi_app = CustomProxyFix(self.wsgi_app)

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


#def setup_app(main=None):
#	app.config.from_object(config)
#	websockets = Sockets(app)
#
#	from zuko.web import ui,admin,user,monitor
#	from zuko.db import register as db_register
#	from zuko.web import register as web_register
#	db_register(app)
#	web_register(app)
#	ui.register(app)
#	admin.register(app)
#	user.register(app)
#	if main is not None:
#		monitor.register(app,websockets,main)
#
#	from zuko.btest import simple_page
#	app.register_blueprint(simple_page, url_prefix="/one", url_defaults={"special":False})
#	app.register_blueprint(simple_page, url_prefix="/two", url_defaults={"special":True})


from pybble.core.models import Site

class _fake_app(Flask):
	pass
	#def __init__(self,config):
	#	self.config = config

ext_config = None
def create_app(site=ROOT_NAME, config=None, test=False, init=False):
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

	global ext_config
	if ext_config is None:
		f_app = _fake_app(os.path.abspath(os.curdir))
		ext_config = f_app.config
		ext_config.from_object(config or ('pybble.test_settings' if test else 'local_settings'))
		if not test:
			ext_config.from_envvar("PYBBLE_SETTINGS", silent=True)
		else:
			ext_config.from_envvar("PYBBLE_TEST_SETTINGS", silent=True)
	
		db.init_app(f_app)

	try:
		site = Site.objects(name=site)[0]
	except IndexError:
		if init is None:
			raise RuntimeError("Site does not exist")
		if site != "_root":
			raise RuntimeError("You cannot initialize a non-root site this way:")
		site = Site(name=site, domain="localhost")
		site.save()
	else:
		if init:
			raise RuntimeError("Site exists")
	cfg = site.config

	# override with ext_config settings, no matter what
	cfg.disarm()
	cfg.update(ext_config)
	cfg.arm()

	app = HamlPybble(site.name, config=cfg)

	# testing trick
	# with app.test_request_context():
#	from quokka.ext import configure_extensions
#	configure_extensions(app, admin_instance or admin)

	# app.wsgi_app = HTTPMethodOverrideMiddleware(app.wsgi_app)
	return app

