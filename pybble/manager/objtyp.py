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
from importlib import import_module

from . import Manager,Command,Option
from ..core.json import encode
from ..core.models.objtyp import ObjType as Typ
from ..core.db import db

class AddTyp(Command):
	def __init__(self):
		super(AddTyp,self).__init__()
		#self.add_option(Option("-?","--help", dest="help",action="store_true",help="Typplay this help text and exit"))
		self.add_option(Option("name", nargs='?', action="store",help="The objtyp's name"))
		self.add_option(Option("path", nargs='?', action="store",help="The class path"))
	def __call__(self,app, help=False,name=None,path=None):
		if help or path is None:
			self.parser.print_help()
			sys.exit(not help)
		d = Typ(path=path,name=name)
		db.add(d)
		db.session.commit()
		
class DocTyp(Command):
	def __init__(self):
		super(DocTyp,self).__init__()
		#self.add_option(Option("-?","--help", dest="help",action="store_true",help="Typplay this help text and exit"))
		self.add_option(Option("name", nargs='?', action="store",help="The objtyp to document"))
		self.add_option(Option("doc", nargs='?', action="store",help="some text"))
	def __call__(self,app, help=False,name=None,doc=None):
		if help or name is None:
			if help:
				self.parser.print_help()
			sys.exit(not help)
		d = Typ.q.get_by(name=name)
		if doc is None:
			if d.infotext is not None:
				print(d.infotext)
		else:
			if doc == "-":
				doc = None
			d.infotext = doc
			db.session.commit()
		
class DropTyp(Command):
	def __init__(self):
		super(DropTyp,self).__init__()
		#self.add_option(Option("-?","--help", dest="help",action="store_true",help="Typplay this help text and exit"))
		self.add_option(Option("name", nargs='?', action="store",help="The ObjType to delete"))
	def __call__(self,app, help=False,name=None):
		if help or name is None:
			self.parser.print_help()
			sys.exit(not help)
		d = Typ.q.get_by(name=name)
		db.session.delete(d)
		db.session.commit()
		
class ListTyp(Command):
	def __init__(self):
		super(ListTyp,self).__init__()
		#self.add_option(Option("-?","--help", dest="help",action="store_true",help="Typplay this help text and exit"))
		self.add_option(Option("-d","--dump", dest="dump",action="store_true",help="Dump a complete object"))
	def __call__(self,app, help=False, dump=False):
		if help:
			self.parser.print_help()
			sys.exit(not help)
		for d in Typ.q.all():
			if dump:
				print(encode(d._dump()))
			else:
				print("{}\t{}\t{}".format(d.id,d.name,d.path))
		
class TypManager(Manager):
	"""Types of databse entries"""
	def __init__(self):
		super(TypManager,self).__init__()
		self.add_command("add", AddTyp())
		self.add_command("delete", DropTyp())
		self.add_command("list", ListTyp())
		self.add_command("doc", DocTyp())

	def create_app(self, app):
		return app
	
