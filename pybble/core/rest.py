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

from .models import Object,Discriminator
from .models.tracking import Tracker,Change,Delete
from .json import encode

class RESTend(object):
	"""This implements a generic front-end to the database object system"""

	## TODO: permissions

	def get(self,id,descr=None):
		obj = Object.q.get_by(id=id)
		if descr is not None:
			D = Discriminator.get(descr).mod
			assert type(obj) is D, "{} is not a {}".format(str(obj),str(D))
		return obj.as_dict

	def put(self,id,descr=None, comment=None,**data):
		obj = Object.q.get_by(id=id)
		changed = {}
		if descr is not None:
			D = Discriminator.get(descr).mod
			assert D is type(Object), "{} is not a {}".format(str(obj),str(D))
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
			Change(request.user,obj, data=encode(changed), comment=comment)
		return { "obj":obj, "changed":changed }
	
	def post(self,descr, comment=None,**data):
		D = Discriminator.get(descr).mod
		obj = D(**data)
		Tracker(request.user,obj, comment=comment)
		return obj

	def patch(self,id,descr=None, comment=None,**data):
		obj = Object.q.get_by(id=id)
		changed = {}
		if descr is not None:
			D = Discriminator.get(descr).mod
			assert D is type(Object), "{} is not a {}".format(str(obj),str(D))
		old = obj.as_dict
		for k,v in data.items():
			ov = getattr(obj,k,None)
			if ov != v:
				setattr(obj,k,v)
				changed[data] = (ov,v)
		if changed:
			Change(request.user,obj, data=encode(changed), comment=comment)
		return { "obj":obj, "changed":changed }
	
	def delete(self,id,descr=None):
		obj = Object.q.get_by(id=id)
		if descr is not None:
			D = Discriminator.get(descr).mod
			assert D is type(Object), "{} is not a {}".format(str(obj),str(D))
		Delete(request.user, obj, comment=comment)
		return { "obj":obj, "deleted":True }

	def list(self,descr=None):
		D = Discriminator
		if descr is not None:
			D = D.get(descr).mod

		res = []
		for obj in D.q.all():
			res.append(obj.as_dict)
		return res
		
	def types(self):
		res = []
		for descr in Discriminator.q.all():
			res.append(descr.as_dict)
		return res

