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
from time import time

from sqlalchemy.orm.exc import NoResultFound

from flask import Flask, request, render_template, g, session, Markup, Response
from flask.config import Config
from flask.templating import DispatchingJinjaLoader
from flask.ext.script import Server

from hamlish_jinja import HamlishExtension
from jinja2 import Template,ChoiceLoader,PackageLoader
from werkzeug import import_string

from .. import ROOT_SITE_NAME
from ..core.db import db
from ..core.models.site import Site
from ..core.models.config import ConfigVar,register_changed
from ..manager import Manager,Command
from ..blueprint import load_app_blueprints

logger = logging.getLogger('pybble.app')

###################################################
# web server setup

class WrapperApp(object):
	"""A dummy app class, used to implement low-weight redirectors"""
	def __init__(self, site, test=None):
		self.site = site
		if not isinstance(self,Flask):
			self.testing = test

		self.read_config(test)

	def make_config(self, instance_relative=None):
		"""called by Flask"""
		return self.read_config()

	def read_config(self, testing=None):
		if self.site is None:
			from pybble.core import config
			return config
			
		cfg = self.site.config

		# override with ext_config settings, no matter what
		cfg._disarm()
		from pybble.core import config
		for k,v in config.items():
			cfg.setdefault(k,v)
		if testing is not None:
			assert testing == cfg['TEST']

		cfg._arm()
		return cfg


class BaseApp(WrapperApp,Flask):
	"""Pybble's basic WSGI application"""
	config = None

	def __init__(self, site, test=False, **kw):
		WrapperApp.__init__(self, site, test=test)

		template_folder = getattr(self.config,"TEMPLATE_ROOT",None)
		if template_folder is None:
			template_folder = os.path.join(os.getcwd(),'templates')
		static_folder = getattr(self.config,"STATIC_ROOT",None)
		if static_folder is None:
			static_folder = os.path.join(os.getcwd(),'pybble','static')

		Flask.__init__(self, site.name, template_folder=template_folder, static_folder=static_folder, **kw)
		if test is not None:
			assert test == self.config.TEST
		self.wsgi_app = CustomProxyFix(self.wsgi_app)
		register_changed(self)

		self.init_routing()
		load_app_blueprints(self)
	
	def create_jinja_environment(self):
		"""Add support for .haml templates."""
		rv = super(BaseApp,self).create_jinja_environment()
 
		rv.extensions["jinja2.ext.HamlishExtension"] = HamlishExtension(rv)
		rv.hamlish_file_extensions=('.haml',)
		rv.hamlish_mode='debug'
		rv.hamlish_enable_div_shortcut=True

		rv.filters['datetime'] = datetimeformat

		rv.globals['site'] = self.site

		## setup package loaders
		apps = set()
		packs = []
		s = self.site
		while s:
			if s.app not in apps:
				apps.add(s.app)
				packs.append(PackageLoader('pybble.app.'+s.app))
				s = s.parent
		packs.append(DispatchingJinjaLoader(self))
		packs.append(PackageLoader('pybble'))
		rv.loader = ChoiceLoader(packs)
		## TODO: inheritance from overridden templates
		## TODO: do the same thing with static files
		return rv

	def select_jinja_autoescape(self, filename):
		"""Returns `True` if autoescaping should be active for the given template name.
		"""
		if filename is None:
			return False
		if filename.endswith('.haml'):
			return True
		return super(BaseApp,self).select_jinja_autoescape(filename)

	@property
	def preserve_context_on_exception(self):
		"""Returns the value of the `PRESERVE_CONTEXT_ON_EXCEPTION`
		configuration value in case it's set, otherwise a sensible default
		is returned.

		Due to the way Flask behaves, this cannot be used while testing.
		"""
		if self.testing:
			return False
		rv = self.config['PRESERVE_CONTEXT_ON_EXCEPTION']
		if rv is not None:
			return rv
		return self.debug

	def init_manager(self, mgr):
		pass
	
	def init_routing(self):
		@self.route('/')
		def index():
			"""Just a generic index page to show."""
			return render_template('index.haml')

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

# global default config
cfg_app = None

class _fake_app(WrapperApp,Flask):
	"""
	This class is only used to load the configuration
	and for initial database access
	"""
	def __init__(self,*a,**k):
		WrapperApp.__init__(self,None)
		Flask.__init__(self,*a,**k)

def create_app(app=None, config=None, site=ROOT_SITE_NAME, verbose=None, test=False):
	"""\
		Setup an app instance. Configuration is loded from
		* local_settings
		* PYBBLE_SETTINGS
		* the database

		:param site: The site name. The default is '_root'; there may be
					more than one one root site
		:param config: A configuration file to load. Default: the PYBBLE
		            environment variable.
		:param test: Required to be identical to config.TESTING.
		:param verbose: Turn on logging.
		"""

	global cfg_app
	if verbose:
		logging.basicConfig(stream=sys.stderr,level=logging.DEBUG)

	if cfg_app is None:
		cfg_app = _fake_app(os.path.abspath(os.curdir))
		if config:
			os.environ['PYBBLE'] = config
		from pybble.core import config as cfg
		cfg_app.config = cfg

		assert test == cfg.get('TESTING',False)
	
	with cfg_app.test_request_context('/'):
		if site is None:
			pass
		elif not isinstance(site,Site):
			try:
				site = Site.q.get_by(domain=site)
			except NoResultFound:
				try:
					site = Site.q.get_by(name=site)
				except NoResultFound:
					if site != ROOT_SITE_NAME:
						raise RuntimeError("The site '%s' does not exist yet."%(site,))
					logger.warn("Creating a new root site")
					site = create_site(None,"localhost","_root",ROOT_SITE_NAME)

		if site is None or site.app is None:
			app = cfg_app
		else:
			app = site.app.mod(site, test=test)

		if verbose:
			logging.basicConfig(
				level=getattr(logging, app.config['LOGGER_LEVEL']),
				format=app.config['LOGGER_FORMAT'],
				datefmt=app.config['LOGGER_DATE_FORMAT']
			)

	return app

def create_site(parent,domain,app,name):
	app_module = import_module("pybble.app."+app)
	assert app_module.App is not None, "App '%s' does not exist"%(app,)
	site = Site(parent=parent, name=name, domain=domain, app=app)
	site.save()
	return site

def list_apps():
	path = os.path.dirname(os.path.abspath(__file__))
	dir_list = os.listdir(path)
	for fname in dir_list:
		if os.path.exists(os.path.join(path, fname, '__init__.py')) and \
				not os.path.exists(os.path.join(path, fname, 'DISABLED')):
			yield fname

