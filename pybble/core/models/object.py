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

# This module contains the basic code for the "Object" class of tables.
# An object is something in some table that is referenceable from a 
# random table via a special composite object.
#
# Needless to say, there is no such thing as referential integrity here.
# (Pybble will handle that transparently. TODO.)

import sys
from base64 import urlsafe_b64encode
try:
	from hashlib import md5
except ImportError:
	from md5 import md5

from datetime import datetime,timedelta
from functools import update_wrapper
from itertools import chain

from sqlalchemy import Integer, Unicode, ForeignKey, event, Index
from sqlalchemy.orm import relationship,backref,composite, mapper
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.inspection import inspect

from ...compat import py2_unicode
from ..json import json_adapter
from ..signal import ObjSignal

from ..db import Base, Column, IDrenderer, db, NoData, maybe_stale, no_autoflush, refresh, setup_events, Dumpable
from ._const import PERM_ADD,PERM_READ

from flask import current_app
from flask._compat import text_type, string_types
from werkzeug.utils import cached_property

ObjectRef = None # cyclic forward decl

class _serialize_object(object):
	"""Reference superclass for JSONification"""
	cls = None
	clsname = None

	@staticmethod
	def encode(obj):
		res = {"t":(obj.typ,obj.subtyp), "s":str(obj)}
		if obj.ext is not None:
			res['x'] = obj.ext
		return res

	@staticmethod
	def decode(t=None,s=None,x=None,**_):
		return ObjType.q.get_by(typ=t[0],subtyp=t[1])

