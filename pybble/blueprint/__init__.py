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

from flask import Flask, render_template, request
from flask import Blueprint as FlaskBlueprint
from flask.config import Config
from flask.ext.script import Server
from flask._compat import string_types,text_type

from ..core.db import db
from ..core.models.site import Site,Blueprint,SiteBlueprint
from ..core.models.tracking import Delete
from ..manager import Manager,Command

logger = logging.getLogger('pybble.blueprint')

class BaseBlueprint(FlaskBlueprint):
	params = None
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
		@self.url_value_preprocessor
		def bp_url_value_preprocessor(endpoint, values):
			request.bp = values.pop('bp')
		@self.url_defaults
		def bp_url_defaults(endpoint, values):
			config = getattr(request, 'bp', None)
			if config is not None:
				values.setdefault('bp', config)

def load_app_blueprints(app):
	site = app.site
	names = set() 
	while site is not None:
		for bp in site.blueprints:
			b = bp.blueprint
			if bp.name in names:
				continue
			names.add(bp.name)
			params = bp.config
			path = bp.path
			if path == "/": path = ""
			bpm = b.mod(bp.name, b.path, url_prefix=path)
			app.register_blueprint(bpm, url_defaults = { "bp": bp })
		site = site.parent

def create_blueprint(site, blueprint, path, name=None):
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
		name = blueprint.name
	bp = SiteBlueprint(site=site, path=path, blueprint=blueprint, name=name)
	db.flush()
	return bp

def drop_blueprint(blueprint,site=None):
	if site is None:
		site = current_app.site

	if isinstance(blueprint,string_types):
		blueprint = Blueprint.q.get_by(name=text_type(blueprint))
	
	bp = SiteBlueprint.q.get_by(site=site, name=text_type(name))
	Delete(bp)

def list_blueprints():
	path = os.path.dirname(os.path.abspath(__file__))
	dir_list = os.listdir(path)
	for fname in dir_list:
		if os.path.exists(os.path.join(path, fname, '__init__.py')) and \
				not os.path.exists(os.path.join(path, fname, 'DISABLED')):
			yield fname

