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
from ..core.models.types import MIMEtype,add_mime
from ..core.db import db

def msplit(typ):
	try:
		typ,subtyp = typ.split('/')
	except ValueError:
		raise RuntimeError("MIME type/subtype, like ‘text/plain’ or ‘image/jpeg’")
	return typ,subtyp

class AddMIME(Command):
	def __init__(self):
		super(AddMIME,self).__init__()
		#self.add_option(Option("-?","--help", dest="help",action="store_true",help="Display this help text and exit"))
		self.add_option(Option("name", nargs='?', action="store",help="A human-readable name"))
		self.add_option(Option("typ", nargs='?', action="store",help="The MIME type/subtype"))
		self.add_option(Option("ext", nargs='?', action="store",help="Its default filename extension (‘-’ to disable)"))
	def __call__(self,app, help=False,name=None,typ=None,ext=None):
		if help or typ is None:
			self.parser.print_help()
			sys.exit(not help)
		typ,subtyp = msplit(typ)
		add_mime(name=name,typ=typ, subtyp=subtyp, ext=ext)
		db.commit()
		
class DocMIME(Command):
	def __init__(self):
		super(DocMIME,self).__init__()
		#self.add_option(Option("-?","--help", dest="help",action="store_true",help="Display this help text and exit"))
		self.add_option(Option("typ", nargs='?', action="store",help="The MIME type to document"))
		self.add_option(Option("doc", nargs='?', action="store",help="some text"))
	def __call__(self,app, help=False,typ=None,doc=None):
		if help or typ is None:
			if help:
				self.parser.print_help()
			sys.exit(not help)
		typ,subtyp = msplit(typ)
		mtype = MIMEtype.q.get_by(typ=typ,subtyp=subtyp)
		if doc is None:
			if mtype.doc is not None:
				print(mtype.doc)
		else:
			if doc == "-":
				doc = None
			mtype.doc = doc
			db.commit()
		
class DropMIME(Command):
	def __init__(self):
		super(DropMIME,self).__init__()
		#self.add_option(Option("-?","--help", dest="help",action="store_true",help="Display this help text and exit"))
		self.add_option(Option("typ", nargs='?', action="store",help="The MIME type to delete"))
	def __call__(self,app, help=False,typ=None):
		if help or typ is None:
			self.parser.print_help()
			sys.exit(not help)
		typ,subtyp = msplit(typ)
		mtype = MIMEtype.q.get_by(typ=typ,subtyp=subtyp)
		db.delete(mtype)
		db.commit()
		
class ListMIME(Command):
	def __call__(self,app, help=False):
		if help:
			self.parser.print_help()
			sys.exit(not help)
		for mtype in MIMEtype.q.all():
			print("{}/{}\t{}\t{}".format(mtype.typ,mtype.subtyp,mtype.ext if mtype.ext is not None else "-", mtype.name))
		
class MIMEManager(Manager):
	"""URLs and their content"""
	def __init__(self):
		super(MIMEManager,self).__init__()
		self.add_command("add", AddMIME())
		self.add_command("delete", DropMIME())
		self.add_command("list", ListMIME())
		self.add_command("doc", DocMIME())

	def create_app(self, app):
		return app
	