_tables = [] # A list of new tables
_refs = [] # A list of "any-table" references (tableobject,columnname)
class ObjectMeta(type(Base)):
	"""\
		Metaclass to auto-setup *-to-one relationships

		Usage:
		
			class Foo(Object):
				bar = ObjectRef(Bar) ## points to instances of `Bar` (referential integrity OK)
				baz = ObjectRef()    ## points to any instance whatsoever (NO referential integrity!)
		
		Options for `ObjectRef`:

		:param backref:       Install a one-to-many list in the "other" direction
		:param nullable:      indicates whether the reference can be NULL, default False
		:param doc:           docstring for the relationship
		:param declared_attr: Flag whether relationship setup should be postponed
		                      Don't set: this code is fragile and not tested
		"""
	def __init__(cls, name, bases, dct):
		if "modified" in dct:
			event.listen(cls,'before_update',update_modified)
			
		if "id" not in dct:
			# the inherited class already has an 'id' column, but that ends
			# up being ambiguous and thus won't work
			dct['id'] = cls.id = Column(Integer, primary_key=True)
		cls._refs = []
		cls.__table_args__ = list(dct.get('__table_args__',[])) # collect indices for foreign-key tables here

		for k,v in dct.items():
			if ObjectRef is not None and isinstance(v,ObjectRef):
				if v.typ is None: ## any table
					from .objtyp import ObjType

					## Create a new composite.
					if v.declared_attr:
						col_typ = declared_attr((lambda k,v: lambda cls: Column(k+'_typ_id',Integer, ForeignKey(ObjType.id),nullable=v.nullable, doc=v.doc))(k,v))
						col_id = declared_attr((lambda k,v: lambda cls: Column(k+'_id',Integer, nullable=v.nullable))(k,v))
					else:
						col_typ = Column(k+'_typ_id',Integer, ForeignKey(ObjType.id),nullable=v.nullable, doc=v.doc)
						col_id = Column(k+'_id',Integer, nullable=v.nullable)
					setattr(cls,k+"_typ_id", col_typ)
					setattr(cls,k+"_id", col_id)
					if v.declared_attr:
						setattr(cls,k, declared_attr((lambda col_typ,col_id: lambda cls: composite(ObjectRef, col_typ,col_id, deferred=True))(col_typ,col_id)))
					else:
						setattr(cls,k, composite(Object._compose, col_typ,col_id, deferred=True))
					_refs.append((cls,k))
					cls.__table_args__.append(Index("i_%s_%s"%(name,k),col_typ,col_id))
				else: ## specific table
					rem = {}
					if v.backref:
						rem['back_populates'] = v.backref
					if isinstance(v.typ,(int,long)):
						v.typ = ObjType.q.get(id=typ).mod
						v.typ_id = v.typ.id
					elif isinstance(v.typ,string_types):
						if v.typ == "self":
							col_typ = Column(k+'_id',Integer, ForeignKey(cls.__tablename__+'.id'),nullable=v.nullable, doc=v.doc)
							col_ref = relationship(cls, remote_side=[cls.id], foreign_keys=(col_typ,), **rem)
							setattr(cls,k+"_id", col_typ)
							setattr(cls,k, col_ref)
							cls._refs.append((cls,k))
							cls.__table_args__.append(Index("i_%s_%s"%(name,k),col_typ))
							if v.backref:
								setattr(cls,v.backref, relationship(cls, primaryjoin = col_typ==cls.id, back_populates=k))
							continue
						else:
							v.typ = ObjType.q.get(path=typ).mod
							v.typ_id = v.typ.id
					else:
						v.typ_id = v.typ.id
						rem['remote_side'] = v.typ.__name__+'.id'
					if v.declared_attr:
						col_typ = declared_attr((lambda k,v: lambda cls: Column(k+'_id',Integer, ForeignKey(v.typ_id),nullable=v.nullable, doc=v.doc))(k,v))
						col_ref = declared_attr((lambda k,v,r: lambda cls: relationship(v.typ, primaryjoin = col_typ==v.typ_id, **r))(k,v,rem))
					else:
						col_typ = Column(k+'_id',Integer, ForeignKey(v.typ_id),nullable=v.nullable, doc=v.doc)
						col_ref = relationship(v.typ, primaryjoin = col_typ==v.typ_id, **rem)
					setattr(cls,k+"_id", col_typ)
					setattr(cls,k, col_ref)
					v.typ._refs.append((cls,k))
					cls.__table_args__.append(Index("i_%s_%s"%(name,k),col_typ))
					if v.backref:
						if isinstance(v.typ,string_types):
							setattr(v.typ,v.backref, relationship(cls, primaryjoin = "%s_id==%s" % (k,v.typ_id), back_populates=k))
						else:
							setattr(v.typ,v.backref, relationship(cls, primaryjoin = col_typ==v.typ.id, back_populates=k))
				
			elif k == 'modified':
				event.listen(cls,'before_update',update_modified)
			
		_tables.append(cls)
		cls_ = cls
		cls.__table_args__ = tuple(cls.__table_args__)
		class serializer(_serialize_object):
			cls = cls_
			clsname = cls_.__module__+'.'+cls_.__name__
		json_adapter(serializer)

		setup_events(cls)

		super(ObjectMeta, cls).__init__(name, bases, dct)

def update_modified(mapper, connection, target):
	"""Utility helper for event.listen('before_update')"""
	target.modified = datetime.utcnow()

