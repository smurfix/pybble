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

"""\
This is the basic support module for blueprints.
"""

import os
import sys
import logging
from time import time
from importlib import import_module

from flask import Flask, request
from flask.blueprints import BlueprintSetupState, Blueprint as FlaskBlueprint
from flask.config import Config
from flask.ext.script import Server
from flask._compat import string_types,text_type

from ..core.db import db
from ..core.models.site import Site,Blueprint,SiteBlueprint
from ..core.models.tracking import Delete
from ..globals import current_site
from ..manager import Manager,Command

logger = logging.getLogger('pybble.blueprint')

class SetupState(BlueprintSetupState):
	def add_url_rule(self, rule, endpoint=None, view_func=None, **options):
		"""A helper method to register a rule (and optionally a view function)
		to the application.  The endpoint is automatically prefixed with the
		blueprint's endpoint if set.
		"""
		if self.url_prefix:
			rule = self.url_prefix + rule
		options.setdefault('subdomain', self.subdomain)
		if endpoint is None:
			endpoint = _endpoint_from_view_func(view_func)
		defaults = self.url_defaults
		if 'defaults' in options:
			defaults = dict(defaults, **options.pop('defaults'))
		if self.blueprint.endpoint:
			endpoint = self.blueprint.endpoint+'.'+endpoint
		self.app.add_url_rule(rule, endpoint, view_func, defaults=defaults, **options)

class BaseBlueprint(FlaskBlueprint):
	TEMPLATE=("templates",)

	params = None
	def __init__(self, bp, path, **kw):
		self.bp = bp
		self.name = bp.name
		self.endpoint = bp.endpoint
		super(BaseBlueprint,self).__init__(bp.name,bp.path, **kw)

	def register(self, app, options, first_registration=False):
		self.app = app
		@self.record
		def get_params(state):
			self.params = state.options
			self.setup()
		super(BaseBlueprint,self).register(app, options, first_registration=first_registration)
		# TODO: templates
	
	def setup(self):
		"""Called after data are loaded. Set up routing, attach modules, etc., here."""
		@self.url_defaults
		def bp_url_defaults(endpoint, values):
			config = getattr(request, 'bp', None)
			if config is not None:
				values.setdefault('bp', config)
		bp_url_defaults._no_urlfor = True

	def add_url_rule(self, rule, endpoint=None, view_func=None, **options):
		"""Like :meth:`Flask.add_url_rule` but for a blueprint.  The endpoint for
		the :func:`url_for` function is prefixed with the name of the blueprint.

		This is a copy from flask.blueprint, except that the dot rule has been removed.
		"""
		#if endpoint:
		#	assert '.' not in endpoint, "Blueprint endpoints should not contain dots"
		self.record(lambda s:
			s.add_url_rule(rule, endpoint, view_func, **options))
	
	def make_setup_state(self, app, options, first_registration=False):
		"""Creates an instance of :meth:`~flask.blueprints.BlueprintSetupState`
		object that is later passed to the register callback functions.
		Subclasses can override this to return a subclass of the setup state.
		"""
		return SetupState(self, app, options, first_registration)

def load_app_blueprints(app):
	site = app.site
	names = set() 
	seen_current_site = False
	while site is not None:
		for bp in site.blueprints:
			b = bp.blueprint
			if bp.name in names:
				continue
			names.add(bp.name)
			params = bp.config
			path = bp.path
			if path == "/": path = ""
			bpm = b.mod(bp, b.path, url_prefix=path)
			app.register_blueprint(bpm, url_defaults = { 'bp': bp })
		if current_site == site:
			seen_current_site = True
		if seen_current_site and not site.inherit_parent:
			break
		site = site.parent

def create_blueprint(site, blueprint, path, name=None,endpoint=None):
	"""\
		Attach a blueprint to a site.

		:param site: The site to attach to.
		:param blueprint: The name of the blueprint in the `pybble.blueprint`
		            directory.
		:param path: The web path to attach the blueprint to.
		:param name: A human-readable name for this attachment.
		"""

	if isinstance(blueprint,string_types):
		blueprint = Blueprint.q.get_by(name=text_type(blueprint))
	
	if name is None:
		name = getattr(blueprint.mod,"_name",blueprint.name)
	bp = SiteBlueprint.new(site=site, path=path, blueprint=blueprint, name=name,endpoint=endpoint)
	db.session.flush()
	return bp

def drop_blueprint(blueprint,site=None):
	if site is None:
		site = current_site

	if isinstance(blueprint,string_types):
		blueprint = Blueprint.q.get_by(name=text_type(blueprint))
	
	bp = SiteBlueprint.q.get_by(site=site, name=text_type(name))
	Delete.new(bp)

def list_blueprints():
	path = os.path.dirname(os.path.abspath(__file__))
	dir_list = os.listdir(path)
	for fname in dir_list:
		if os.path.exists(os.path.join(path, fname, '__init__.py')) and \
				not os.path.exists(os.path.join(path, fname, 'DISABLED')):
			yield fname

