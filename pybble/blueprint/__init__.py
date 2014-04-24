# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, division, unicode_literals
##
## This is part of Pybble, a WMS (Whatever Management System) based on
## Jinja2/Haml, Werkzeug, Flask, and Optimism.
##
## Pybble is Copyright © 2009-2014 by Matthias Urlichs <matthias@urlichs.de>,
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
from importlib import import_module

from flask import Flask, render_template
from flask import Blueprint as FlaskBlueprint
from flask.config import Config
from flask.ext.script import Server

from ..core.db import db
from ..core.models.site import Site,Blueprint
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
		pass

def load_app_blueprints(app):
	site = app.site
	names = set() 
	while site is not None:
		for bp in site.blueprints:
			if bp.name in names:
				continue
			names.add(bp.name)
			params = bp.params
			bp = bp.mod()
			bp.setup_app(app)
			app.register_blueprint(bp, **params._data)
		site = site.parent

def create_blueprint(site, blueprint, path, name=None):
	"""\
		Attach a blueprint.

		:param site: The site to attach to.
		:param blueprint: The name of the blueprint in the `pybble.blueprint`
		            directory.
		:param path: The web path to attach the blueprint to.
		:param name: A human-readable name for this attachment.
		"""

	bp_module = import_module("pybble.blueprint."+blueprint)
	assert bp_module.Blueprint is not None, "App '%s' does not exist"%(app,)
	if name is None:
		name = blueprint
	bp = Blueprint(site=site, name=name, path=path, blueprint=blueprint)
	bp.save()
	return bp

def drop_blueprint(site,name):
	bp = Blueprint.objects.get(parent=site, name=name)
	bp.delete()

def list_blueprints():
	path = os.path.dirname(os.path.abspath(__file__))
	dir_list = os.listdir(path)
	for fname in dir_list:
		if os.path.exists(os.path.join(path, fname, '__init__.py')) and \
				not os.path.exists(os.path.join(path, fname, 'DISABLED')):
			yield fname

