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

from flask import request
from .db import db
from .models.object import Object
from .models.objtyp import ObjType
from .models.tracking import Tracker,Change,Delete
from .json import encode

class RESTend(object):
	"""This implements a generic front-end to the database object system"""
	def __init__(self, json=True):
		self.json = json

	## TODO: permissions
	def get(self,objtyp,id):
		obj = ObjType.get(objtyp,id)
		if self.json:
			obj = obj.as_dict
		return obj

	def put(self,objtyp,id, comment=None,**data):
		obj = ObjType.get(objtyp,id)
		changed = {}
		old = obj.as_dict
		for k,v in data.items():
			ov = getattr(obj,k,None)
			if ov != v:
				setattr(obj,k,v)
				changed[data] = (ov,v)
		for k,v in old.items():
			if k not in data and v is not None:
				setattr(obj,k,None)
				changed[data] = (ov,None)
		if changed:
			Change.new(obj, data=encode(changed), comment=comment)
		if self.json:
			obj = obj.as_dict
		return { "obj":obj, "changed":changed }
	
	def post(self,objtyp, comment=None,**data):
		objtyp = ObjType.get(objtyp)
		try:
			obj = objtyp.mod.new(**data)
		except TypeError as e:
			raise TypeError("{}: {}".format(objtyp,e)) ## SIGH
		res = Tracker.new(obj, comment=comment)
		if self.json:
			res = res.as_dict
		return res

	def patch(self,objtyp,id, comment=None,**data):
		obj = ObjType.get(objtyp,id)
		changed = {}

		old = obj.as_dict
		for k,v in data.items():
			ov = getattr(obj,k,None)
			if ov != v:
				setattr(obj,k,v)
				changed[k] = (ov,v)
		if changed:
			res = Change.new(obj, data=encode(changed), comment=comment)
			if self.json:
				res = res.as_dict
		else:
			res = { 'obj': obj}
		return res
	
	def delete(self,typ,id, comment=None):
		obj = ObjType.get(typ,id)
		Delete.new(obj, comment=comment)
		if self.json:
			obj = obj.as_dict
		return { "obj":obj, "deleted":True }

	def list(self,typ=None):

		res = []
		for obj in ObjType.get(typ).mod.q.all():
			if self.json:
				obj = obj.as_dict
			res.append(obj)
		return res
		
	def types(self):
		res = []
		for objtyp in ObjType.q.all():
			if self.json:
				objtyp = objtyp.as_dict
			res.append(objtyp)
		return res

