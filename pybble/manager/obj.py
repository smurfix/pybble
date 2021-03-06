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

from flask import current_app

from . import Manager,Command,Option,PrepCommand
from ..core.rest import RESTend
from ..core.db import db, NoData,ManyData
from ..core.models.objtyp import ObjType
from ..core.models.types import MIMEtype
from ..core.models._const import PERM_NAME, TM_DETAIL
from ..core.json import encode
from ..utils import getsubattr
from ..utils.show import show,Cache

class NotGiven: pass

def _parse(args):
	"""
	Translate a list of foo=bar strings to a dict.

	Special cases:
		* foo=- ⇒ None
		* foo=123 ⇒ converted to integer
		* foo=True ⇒ converted to Boolean
		* foo==D:User ⇒ refer to the User table
		* foo==R:Read ⇒ refer to the "Read" access right
		* foo==T:Detail ⇒ refer to the "Detail" template type
		* foo==M:text/html ⇒ refer to this MIME type
		* foo==Bar:123 ⇒ reference to this database entry
	"""
	data = {}
	for k in args:
		k,v = k.split('=',1)
		if v == "":
			pass
		elif v in ("-","None"):
			v = None
		elif v == "True":
			v = True
		elif v == "False":
			v = False
		elif v.startswith("="):
			objtyp,oid = v[1:].split(":")
			if objtyp == "D":
				v = ObjType.get(oid)
			elif objtyp == "R":
				v = PERM_NAME[oid]
			elif objtyp == "T":
				v = TM_DETAIL[oid]
			elif objtyp == "M":
				v = MIMEtype.get(oid)
			else:
				try:
					v = ObjType.get(objtyp)
				except NoData:
					raise RuntimeError("I do not know the type ‘{}’".format(objtyp))
				try:
					v = v.mod.q.get_by(id=int(oid))
				except NoData:
					raise RuntimeError("I do not know the item ‘{}:{}’".format(objtyp,oid))
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
		self.add_option(Option("typ", nargs='?', action="store",help="The item's type; if missing: list types"))
		self.add_option(Option("id", type=int, nargs='?', action="store",help="The item's ID; if missing: list entries of that type"))
	def run(self,args, help=False, id=None,typ=None):
		quiet = current_app._manager_quiet
		json = current_app._manager_json
		exp = current_app._manager_expand
		if help or exp and json:
			self.parser.print_help()
			sys.exit(not help)

		if typ is None:
			data = RESTend(json).types()
			if exp is not None:
				data = [data]
		elif id is None:
			data = RESTend(json).list(typ)
			if exp is not None:
				data = [data]
		elif not args:
			data = RESTend(json).get(id=int(id),objtyp=typ)
			if not exp: exp = "-"
			data = [data]
		else:
			data = RESTend(json).get(typ,int(id))
			data = [getsubattr(data,a) for a in args]
			if exp is None and len(args) == 1:
				exp = "-"

		if not quiet:
			cache=Cache()
			for d in data:
				if json:
					print(encode(d))
				else:
					show(d, expand=exp, cache=cache)
		db.session.commit()
		
class CmdDIR(PrepCommand):
	"""Retrieve a list of records (or a list of record types)"""
	## TODO: allow expansion for JSON
	capture_all_args = True

	def __init__(self):
		super(CmdDIR,self).__init__()
		self.add_option(Option("typ", nargs='?', action="store",help="The item's type; if missing: list types"))
	def run(self, args, help=False, typ=None):
		quiet = current_app._manager_quiet
		json = current_app._manager_json
		exp = current_app._manager_expand
		if help:
			self.parser.print_help()
			sys.exit(not help)

		if typ is None:
			data = RESTend(json).types()
		else:
			data = RESTend(json).list(typ)

		if not quiet:
			for d in data:
				if json:
					print(encode(d))
				else:
					show(d, expand=exp)
		db.session.commit()
		
