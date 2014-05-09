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

from flask import Flask, request, render_template, g, session, Markup, Response, current_app
from flask.config import Config
from flask.templating import DispatchingJinjaLoader
from flask.ext.script import Server
from flask._compat import text_type

from hamlish_jinja import HamlishExtension
from jinja2 import Template,BaseLoader, TemplateNotFound
from werkzeug import import_string
from blinker import Signal

from .. import FROM_SCRIPT,ROOT_SITE_NAME,ROOT_USER_NAME
from ..core.db import db, NoData, register
from ..core.signal import all_apps
from ..core.models.template import Template as DBTemplate
from ..core.models.site import Site,App,SiteBlueprint,Blueprint
from ..core.models.config import ConfigVar
from ..core.models.user import User
from ..manager import Manager,Command
from ..blueprint import load_app_blueprints
from ..render import load_app_renderer

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

	def __init__(self, site, testing=None):
		self.site = site
		if not isinstance(self,Flask):
			self.testing = testing

		self.read_config(testing)

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
		self.config._reload(name=kw.get('name',None))
	
class SiteTemplateLoader(BaseLoader):
	def __init__(self, site):
		self.site = site

	def get_source(self, environment, template):
		"""\
			Find a template.

			* attached to "self"
			* if this is a site:
			  * if the template name contains a slash,
			    * attached to the SiteBlueprint
			    * attached to the Blueprint
			  * attached to the app
			* recurse to my parent
			"""
		seen = set()
		s = self.site
		template = text_type(template)
		while s is not None:
			if s in seen:
				break
			seen.add(s)
			t = None
			try: t = DBTemplate.q.get_by(site=s,name=template)
			except NoData:
				if isinstance(s,Site):
					i = template.find('/')
					if i >0:
						try: # the name might refer to a SiteBlueprint
							sbp = SiteBlueprint.q.get_by(parent=s,name=template[:i])
						except NoData: # or to the Blueprint it points to
							try:
								bp = db.query(SiteBlueprint).filter(SiteBlueprint.parent==s).join(Blueprint, SiteBlueprint.superparent).filter(Blueprint.name==template[:i]).limit(1).one().blueprint
							except NoData:
								bp = None
						else:
							# we get here if the prefix refers to a SiteBlueprint entity
							try:
								t = DBTemplate.q.get_by(parent=sbp, name=template[i+1:])
							except NoData:
								# not found, so check the blueprint
								bp = sbp.blueprint
						if t is None and bp is not None:
							try: t = DBTemplate.q.get_by(parent=bp, name=template[i+1:])
							except NoData: pass
					if t is None and i>0 and s.app.name == template[:i]:
						try: t = DBTemplate.q.get_by(parent=s.app, name=template[i+1:])
						except NoData: pass

			if t is not None:
				mtime = t.modified
				def t_is_current():
					db.refresh(t,('modified',))
					return mtime == t.modified
				return t.data, template, t_is_current

			if not s.parent:
				break
			if s.parent in seen:
				s = s.superparent or s.parent.superparent
			else:
				s = s.parent
		raise TemplateNotFound(template)

class BaseApp(WrapperApp,Flask):
	"""Pybble's basic WSGI application"""
	config = None

	def __init__(self, site, testing=False, **kw):
		WrapperApp.__init__(self, site, testing=testing)

		template_folder = getattr(self.config,"TEMPLATE_ROOT",None)
		if template_folder is None:
			template_folder = os.path.join(os.getcwd(),'templates')
		static_folder = getattr(self.config,"STATIC_ROOT",None)
		if static_folder is None:
			static_folder = os.path.join(os.getcwd(),'pybble','static')

		Flask.__init__(self, site.name, template_folder=template_folder, static_folder=static_folder, **kw)
		if testing is not None:
			assert testing == self.config.TESTING
		self.wsgi_app = CustomProxyFix(self.wsgi_app)

		self.signal = Signal()
		self.signal.connect(self._reload)
		all_apps.connect(self._reload)

		load_app_renderer(self)
		load_app_blueprints(self)
		self.setup()

		self.before_request(self._setup_user)
	
	def _setup_user(self, **kw):
		## TODO convert to Flask.login
		if current_app.config.TESTING:
			request.user = current_app.site.owner
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
			request.user = User.q.get_by(name="",site=current_app.site)
	
	def create_jinja_environment(self):
		"""Add support for .haml templates."""
		rv = super(BaseApp,self).create_jinja_environment()
 
		rv.extensions["jinja2.ext.HamlishExtension"] = HamlishExtension(rv)
		rv.hamlish_file_extensions=('.haml',)
		rv.hamlish_mode='debug'
		rv.hamlish_enable_div_shortcut=True

		rv.filters['datetime'] = datetimeformat

		rv.globals['site'] = self.site

		## setup template loader
		rv.loader = SiteTemplateLoader(self.site)
		## TODO: do the same thing with static files

		from pybble.render import add_to_jinja
		add_to_jinja(rv)
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
	if verbose:
		logging.basicConfig(stream=sys.stderr,level=logging.DEBUG)

	if cfg_app is None:
		cfg_app = _fake_app(os.path.abspath(os.curdir))
		if config:
			os.environ['PYBBLE'] = config
		from pybble.core import config as cfg
		cfg_app.config = cfg

		assert testing == cfg.get('TESTING',False), (testing,cfg.get('TESTING',False))
	
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
					if site != ROOT_SITE_NAME:
						raise RuntimeError("The site '%s' does not exist yet."%(site,))
					logger.warn("Creating a new root site")
					site = create_site(None,"localhost","_root",ROOT_SITE_NAME)

		if site is None or site.app is None:
			app = cfg_app
		else:
			app = site.app.mod(site, testing=testing)

		if verbose:
			logging.basicConfig(
				level=getattr(logging, app.config['LOGGER_LEVEL']),
				format=app.config['LOGGER_FORMAT'],
				datefmt=app.config['LOGGER_DATE_FORMAT']
			)

	register(app)
	return app

def create_site(parent,domain,app,name):
	app = App.q.get_by(name=app)
	site = Site(parent=parent, name=name, domain=domain, app=app)
	db.flush()
	return site

def drop_site(site=None):
	if site is None:
		site = current_app.site
	elif isinstance(site,string_types):
		try:
			site = Site.q.get_by(name=text_type(site),parent=current_app.site)
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

