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

from ..core.db import db
from ..core.models import Object, Discriminator
from ..core.json import encode,decode
from . import Manager,Command,Option
from .descr import ListDis

class AddObject(Command):
	"""Add an object type"""
	def __init__(self):
		super(AddObject,self).__init__()
		#self.add_option(Option("-?","--help", dest="help",action="store_true",help="Display this help text and exit"))
		self.add_option(Option("name", nargs='?', action="store",help="The Object type's name"))
		self.add_option(Option("data", nargs='*', action="append",help="name=value pairs for insertion"))
	def __call__(self,app, help=False,name=None,data=None):
		if help or type is None:
			self.parser.print_help()
			print("Available Object handlers: "+" ".join(list_Objects()),file=sys.stderr)
			sys.exit(not help)
		create_Object(type=type, name=name, doc=doc)
		
class DropObject(Command):
	"""Remove an Object type"""
	def __init__(self):
		super(DropObject,self).__init__()
		#self.add_option(Option("-?","--help", dest="help",action="store_true",help="Display this help text and exit"))
		self.add_option(Option("id", nargs='?', action="store",help="The Object ID to mark-as-deleted"))
	def __call__(self,app, help=False,name=None):
		if help or name is None:
			self.parser.print_help()
			sys.exit(not help)
		drop_Object(name)
		
class ListObject(Command):
	"""List an object, or known objects of a type"""
	def __init__(self):
		super(ListObject,self).__init__()
		#self.add_option(Option("-?","--help", dest="help",action="store_true",help="Display this help text and exit"))
		self.add_option(Option("-d","--dump", dest="dump",action="store_true",help="Dump a complete object"))
		self.add_option(Option("typ", nargs='?', action="store",help="The object type"))
		self.add_option(Option("oid", nargs='?', action="store",help="The Object ID"))
		self.add_option(Option("var", nargs='?', action="store",help="The Object's variable"))
	def __call__(self,app, help=False,typ=None,oid=None,var=None, dump=False):
		if help:
			self.parser.print_help()
			sys.exit(not help)
		if typ is None:
			ListDis()(app,dump)
			return
		typ = Discriminator.get(typ).mod
		if oid is None:
			## list them all
			for obj in typ.q.all():
				if dump:
					print(encode(obj._dump()))
				else:
					print(str(obj))
			return
		obj = typ.q.get_by(id=oid)
		if var is not None:
			obj = getatr(obj,var)
		if dump:
			print(encode(obj._dump()))
		else:
			print(str(obj))
		
class ObjectManager(Manager):
	"""Object types Pybble knows about"""
	def __init__(self):
		super(ObjectManager,self).__init__()
		self.add_command("add", AddObject())
		self.add_command("delete", DropObject())
		self.add_command("list", ListObject())

	def create_app(self, app):
		return app
	
