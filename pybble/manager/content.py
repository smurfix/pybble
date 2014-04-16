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
from ..core.models import Object

class AddContent(Command):
	"""Add a content type"""
	def __init__(self):
		super(AddContent,self).__init__()
		#self.add_option(Option("-?","--help", dest="help",action="store_true",help="Display this help text and exit"))
		self.add_option(Option("name", nargs='?', action="store",help="The content type's name"))
		self.add_option(Option("data", nargs='*', action="append",help="name=value pairs for insertion"))
	def __call__(self,app, help=False,name=None,data=None):
		if help or type is None:
			self.parser.print_help()
			print("Available content handlers: "+" ".join(list_Contents()),file=sys.stderr)
			sys.exit(not help)
		create_Content(type=type, name=name, doc=doc)
		
class DropContent(Command):
	"""Remove a content type"""
	def __init__(self):
		super(DropContent,self).__init__()
		#self.add_option(Option("-?","--help", dest="help",action="store_true",help="Display this help text and exit"))
		self.add_option(Option("id", nargs='?', action="store",help="The content ID to mark-as-deleted"))
	def __call__(self,app, help=False,name=None):
		if help or name is None:
			self.parser.print_help()
			sys.exit(not help)
		drop_Content(name)
		
class ListContent(Command):
	"""List known content types"""
	def __init__(self):
		super(ListContent,self).__init__()
		#self.add_option(Option("-?","--help", dest="help",action="store_true",help="Display this help text and exit"))
		self.add_option(Option("name", nargs='?', action="store",help="The content type's name"))
	def __call__(self,app, help=False,name=None):
		if help:
			self.parser.print_help()
			sys.exit(not help)
		if name is not None:
			## grab database fields from named object class
			## list them
			import pdb;pdb.set_trace()
			return
		## grab non-abstract polymorphics from Object
		## list them
		import pdb;pdb.set_trace()
		super(ListContent,self).__init__()
		for ct in Content.objects(**filter):
			print(ct.type,ct.name,ct.doc)
		
class ContentManager(Manager):
	"""Content types Pybble knows about"""
	def __init__(self):
		super(ContentManager,self).__init__()
		self.add_command("add", AddContent())
		self.add_command("delete", DropContent())
		self.add_command("list", ListContent())

	def create_app(self, app):
		return app
	
