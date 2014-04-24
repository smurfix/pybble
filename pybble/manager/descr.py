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
from importlib import import_module
from sqlalchemy.orm.exc import NoResultFound

from . import Manager,Command,Option
from ..core.models import Discriminator as Dis
from ..core.db import db

class AddDis(Command):
	def __init__(self):
		super(AddDis,self).__init__()
		#self.add_option(Option("-?","--help", dest="help",action="store_true",help="Display this help text and exit"))
		self.add_option(Option("name", nargs='?', action="store",help="The discriminator's"))
		self.add_option(Option("path", nargs='?', action="store",help="The class path"))
	def __call__(self,app, help=False,name=None,typ=None,ext=None):
		if help or typ is None:
			self.parser.print_help()
			sys.exit(not help)
		d = Dis(name=typ,display_name=name)
		db.add(d)
		db.commit()
		
class DocDis(Command):
	def __init__(self):
		super(DocDis,self).__init__()
		#self.add_option(Option("-?","--help", dest="help",action="store_true",help="Display this help text and exit"))
		self.add_option(Option("typ", nargs='?', action="store",help="The discriminator to document"))
		self.add_option(Option("doc", nargs='?', action="store",help="some text"))
	def __call__(self,app, help=False,typ=None,doc=None):
		if help or typ is None:
			if help:
				self.parser.print_help()
			sys.exit(not help)
		d = Dis.q.get_by(name=typ)
		if doc is None:
			if d.infotext is not None:
				print(d.infotext)
		else:
			if doc == "-":
				doc = None
			d.infotext = doc
			db.commit()
		
class DropDis(Command):
	def __init__(self):
		super(DropDis,self).__init__()
		#self.add_option(Option("-?","--help", dest="help",action="store_true",help="Display this help text and exit"))
		self.add_option(Option("typ", nargs='?', action="store",help="The Discriminator to delete"))
	def __call__(self,app, help=False,typ=None):
		if help or typ is None:
			self.parser.print_help()
			sys.exit(not help)
		d = Dis.q.get_by(name=typ)
		db.delete(d)
		db.commit()
		
class ListDis(Command):
	def __call__(self,app, help=False):
		if help:
			self.parser.print_help()
			sys.exit(not help)
		for d in Dis.q.all():
			print("{}\t{}\t{}".format(d.id,d.name,d.display_name))
		
class DisManager(Manager):
	"""URLs and their content"""
	def __init__(self):
		super(DisManager,self).__init__()
		self.add_command("add", AddDis())
		self.add_command("delete", DropDis())
		self.add_command("list", ListDis())
		self.add_command("doc", DocDis())

	def create_app(self, app):
		return app
	