_type = {}
class Object(Base):
	__metaclass__ = ObjectMeta
	__abstract__ = True

	_rec_str = 0 ## marker for possibly-recursive __str__ calls
	_deleting = False ## marker for skipping some do-not-modify tests

	_no_crumbs = False ## if True, don't create Breadcrumb data when visiting

	## Default permissions
	_site_perm=None
	_anon_perm=None
	_admin_perm=PERM_ADD

	def __composite_values__(self):
		return self.type.id, self.id

	@staticmethod
	def _compose(type,id):
		from .objtyp import ObjType
		return ObjType.get(type, id)

	@property
	def type(self):
		cls = self.__class__
		t = _type.get(id(cls),None)
		if t is None:
			from .objtyp import ObjType
			_type[id(cls)] = t = ObjType.get(cls)
			return t
		else:
			return refresh(t)
		
	@classmethod
	def get(cls,id):
		return cls.q.get_by(id=id)

	@cached_property
	def oid(self):
		"""
			Return a crypto ID of an object.
			This is done so that simply enumerating object IDs off the web pages wont work.
			"""
		if self.id is None:
			db.flush()
		return "%d.%d.%s" % (self.type.id,
		                     self.id, 
		                     urlsafe_b64encode(md5(str(self.type.id) +'.'+ str(self.id) + current_app.config.SECRET_KEY)\
		                                          .digest()).strip('\n =')[:10])

	@staticmethod
	def by_oid(oid):
		"""Given an object ID, return the object"""
		try:
			cid,id,hash = oid.split(".")
		except ValueError:
			raise ValueError("bad OID: '%s'" % (oid,))
		cls = Discriminator.get(cid).mod
		obj = cls.q.get_by(id=int(id))
		if oid != obj.oid:
			raise ValueError("This object does not exist: " % (oid,))
		return obj

	## membership, somewhat generalized

	_member_rules = []
	class _rules(object):
		def __init__(self, table,src,dst, args):
			self.table = table
			self.src = src
			self.dst = dst
			self.args = args

	def all_memberships(self, typ=None):
		"""Return all objects (of some type?) I am a member of."""
		if typ is not None:
			typ = ObjTyp.get(typ)
		for t in self._member_rules:
			q = dict(t.args)
			q[t.src] = self
			for m in t.table.q.filter_by(**q):
				mm = getattr(m,t.dst)
				if typ is None or mm.type is typ:
					yield m,mm

	@property
	def memberships(self):
		return self.all_memberships()

	@classmethod
	def new_member_rule(cls, table,src,dst, **args):
		cls._member_rules.append(cls._rules(table,src,dst,args))

	def all_memberships(self, objtyp=None):
		"""Return all objects (of some type?) I am a member of."""
		from .objtyp import ObjType

		objtyp = ObjType.get(objtyp)
		for t in self._member_rules:
			q = dict(t.args)
			q[t.src] = self
			for m in t.table.q.filter_by(**q):
				mm = getattr(m,t.dst)
				if objtyp is None or mm.type == objtyp:
					yield m,mm

	@property
	def all_refs(self, typ=None):
		"""\
			Return all (obj,attr) tuples where getattr(obj,attr)==self.
			if typ != None, also limit to isinstance(obj,typ).
			"""
		if typ is not None and (not isinstance(typ,type) or not issubclass(typ,Object)):
			typ = ObjType.get(objtyp).mod

		for t,k in chain(_refs,self._refs):
			if typ is not None and typ is not t:
				continue
			for r in t.q.filter(getattr(t,k) == self):
				yield r,k

	@property
	def signal(self):
		"""\
			A unique and site-wide signaller for this object.
			See ``blinker.Signal`` for details.
			"""
		return ObjSignal(self)

	@property
	def _stale(self):
		"""Check whether an object should not be displayed en detail, and why"""
		i = inspect(self)
		if i.expired: return "EXP"
		return ""

	def __str__(self):
		s = self._stale
		if s or self._rec_str>1: return '‹%s:%s %s›' % (self.__class__.__name__, self.id, s)

		if self.deleted: d = "DEL "
		else: d = ""
		s = self.as_str
		if s is None:
			s = ""
		else:
			s = " "+s
		return u'‹%s%s:%s%s›' % (d,self.__class__.__name__, self.id, s)

	def __repr__(self):
		s = self._stale
		if s or self._rec_str>1: return '<%s:%s %s>' % (self.__class__.__name__, self.id, s)
		try:
			return str(self)
		except Exception as err:
			return '<%s:%s ?? %s>' % (self.__class__.__name__, self.id, str(err))

	@property
	def as_str(self):
		if hasattr(self,"name"):
			return self.name
		else:
			return None

class ObjectRef(object):
	def __init__(self, typ=None,backref=None, nullable=False, doc=None, declared_attr=False):
		self.typ = typ
		self.backref = backref
		self.nullable = nullable
		self.doc = doc
		self.declared_attr = declared_attr


@event.listens_for(mapper, "after_configured")
def add_objtypes():
	"""Initialize ObjType and MIMEtype entries for our tables"""
	from .objtyp import ObjType
	global _tables
	for t in _tables:
		typ = ObjType.get(t)
		for pm in ('site','admin','anon'):
			if getattr(typ,pm+'_permission',None) is not None:
				continue
			setattr(typ,pm+'_permission', getattr(t,'_'+pm+'_perm',None))

	_tables = []
	
