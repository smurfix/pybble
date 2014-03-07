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
from mongoengine.errors import DoesNotExist

from . import Manager,Command,Option
from ..core.models import Blueprint
from ..blueprint import create_blueprint,drop_blueprint,list_blueprints

class AddBlueprint(Command):
	def __init__(self):
		super(AddBlueprint,self).__init__()
		#self.add_option(Option("-?","--help", dest="help",action="store_true",help="Display this help text and exit"))
		self.add_option(Option("name", nargs='?', action="store",help="The blueprint's internal name"))
		self.add_option(Option("bp", nargs='?', action="store",help="The Pybble blueprint to install"))
		self.add_option(Option("path", nargs='?', action="store",help="The path prefix to attach it to"))
	def __call__(self,app, help=False,bp=None,path=None,name=None):
		if help or path is None:
			self.parser.print_help()
			print("Available blueprints: "+" ".join(list_blueprints()),file=sys.stderr)
			sys.exit(not help)
		if not path.startswith('/'):
			print("This does not work -- paths must start with a slash.", file=sys.stderr)
			sys.exit(1)
		create_blueprint(site=app.site, path=path, blueprint=bp, name=name)
		
class ParamBlueprint(Command):
	def __init__(self):
		super(ParamBlueprint,self).__init__()
		#self.add_option(Option("-?","--help", dest="help",action="store_true",help="Display this help text and exit"))
		self.add_option(Option("name", nargs='?', action="store",help="The blueprint's internal name"))
		self.add_option(Option("key", nargs='?', action="store",help="The parameter name"))
		self.add_option(Option("value", nargs='?', action="store",help="The value"))
	def __call__(self,app, help=False,name=None,key=None,value=None):
		if help or name is None:
			self.parser.print_help()
			sys.exit(not help)
		try:
			bp = Blueprint.objects.get(name=name, site=app.site)
		except DoesNotExist:
			raise DoesNotExist("Blueprint site=%s name=%s" % (app.site.name,name))
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
	def __call__(self,app, help=False,name=None):
		if help or name is None:
			self.parser.print_help()
			sys.exit(not help)
		drop_blueprint(app.site,name)
		
class ListBlueprint(Command):
	def __call__(self,app, help=False):
		if help:
			self.parser.print_help()
			sys.exit(not help)
		for bp in app.site.blueprints:
			print(bp.name,bp.blueprint,bp.path)
		
class BlueprintManager(Manager):
	def __init__(self):
		super(BlueprintManager,self).__init__()
		self.add_command("add", AddBlueprint())
		self.add_command("delete", DropBlueprint())
		self.add_command("list", ListBlueprint())
		self.add_command("param", ParamBlueprint())

	def create_app(self, app):
		return app
	