class CmdDELETE(PrepCommand):
	"""Delete a record"""
	def __init__(self):
		super(CmdDELETE,self).__init__()
		self.add_option(Option("-c", "--comment", dest="comment", action="store", required=False, help="Reason for this change"))
		self.add_option(Option("typ", nargs='?', action="store",help="The item's type; if missing: list types"))
		self.add_option(Option("id", type=int, nargs='?', action="store",help="The item's ID; if missing: list entries of that type"))
	def run(self, help=False, id=None,typ=None, comment=None):
		quiet = current_app._manager_quiet
		json = current_app._manager_json
		exp = current_app._manager_expand
		if help or not id:
			self.parser.print_help()
			sys.exit(not help)
		res = RESTend(json).delete(id=int(id),objtyp=typ, comment=comment)

		if not quiet:
			if json:
				print(encode(res))
			else:
				show(res, expand=exp)
		db.session.commit()
		
class CmdPOST(PrepCommand):
	"""Add a record"""
	capture_all_args = True
	def __init__(self):
		super(CmdPOST,self).__init__()
		self.add_option(Option("-c", "--comment", dest="comment", action="store", required=False, help="Reason for this change"))
		self.add_option(Option("typ", nargs='?', action="store",help="The item's type"))
	def run(self, args, typ=None,help=False,comment=None):
		quiet = current_app._manager_quiet
		json = current_app._manager_json
		exp = current_app._manager_expand
		if help or not args:
			self.parser.print_help()
			sys.exit(not help)
		data = _parse(args)
		res = RESTend(json).post(objtyp=typ, comment=comment, **data)

		if not quiet:
			if json:
				print(encode(res))
			else:
				show(res, expand=exp)
		db.session.commit()
		
class CmdPUT(PrepCommand):
	"""Change a record (clear not-mentioned data)"""
	capture_all_args = True
	def __init__(self):
		super(CmdPUT,self).__init__()
		self.add_option(Option("-c", "--comment", dest="comment", action="store", required=False, help="Reason for this change"))
		self.add_option(Option("typ", nargs='?', action="store",help="The item's type"))
		self.add_option(Option("id", type=int, nargs='?', action="store",help="The item's ID"))
	def run(self, args, typ=None,id=None,help=False,comment=None):
		quiet = current_app._manager_quiet
		json = current_app._manager_json
		exp = current_app._manager_expand
		if help or not args or not id:
			self.parser.print_help()
			sys.exit(not help)
		data = _parse(args)
		res = RESTend(json).put(id=int(id), objtyp=typ, comment=comment, **data)

		if not quiet:
			if json:
				print(encode(res))
			else:
				show(res, expand=exp)
		db.session.commit()
		
class CmdPATCH(PrepCommand):
	"""Change a record (don't touch not-mentioned data)"""
	capture_all_args = True
	def __init__(self):
		super(CmdPATCH,self).__init__()
		self.add_option(Option("-c", "--comment", dest="comment", action="store", required=False, help="Reason for this change"))
		self.add_option(Option("typ", nargs='?', action="store",help="The item's type"))
		self.add_option(Option("id", nargs='?', type=int, action="store",help="The item's ID"))
	def run(self, args, typ=None,id=None,help=False,comment=None):
		quiet = current_app._manager_quiet
		json = current_app._manager_json
		exp = current_app._manager_expand
		if help or not args or not id:
			self.parser.print_help()
			sys.exit(not help)
		id = int(id)
		data = _parse(args)
		res = RESTend(json).patch(id=int(id), objtyp=typ, comment=comment, **data)

		if not quiet:
			if json:
				print(encode(res))
			else:
				show(res, expand=exp)
		db.session.commit()
		
class RESTManager(Manager):
	"""Directly manipulate the database"""
	def __init__(self):
		super(RESTManager,self).__init__()
		self.add_option("-j", "--json", dest="json", action="store_true", required=False, help="emit JSON (input is TODO)")
		self.add_option("-x","--expand",action="append", dest="exp", help="additional detail to print")
		self.add_option("-q","--quiet",action="store_true", dest="quiet", required=False, help="do not print anything on success")

		self.add_command("get", CmdGET())
		self.add_command("replace", CmdPUT())
		self.add_command("add", CmdPOST())
		self.add_command("update", CmdPATCH())
		self.add_command("delete", CmdDELETE())
		self.add_command("list", CmdDIR())

	def __call__(self, app, json=False, exp=None, quiet=False):
		app._manager_quiet = quiet
		app._manager_json = json
		app._manager_quiet = quiet
		if exp:
			exp = ",".join(exp)
		app._manager_expand = exp
		return app
	
