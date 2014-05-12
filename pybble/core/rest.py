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
from .models import Object,Discriminator
from .models.tracking import Tracker,Change,Delete
from .json import encode

class RESTend(object):
	"""This implements a generic front-end to the database object system"""
	def __init__(self, json=True):
		self.json = json

	## TODO: permissions
	def get(self,id,descr=None):
		obj = Object.q.get_by(id=id)
		if descr is not None:
			D = Discriminator.get(descr).mod
			assert type(obj) is D, "{} is not a {}".format(str(obj),str(D))
		if self.json:
			obj = obj.as_dict
		return obj

	def put(self,id,descr=None, comment=None,**data):
		obj = Object.q.get_by(id=id)
		changed = {}
		if descr is not None:
			D = Discriminator.get(descr).mod
			assert D is type(obj), "{} is not a {}".format(str(obj),str(D))
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
			Change(obj, data=encode(changed), comment=comment)
		if self.json:
			obj = obj.as_dict
		return { "obj":obj, "changed":changed }
	
	def post(self,descr, comment=None,**data):
		D = Discriminator.get(descr).mod
		try:
			obj = D(**data)
		except TypeError as e:
			raise TypeError("{}: {}".format(D,e)) ## SIGH
		res = Tracker(request.user,obj, comment=comment)
		if self.json:
			res = res.as_dict
		return res

	def patch(self,id,descr=None, comment=None,**data):
		obj = Object.q.get_by(id=id)
		changed = {}
		if descr is not None:
			D = Discriminator.get(descr).mod
			assert D is type(obj), "{} is not a {}".format(str(obj),str(D))
		old = obj.as_dict
		for k,v in data.items():
			ov = getattr(obj,k,None)
			if ov != v:
				setattr(obj,k,v)
				changed[k] = (ov,v)
		if changed:
			res = Change(obj, data=encode(changed), comment=comment)
			if self.json:
				res = res.as_dict
		else:
			res = { 'obj': obj}
		return res
	
	def delete(self,id,descr=None, comment=None):
		obj = Object.q.get_by(id=id)
		if descr is not None:
			D = Discriminator.get(descr).mod
			assert D is type(obj), "{} is not a {}".format(str(obj),str(D))
		Delete(obj, comment=comment)
		if self.json:
			obj = obj.as_dict
		return { "obj":obj, "deleted":True }

	def list(self,descr=None):
		D = Discriminator
		if descr is not None:
			D = D.get(descr).mod

		res = []
		for obj in D.q.all():
			if self.json:
				obj = obj.as_dict
			res.append(obj)
		return res
		
	def types(self):
		res = []
		for descr in Discriminator.q.all():
			if self.json:
				descr = descr.as_dict
			res.append(descr)
		return res

