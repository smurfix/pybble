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

# This module describes the basic object type table.

from sqlalchemy import Unicode,Integer

from flask._compat import string_types,text_type

from . import LEN_NAME,LEN_DOC
from ._utils import Loadable
from .object import Object
from ..json import json_adapter
from ..db import db, NoData, refresh

_type_id = {}
_type_name = {}
_typemod_id = {}
_typemod_name = {}

class ObjType(Loadable, Object):
	"""Object registry"""
	__tablename__ = "objtype"

	name = db.Column(Unicode(LEN_NAME), nullable=False, unique=True)
	doc = db.Column(Unicode(LEN_DOC), nullable=True)

	def __str__(self):
		return u'‹T:%s %s›' % (self.id, self.name)
	def __repr__(self):
		return '<T:%s %s>' % (self.id, self.name)

	def setup(self, name,doc=None,**kw):
		if name.startswith("pybble.core.models."):
			name = name.rsplit('.',1)[-1]
		self.name = name
		if doc is not None:
			self.doc = doc
		super(ObjType,self).setup(**kw)
	
	@classmethod
	def get(cls, typ, obj=None):
		"""\
			Resolve 'something' to an object type, or (of the second
			parameter is an integer) to an object.
			
			"""
		if typ is None and obj is None:
			return None
		if typ is not None and obj is not None:
			if isinstance(obj,(int,long)):
				return cls.get(typ).get_obj(obj)
			typ = cls.get(typ)
			assert obj.type is typ, str((obj.type,typ))
			return typ

		if hasattr(typ,'_get_current_object'): # Flask localproxy
			typ = typ._get_current_object()
		if isinstance(typ,type) and issubclass(typ, Object):
			path = typ.__module__+'.'+typ.__name__
			try:
				return cls.q.get_by(path=path)
			except NoData:
				from .types import MIMEtype
				res = cls.new(path=path,name=path)
				mime = MIMEtype.get("pybble",typ.__name__.lower(),add=res)
				return res
		if isinstance(typ, string_types):
			try: typ = int(typ)
			except ValueError: pass
		if isinstance(typ, cls):
			return typ
		if isinstance(typ, Object):
			typ = typ.type_id
		if isinstance(typ, string_types):
			res = _type_name.get(typ,None)
			if res is not None:
				return refresh(res)
			res = cls.q.get_by(name=text_type(typ))
		elif isinstance(typ, (int,long)):
			res = _type_id.get(typ,None)
			if res is not None:
				return refresh(res)
			res = cls.q.get_by(id=typ)
		else:
			raise RuntimeError("No known way to get an object type for "+str(typ))
		_type_id[res.id] = res
		_type_name[res.name] = res
		_typemod_id[res.id] = res.mod
		_typemod_name[res.name] = res.mod
		return res

	@classmethod
	def get_mod(cls, typ):
		"Optimization"
		if isinstance(typ, string_types):
			res = _typemod_name.get(typ,None)
			if res is not None:
				return res
			res = cls.q.get_by(name=text_type(typ))
		elif isinstance(typ, (int,long)):
			res = _typemod_id.get(typ,None)
			if res is not None:
				return res
			res = cls.q.get_by(id=typ)
		else:
			raise RuntimeError("No known way to get an object type for "+str(typ))
		_type_id[res.id] = res
		_type_name[res.name] = res
		_typemod_id[res.id] = res.mod
		_typemod_name[res.name] = res.mod
		return res.mod
		
	def get_obj(self, id):
		return self.mod.q.get_by(id=id)

@json_adapter
class _serialize_objtype(object):
	cls = ObjType
	clsname = "objtyp"
	
	@staticmethod
	def encode(obj):
		res = {"t":obj.id, "s":str(obj)}
		return res
		
	@staticmethod
	def decode(t,s=None,**_):
		return ObjType.get(t)

