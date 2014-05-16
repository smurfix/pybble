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
from time import time
from itertools import chain

from flask import Flask, request, render_template, g, session, Markup, Response as BaseResponse, current_app
from flask.config import Config
from flask.templating import DispatchingJinjaLoader
from flask.ext.script import Server
from flask._compat import text_type
from flask.wrappers import Request

from hamlish_jinja import HamlishExtension
from werkzeug import import_string

from .. import FROM_SCRIPT,ROOT_SITE_NAME,ROOT_USER_NAME
from ..core.db import db, NoData, init_db, refresh
from ..core.signal import all_apps
from ..core.models.site import Site,App,SiteBlueprint,Blueprint
from ..core.models.config import ConfigVar
from ..core.models.user import User
from ..manager import Manager,Command
from ..render import ContentData
from ..blueprint import load_app_blueprints

logger = logging.getLogger('pybble.app')

###################################################
# web server setup

class _missing: pass
class cached_config(object):
	def __get__(self, obj, type=None):
		if obj is None:
			return self
		value = obj.__dict__.get('config', _missing)
		if value is _missing:
			if obj.site is None:
				return None
			value = obj.site.config
			obj.__dict__['config'] = value
		return value

class WrapperApp(object):
	"""A dummy app class, used to implement low-weight redirectors;
		also holds the app's configuration"""
	config = cached_config()
	site = None

	def __init__(self, site=None, testing=None, **kw):
		self.site = site
		super(WrapperApp,self).__init__(**kw)
		if not hasattr(self,'testing'):
			self.testing = testing
		elif testing is not None:
			assert self.testing == testing

		self.read_config(self.testing)

	def make_config(self, instance_relative=None):
		"""called by Flask"""
		return self.read_config()

	def read_config(self, testing=None):
		if self.site is None:
			from pybble.core import config
			return config
			
		cfg = self.site.config
		if testing is not None:
			assert testing == cfg['TESTING']
		return cfg
	
	def _reload(self,sender,**kw):
		"""Blinker signal processor to reload my configuration"""
		### this might also invalidate cached data or whatever
		### note that the site has its own listener
		pass
	
	def __str__(self):
		return "‹{}.{} ‘{}’›".format(self.__class__.__module__,self.__class__.__name__,self.site.name if self.site else "??")
	__repr__=__str__
	__unicode__=__str__

class Response(BaseResponse):
	@classmethod
	def force_type(cls,req,env=None):
		if isinstance(req,ContentData):
			resp = cls(req.content, content_type=str(req.from_mime))
			return resp
		else:
			return super(cls,Response).force_type(req,env)

class BaseApp(WrapperApp,Flask):
	"""Pybble's basic WSGI application"""
	config = None
	response_class = Response

	def __init__(self, site, testing=False, **kw):
		super(BaseApp,self).__init__(site=site,testing=testing, import_name="pybble", template_folder=None, static_folder=None, **kw)

		self.wsgi_app = CustomProxyFix(self.wsgi_app)

		if site is not None:
			site.signal.connect(self._reload)
		all_apps.connect(self._reload)

		load_app_blueprints(self)
		self.setup()

		self.before_request(self._setup_site)
		self.before_request(self._setup_user)
	
	def _setup_site(self, **kw):
		if current_app.site is None:
			request.site = None
		else:
			request.site = refresh(current_app.site)
		
	def inject_url_defaults(self, endpoint, values):
		"""Injects the URL defaults for the given endpoint directly into
		the values dictionary passed.  This is used internally and
		automatically called on URL building.

		Fix: Blueprint endpoints may not be dotted.
		"""
		funcs = self.url_default_functions.get(None, ())
		if '.' in endpoint:
			bp = endpoint.split('.', 1)[0]
			funcs = chain(funcs, self.url_default_functions.get(bp, ()))
		for func in funcs:
			func(endpoint, values)

	def _setup_user(self, **kw):
		## TODO convert to Flask.login
		if current_app.config.TESTING:
			request.user = request.site.owner
		elif 'user' in session:
			request.user = User.q.get_by(id=session.user)
		elif FROM_SCRIPT:
			try:
				root = Site.q.get_by(name=ROOT_SITE_NAME)
			except NoData:
				logger.warn("No root site was found.")
				request.user = None
			else:
				try:
					request.user = User.q.get(User.site == root, User.username==ROOT_USER_NAME)
				except NoData:
					logger.warn("No root user was found.")
					request.user = None
		else:
			request.user = User.q.get_by(name="",site=request.site)
	
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
	
	def setup(self):
		"""
		Do everything necessary to get the app into a state where it can
		serve requests.
		"""
		pass

	# Note that there is no `teardown` call.
	# Your app needs to be able to restart after being forcibly terminated.

def _blueprint(self):
	"""The name of the current blueprint"""
	if self.url_rule and '.' in self.url_rule.endpoint:
		return self.url_rule.endpoint.split('.', 1)[0]
Request.blueprint = property(_blueprint)

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
		k["static_folder"] = None
		super(_fake_app,self).__init__(*a,**k)

def create_app(app=None, config=None, site=ROOT_SITE_NAME, verbose=None, testing=False):
	"""\
		Setup an app instance. Configuration is loaded from
		* local_settings
		* PYBBLE_SETTINGS
		* the database

		:param site: The site name. The default is '_root'; there may be
					more than one one root site
		:param config: A configuration file to load. Default: the PYBBLE
		            environment variable.
		:param testing: Required to be identical to config.TESTING.
		:param verbose: Turn on logging.
		"""

	global cfg_app

	if cfg_app is None:
		cfg_app = _fake_app(import_name=os.path.abspath(os.curdir))
		if config:
			os.environ['PYBBLE'] = config
		from pybble.core import config as cfg
		assert testing == cfg.get('TESTING',False), (testing,cfg.get('TESTING',False))
		cfg_app.config = cfg

		if verbose:
			if app:
				cf = app.config
			else:
				cf = cfg
			logging.basicConfig(
				stream=sys.stderr,
				level=getattr(logging, cf['LOGGER_LEVEL']),
				format=cf['LOGGER_FORMAT'],
				datefmt=cf['LOGGER_DATE_FORMAT']
			)
	
	with cfg_app.test_request_context('/'):
		if site is None:
			pass
		elif not isinstance(site,Site):
			try:
				site = Site.q.get_by(domain=text_type(site))
			except NoData:
				try:
					site = Site.q.get_by(name=text_type(site))
				except NoData:
					raise RuntimeError("The site '%s' does not exist yet."%(site,))

		if site is not None:
			site = refresh(site)
		if site is None or site.app is None:
			app = cfg_app
		else:
			app = site.app.mod(site, testing=testing)

	@app.url_value_preprocessor
	def bp_url_value_preprocessor(endpoint, values):
		if values:
			request.bp = values.pop('bp',None)

	init_db(app)
	return app

def create_site(parent,domain,app,name):
	app = App.q.get_by(name=app)
	site = Site(parent=parent, name=name, domain=domain, app=app)
	db.flush()
	return site

def drop_site(site=None):
	if site is None:
		site = request.site
	elif isinstance(site,string_types):
		try:
			site = Site.q.get_by(name=text_type(site),parent=request.site)
		except NoData:
			site = Site.q.get_by(domain=text_type(site))
	Delete(site)

def list_apps():
	path = os.path.dirname(os.path.abspath(__file__))
	dir_list = os.listdir(path)
	for fname in dir_list:
		if os.path.exists(os.path.join(path, fname, '__init__.py')) and \
				not os.path.exists(os.path.join(path, fname, 'DISABLED')):
			yield fname

