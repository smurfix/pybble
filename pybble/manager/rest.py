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

from . import Manager,Command,Option
from ..core.rest import RESTend
from ..core.db import db
from ..core.models import Discriminator
from ..blueprint import create_blueprint,drop_blueprint,list_blueprints
from ..core.json import encode,decode
from ..utils.show import show

def _parse(args):
	"""
	Translate a list of foo=bar strings to a dict.

	Special cases:
		* foo=- ⇒ None
		* foo=123 ⇒ converted to integer
		* foo==Bar:123 ⇒ reference to this database entry
	"""
	data = {}
	for k in args:
		k,v = args.split('=',1)
		if v == "":
			pass
		elif v == "-":
			v = None
		elif v.startswith("="):
			descr,oid = v.split(":")
			v = Discriminator.get(descr).map.q.get_by(id=int(oid))
		else:
			try:
				v = int(v)
			except ValueError:
				pass
		data[k] = v
	return data

class CmdGET(Command):
	"""Retrieve a record (or a list of them (or a list of record types))"""
	def __init__(self):
		super(CmdGET,self).__init__()
		self.add_option(Option("typ", nargs='?', action="store",help="The item's type; if missing: list types"))
		self.add_option(Option("id", type=int, nargs='?', action="store",help="The item's ID; if missing: list entries of that type"))
	def __call__(self,app, help=False, id=None,typ=None):
		if help:
			self.parser.print_help()
			sys.exit(not help)
		if typ is None:
			show(RESTend().types(), expand=None)
			return
		if id is None:
			show(RESTend().list(typ), expand=".")
			return
		res = RESTend().get(int(id),typ)
		show(res)
		db.commit()
		
class CmdDELETE(Command):
	"""Delete a record"""
	def __init__(self):
		super(CmdDELETE,self).__init__()
		self.add_option(Option("typ", nargs='?', action="store",help="The item's type; if missing: list types"))
		self.add_option(Option("id", type=int, nargs='?', action="store",help="The item's ID; if missing: list entries of that type"))
	def __call__(self,app, help=False, id=None,typ=None):
		if help or not id:
			self.parser.print_help()
			sys.exit(not help)
		res = RESTend().delete(int(id),typ)
		show(res)
		db.commit()
		
class CmdPOST(Command):
	"""Add a record"""
	capture_all_args = True
	def __init__(self):
		super(CmdPOST,self).__init__()
		self.add_option(Option("typ", nargs='?', action="store",help="The item's type"))
	def __call__(self,app, args, typ=None,help=False):
		if help or not args:
			self.parser.print_help()
			sys.exit(not help)
		data = _parse(args)
		res = RESTend().post(descr=typ, **data)
		show(res)
		
class CmdPUT(Command):
	"""Change a record (clear not-mentioned data)"""
	capture_all_args = True
	def __init__(self):
		super(CmdPUT,self).__init__()
		self.add_option(Option("typ", nargs='?', action="store",help="The item's type"))
		self.add_option(Option("id", type=int, nargs='?', action="store",help="The item's ID"))
	def __call__(self,app, args, typ=None,id=None,help=False):
		if help or not args or not id:
			self.parser.print_help()
			sys.exit(not help)
		data = _parse(args)
		res = RESTend().put(id=id, descr=typ, **data)
		show(res)
		
class CmdPATCH(Command):
	"""Change a record (don't touch not-mentioned data)"""
	capture_all_args = True
	def __init__(self):
		super(CmdPATCH,self).__init__()
		self.add_option(Option("typ", nargs='?', action="store",help="The item's type"))
		self.add_option(Option("id", nargs='?', action="store",help="The item's ID"))
	def __call__(self,app, args, typ=None,id=None,help=False):
		if help or not args or not id:
			self.parser.print_help()
			sys.exit(not help)
		data = _parse(args)
		res = RESTend().patch(descr=typ, **data)
		show(res)
		
class DocREST(Command):
	def __init__(self):
		super(DocREST,self).__init__()
		#self.add_option(Option("-?","--help", dest="help",action="store_true",help="Display this help text and exit"))
		self.add_option(Option("typ", nargs='?', action="store",help="The REST type to document"))
		self.add_option(Option("doc", nargs='?', action="store",help="some text"))
	def __call__(self,app, help=False,typ=None,doc=None):
		if help or typ is None:
			if help:
				self.parser.print_help()
			sys.exit(not help)
		typ,subtyp = msplit(typ)
		mtype = RESTtype.q.get_by(typ=typ,subtyp=subtyp)
		if doc is None:
			if mtype.doc is not None:
				print(mtype.doc)
		else:
			if doc == "-":
				doc = None
			mtype.doc = doc
			db.commit()
		
class DropREST(Command):
	def __init__(self):
		super(DropREST,self).__init__()
		#self.add_option(Option("-?","--help", dest="help",action="store_true",help="Display this help text and exit"))
		self.add_option(Option("typ", nargs='?', action="store",help="The REST type to delete"))
	def __call__(self,app, help=False,typ=None):
		if help or typ is None:
			self.parser.print_help()
			sys.exit(not help)
		typ,subtyp = msplit(typ)
		mtype = RESTtype.q.get_by(typ=typ,subtyp=subtyp)
		db.delete(mtype)
		db.commit()
		
class CmdDIR(Command):
	"""List all items of a type"""
	def __call__(self,app, help=False):
		if help:
			self.parser.print_help()
			sys.exit(not help)
		res = []
		for mtype in RESTtype.q.all():
			print("{}/{}\t{}\t{}".format(mtype.typ,mtype.subtyp,mtype.ext if mtype.ext is not None else "-", mtype.name))
		
class RESTManager(Manager):
	"""Directly manipulate the database"""
	json = None ## TODO
	def __init__(self):
		super(RESTManager,self).__init__()
		self.add_option("-j", "--json", dest="json", required=False, help="Accept/send JSON")

		self.add_command("get", CmdGET())
		self.add_command("put", CmdPUT())
		self.add_command("post", CmdPOST())
		self.add_command("patch", CmdPATCH())
		self.add_command("delete", CmdDELETE())
		self.add_command("list", CmdDIR())

	def __call__(self, app, json=False):
		self.json = json
		return app
	
