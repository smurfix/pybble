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
from importlib import import_module

from flask import Flask, render_template
from flask import Blueprint as FlaskBlueprint
from flask.config import Config
from flask.ext.script import Server

from mongoengine.errors import DoesNotExist

from .. import ROOT_NAME
from ..core.db import db
from ..core.models import Site,Blueprint
from ..manager import Manager,Command

logger = logging.getLogger('pybble.blueprint')

class BaseBlueprint(FlaskBlueprint):
	params = None
	def register(self, app, options, first_registration=False):
		self.add_routes()
		@self.record
		def get_params(state):
			self.params = state.options
		super(BaseBlueprint,self).register(app, options, first_registration=False)
		# TODO: templates
	
	def add_routes(self):
		pass

def load_blueprints(app):
	site = app.site
	names = set() 
	while site is not None:
		for bp in site.blueprints:
			if bp.name in names:
				continue
			names.add(bp.name)
			bp_mod = "pybble.blueprint."+bp.blueprint
			bp_module = import_module(bp_mod)
			b = bp_module.Blueprint(bp.name, bp_mod, template_folder= os.path.join(os.path.dirname(os.path.abspath(__file__)),bp.blueprint,'templates'))
			if not bp.path.startswith('/'):
				bp.path = '/_broken/'+bp.path
			app.register_blueprint(b, url_prefix=bp.path, **bp.params._data)
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
	bp = Blueprint(parent=site, name=name, path=path, blueprint=blueprint)
	bp.save()
	return bp

def drop_blueprint(site,name):
	bp = Blueprint.objects.get(parent=site, name=name)
	bp.delete()

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

