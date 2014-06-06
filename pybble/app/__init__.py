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
from urllib import urlencode

from flask import Flask, request, g, session, Markup, Response as BaseResponse, current_app, Markup
from flask.config import Config
from flask.templating import DispatchingJinjaLoader
from flask.ext.script import Server
from flask._compat import text_type
from flask.wrappers import Request

from werkzeug import import_string

from .. import FROM_SCRIPT,ROOT_SITE_NAME,ROOT_USER_NAME
from ..core.db import db, NoData,ManyData, init_db, refresh
from ..core.signal import all_apps
from ..core.models.site import Site,App,SiteBlueprint,Blueprint
from ..core.models.config import ConfigVar
from ..core.models.user import User
from ..core.models.types import MIMEtranslator
from ..core.models.object import Object
from ..globals import current_site
from ..manager import Manager,Command
from ..render import ContentData,get_context
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
		return "‹{}.{} ‘{}’›".format(self.__class__.__module__,self.__class__.__name__,refresh(self.site).name if self.site else "??")
	__repr__=__str__
	__unicode__=__str__

class Response(BaseResponse):
	@classmethod
	def force_type(cls,req,env=None):
		if isinstance(req,ContentData):
			vars = {'c':req}
			if isinstance(req.content,Object):
				vars['obj'] = req.content
			return cls(req.render(**vars), content_type=str(req.to_mime))
		else:
			return super(cls,Response).force_type(req,env)

class BaseApp(WrapperApp,Flask):
	"""Pybble's basic WSGI application"""
	config = None
	response_class = Response
	translators = {}

	TEMPLATE=("templates",)

	def __init__(self, site, testing=False, **kw):
		super(BaseApp,self).__init__(site=site,testing=testing, import_name="pybble", template_folder=None, static_folder=None, **kw)

		if site is not None:
			site.signal.connect(self._reload)
		all_apps.connect(self._reload)

		load_app_blueprints(self)
		self.setup()

		for t in MIMEtranslator.q.all():
			self.translators[t.name] = t.mod.init_app(self)

		self.before_request(self._setup_user)
		self.context_processor(get_context)
	
	def create_jinja_environment(self):
		from ..render.jinja import Environment
		return Environment(self)

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
			if not getattr(func,'_no_urlfor',False):
				func(endpoint, values)

	def _setup_user(self, **kw):
		## TODO convert to Flask.login
		if current_app.config.TESTING:
			request.user = User.q.get_by(username=ROOT_USER_NAME)
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
			request.user = User.q.get_by(name="",site=current_site)
	
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

# global default config
cfg_app = None
def make_cfg_app():
	global cfg_app
	if cfg_app is not None:
		return cfg_app
	cfg_app = _fake_app(import_name=os.path.abspath(os.curdir))

	from pybble.core import config as cfg
	cfg_app.config = cfg
	init_db(cfg_app)

#	logging.basicConfig(
#		stream=sys.stderr,
#		level=getattr(logging, cfg['LOGGER_LEVEL']),
#		format=cfg['LOGGER_FORMAT'],
#		datefmt=cfg['LOGGER_DATE_FORMAT']
#	)
	return cfg_app

class _fake_app(WrapperApp,Flask):
	"""
	This class is only used to load the configuration
	and for initial database access
	"""
	def __init__(self,*a,**k):
		k["static_folder"] = None
		super(_fake_app,self).__init__(*a,**k)

def create_app(app=None, config=None, site=ROOT_SITE_NAME, testing=False):
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
		"""

	if config:
		os.environ['PYBBLE'] = config

	make_cfg_app()

	if testing is not None:
		assert testing == cfg_app.config.get('TESTING',False), (testing,cfg_app.config.get('TESTING',False))
	else:
		testing = cfg_app.config.get('TESTING',False)
		assert testing is not None

	with cfg_app.test_request_context('/'):
		if site is None:
			pass
		elif not isinstance(site,Site):
			if site == ROOT_SITE_NAME:
				try:
					site = Site.q.get(Site.parent==None)
				except NoData:
					raise RuntimeError("I cannot find your root site!")
				except ManyData:
					raise RuntimeError("You seem to have more than one root. Fix that (with mgr -S): "+"".join(x for x in Site.q.filter(Site.parent==None)))
			else:
				try:
					try:
						site = Site.q.get_by(domain=text_type(site))
					except NoData:
						site = Site.q.get_by(name=text_type(site))
				except NoData:
					raise RuntimeError("The site ‘%s’ does not exist."%(site,))
				except ManyData:
					raise RuntimeError("The site name ‘%s’ is not unique: %s"%(site," ".join(x.domain for x in Site.q.filter_by(name=text_type(site)))))

		if site is not None:
			site = refresh(site)
		if site is None or site.app is None:
			app = cfg_app
		else:
			app = site.app.mod(site, testing=testing)

	if app is not cfg_app:
		init_db(app)

		@app.url_value_preprocessor
		def bp_url_value_preprocessor(endpoint, values):
			if values:
				request.bp = refresh(values.pop('bp',None))

	with app.app_context():
		logging.disable(logging.NOTSET if app.debug is not None else logging.DEBUG)

		if app.config.URLFOR_ERROR_FATAL is None:
			app.config.URLFOR_ERROR_FATAL = app.debug
		if not app.config.URLFOR_ERROR_FATAL:
			def build_err(error, endpoint, values):
				#return Markup('<a href="#" class="build_error" title="%s (%s)">Bad link</a>') % (endpoint,repr(values))
				return Markup('bad_Link/')+endpoint+"?"+urlencode(values)
			app.url_build_error_handlers.append(build_err)

	return app

def create_site(parent,domain,app,name):
	app = App.q.get_by(name=app)
	site = Site.new(parent=parent, name=name, domain=domain, app=app, superuser=request.user)
	db.session.flush()
	return site

def drop_site(site=None):
	if site is None:
		site = current_site
	elif isinstance(site,string_types):
		try:
			site = Site.q.get_by(name=text_type(site),parent=current_site)
		except NoData:
			site = Site.q.get_by(domain=text_type(site))
	Delete.new(site)

def list_apps():
	path = os.path.dirname(os.path.abspath(__file__))
	dir_list = os.listdir(path)
	for fname in dir_list:
		if os.path.exists(os.path.join(path, fname, '__init__.py')) and \
				not os.path.exists(os.path.join(path, fname, 'DISABLED')):
			yield fname

