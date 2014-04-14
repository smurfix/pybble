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
from ..core.models.doc import ContentType
from ..content import create_contenttype,drop_contenttype,list_contenttypes

class AddContentType(Command):
	"""Add a content type"""
	def __init__(self):
		super(AddContentType,self).__init__()
		#self.add_option(Option("-?","--help", dest="help",action="store_true",help="Display this help text and exit"))
		self.add_option(Option("name", nargs='?', action="store",help="The contenttype's name"))
		self.add_option(Option("type", nargs='?', action="store",help="The class that can render/edit this content"))
		self.add_option(Option("doc", nargs='?', action="store",help="Slightly more verbose documentation"))
	def __call__(self,app, help=False,name=None,type=None,doc=None):
		if app.site.parent is not None:
			print("Content types are global. You cannot add them to a specific site.", file=sys.stderr)
			sys.exit(1)
		if help or type is None:
			self.parser.print_help()
			print("Available content handlers: "+" ".join(list_contenttypes()),file=sys.stderr)
			sys.exit(not help)
		create_contenttype(type=type, name=name, doc=doc)
		
class DropContentType(Command):
	"""Remove a content type"""
	def __init__(self):
		super(DropContentType,self).__init__()
		#self.add_option(Option("-?","--help", dest="help",action="store_true",help="Display this help text and exit"))
		self.add_option(Option("name", nargs='?', action="store",help="The contenttype's name"))
	def __call__(self,app, help=False,name=None):
		if app.site.parent is not None:
			print("Content types are global. You cannot remove them from a specific site.", file=sys.stderr)
			sys.exit(1)
		if help or name is None:
			self.parser.print_help()
			sys.exit(not help)
		drop_contenttype(name)
		
class ListContentType(Command):
	"""List configured content types"""
	def __init__(self):
		super(ListContentType,self).__init__()
		#self.add_option(Option("-?","--help", dest="help",action="store_true",help="Display this help text and exit"))
		self.add_option(Option("name", nargs='?', action="store",help="The contenttype's name"))
	def __call__(self,app, help=False,name=None):
		if help:
			self.parser.print_help()
			sys.exit(not help)
		filter = {}
		if name is not None:
			filter['name'] = name
		for ct in ContentType.objects(**filter):
			print(ct.type,ct.name,ct.doc)
		
class ContentTypeManager(Manager):
	"""Content types Pybble knows about"""
	def __init__(self):
		super(ContentTypeManager,self).__init__()
		self.add_command("add", AddContentType())
		self.add_command("delete", DropContentType())
		self.add_command("list", ListContentType())

	def create_app(self, app):
		return app
	
