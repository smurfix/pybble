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

from . import Manager,Command,Option,PrepCommand
from ..core.rest import RESTend
from ..core.db import db, NoData
from ..core.models import Discriminator
from ..blueprint import create_blueprint,drop_blueprint,list_blueprints
from ..core.json import encode,decode
from ..utils import getsubattr
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
		k,v = k.split('=',1)
		if v == "":
			pass
		elif v == "-":
			v = None
		elif v.startswith("="):
			descr,oid = v[1:].split(":")
			try:
				v = Discriminator.get(descr)
			except NoData:
				raise RuntimeError("I do not know the type ‘{}’".format(descr))
			try:
				v = v.mod.q.get_by(id=int(oid))
			except NoData:
				raise RuntimeError("I do not know the item ‘{}:{}’".format(descr,oid))

		else:
			try:
				v = int(v)
			except ValueError:
				pass
		data[k] = v
	return data

class CmdGET(PrepCommand):
	"""Retrieve part of of a record (or a (or a list of them (or a list of record types)))"""
	## TODO: allow expansion for JSON
	capture_all_args = True

	def __init__(self):
		super(CmdGET,self).__init__()
		self.add_option(Option("-x","--expand",action="append", dest="exp", help="additional detail to print"))
		self.add_option(Option("typ", nargs='?', action="store",help="The item's type; if missing: list types"))
		self.add_option(Option("id", type=int, nargs='?', action="store",help="The item's ID; if missing: list entries of that type"))
	def run(self,args, help=False, id=None,typ=None, exp=None):
		json = current_app.json
		if help or exp and json:
			self.parser.print_help()
			sys.exit(not help)
		if exp:
			exp = ",".join(exp)

		if typ is None:
			data = RESTend(json).types()
			if exp is not None:
				data = [data]
		elif id is None:
			data = RESTend(json).list(typ)
			if exp is not None:
				data = [data]
		elif not args:
			data = RESTend(json).get(int(id),typ)
			if not exp: exp = "-"
			data = [data]
		else:
			data = RESTend(json).get(int(id),typ)
			data = [getsubattr(data,a) for a in args]
			if exp is None and len(args) == 1:
				exp = "-"
			
		for d in data:
			if json:
				print(encode(d))
			else:
				show(d, expand=exp)
		db.commit()
		
class CmdDIR(PrepCommand):
	"""Retrieve a list of records (or a list of record types)"""
	## TODO: allow expansion for JSON
	capture_all_args = True

	def __init__(self):
		super(CmdDIR,self).__init__()
		self.add_option(Option("typ", nargs='?', action="store",help="The item's type; if missing: list types"))
	def run(self, args, help=False, typ=None, exp=None):
		json = current_app.json
		if help:
			self.parser.print_help()
			sys.exit(not help)

		if typ is None:
			data = RESTend(json).types()
		else:
			data = RESTend(json).list(typ)

		for d in data:
			if json:
				print(encode(d))
			else:
				show(d)
		db.commit()
		
class CmdDELETE(PrepCommand):
	"""Delete a record"""
	def __init__(self):
		super(CmdDELETE,self).__init__()
		self.add_option(Option("typ", nargs='?', action="store",help="The item's type; if missing: list types"))
		self.add_option(Option("id", type=int, nargs='?', action="store",help="The item's ID; if missing: list entries of that type"))
	def run(self, help=False, id=None,typ=None):
		if help or not id:
			self.parser.print_help()
			sys.exit(not help)
		res = RESTend().delete(int(id),typ)
		show(res)
		db.commit()
		
class CmdPOST(PrepCommand):
	"""Add a record"""
	capture_all_args = True
	def __init__(self):
		super(CmdPOST,self).__init__()
		self.add_option(Option("typ", nargs='?', action="store",help="The item's type"))
	def run(self, args, typ=None,help=False):
		if help or not args:
			self.parser.print_help()
			sys.exit(not help)
		data = _parse(args)
		res = RESTend().post(descr=typ, **data)
		show(res)
		
class CmdPUT(PrepCommand):
	"""Change a record (clear not-mentioned data)"""
	capture_all_args = True
	def __init__(self):
		super(CmdPUT,self).__init__()
		self.add_option(Option("typ", nargs='?', action="store",help="The item's type"))
		self.add_option(Option("id", type=int, nargs='?', action="store",help="The item's ID"))
	def run(self, args, typ=None,id=None,help=False):
		if help or not args or not id:
			self.parser.print_help()
			sys.exit(not help)
		data = _parse(args)
		res = RESTend().put(id=id, descr=typ, **data)
		show(res)
		
class CmdPATCH(PrepCommand):
	"""Change a record (don't touch not-mentioned data)"""
	capture_all_args = True
	def __init__(self):
		super(CmdPATCH,self).__init__()
		self.add_option(Option("typ", nargs='?', action="store",help="The item's type"))
		self.add_option(Option("id", nargs='?', action="store",help="The item's ID"))
	def run(self, args, typ=None,id=None,help=False):
		if help or not args or not id:
			self.parser.print_help()
			sys.exit(not help)
		data = _parse(args)
		res = RESTend().patch(descr=typ, **data)
		show(res)
		
class RESTManager(Manager):
	"""Directly manipulate the database"""
	json = None ## TODO
	def __init__(self):
		super(RESTManager,self).__init__()
		self.add_option("-j", "--json", dest="json", action="store_true", required=False, help="Accept/send JSON")

		self.add_command("get", CmdGET())
		self.add_command("replace", CmdPUT())
		self.add_command("add", CmdPOST())
		self.add_command("update", CmdPATCH())
		self.add_command("delete", CmdDELETE())
		self.add_command("list", CmdDIR())

	def __call__(self, app, json=False):
		app.json = json
		return app
	
