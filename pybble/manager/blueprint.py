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
from importlib import import_module

from flask import current_app

from . import Manager,Option
from . import PrepCommand as Command
from ..core.models.site import Blueprint
from ..core.db import NoData
from ..blueprint import create_blueprint,drop_blueprint,list_blueprints

class AddBlueprint(Command):
	"""Attach a blueprint to a site."""
	def __init__(self):
		super(AddBlueprint,self).__init__()
		#self.add_option(Option("-?","--help", dest="help",action="store_true",help="Display this help text and exit"))
		self.add_option(Option("bp", nargs='?', action="store",help="The Pybble blueprint to install"))
		self.add_option(Option("path", nargs='?', action="store",help="The URL prefix to attach it to"))
		self.add_option(Option("name", nargs='?', action="store",help="The blueprint's name, for templates et al."))
	def run(self, help=False,bp=None,name=None,path=None):
		if help or path is None:
			self.parser.print_help()
			print("Available blueprints: "+" ".join(list_blueprints()),file=sys.stderr)
			sys.exit(not help)
		if path == "/":
			path = None
		elif not path.startswith('/'):
			print("This does not work -- paths must start with a slash.", file=sys.stderr)
			sys.exit(1)
		bp = Blueprint.q.get_by(name=name)
		if name is None:
			name = bp.name
		create_blueprint(site=current_app.site, path=path, blueprint=bp, name=name)
		
class ParamBlueprint(Command):
	"""Set a blueprint's parameter"""
	def __init__(self):
		super(ParamBlueprint,self).__init__()
		#self.add_option(Option("-?","--help", dest="help",action="store_true",help="Display this help text and exit"))
		self.add_option(Option("name", nargs='?', action="store",help="The attached blueprint's name"))
		self.add_option(Option("key", nargs='?', action="store",help="The parameter name"))
		self.add_option(Option("value", nargs='?', action="store",help="The value"))
	def run(self, help=False,name=None,key=None,value=None):
		if help or name is None:
			self.parser.print_help()
			sys.exit(not help)
		try:
			bp = SiteBlueprint.objects.get(name=name, site=current_app.site)
		except NoData:
			raise NoData("Blueprint site=%s name=%s" % (current_app.site.name,name))
		if key is None:
			for k,v in bp.params._data.items():
				print(k,v)
			return
		if value is None:
			print(getattr(bp.params,key))
			return
		if value == "-":
			delattr(bp.params,key)
		else:
			try:
				value = eval(value)
			except (SyntaxError,NameError):
				pass
			setattr(bp.params,key,value)
		bp.save()
		
class DropBlueprint(Command):
	def __init__(self):
		super(DropBlueprint,self).__init__()
		#self.add_option(Option("-?","--help", dest="help",action="store_true",help="Display this help text and exit"))
		self.add_option(Option("name", nargs='?', action="store",help="The blueprint's internal name"))
	def run(self, help=False,name=None):
		if help or name is None:
			self.parser.print_help()
			sys.exit(not help)
		drop_blueprint(name)
		
class ListBlueprint(Command):
	def run(self, help=False):
		if help:
			self.parser.print_help()
			sys.exit(not help)
		for bp in current_app.site.blueprints:
			print(bp.name,bp.blueprint,bp.path)
		
class BlueprintManager(Manager):
	"""URLs and their content"""
	def __init__(self):
		super(BlueprintManager,self).__init__()
		self.add_command("add", AddBlueprint())
		self.add_command("delete", DropBlueprint())
		self.add_command("list", ListBlueprint())
		self.add_command("param", ParamBlueprint())

