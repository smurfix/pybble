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
try:
	from jinja2 import is_undefined
except ImportError:
	def is_undefined(x):
		return False

from datetime import datetime,timedelta
from functools import update_wrapper
from itertools import chain

from sqlalchemy import Integer, Unicode, ForeignKey, event, Index
from sqlalchemy.orm import backref,composite, mapper
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.inspection import inspect

from ..forms import FieldSet

from ...compat import py2_unicode
from ...cache import delete as delete_cache
from ..utils import hybridmethod
from ..json import json_adapter
from ..signal import ObjSignal

from ..db import db, NoData,NoDataExc, maybe_stale, no_autoflush, refresh, setup_events, Dumpable
from ._const import PERM_ADD,PERM_READ,PERM_ADMIN
from ._render import Rendered

from flask import current_app
from flask._compat import text_type, string_types
from werkzeug.utils import cached_property

ObjectRef = None
# This is here to break a cyclic reference problem:
# * ObjectRef wants to refer to Object
# * Object needs ObjectMeta when initializing
# * ObjectMeta needs to special-case ObjectRef instances
#
# We resolve this by leaving ObjectRef as None here, since it's only
# used in subclasses of Object, and declaring it for real at the bottom
# of this file.

class _serialize_object(object):
	"""Reference superclass for JSONification"""
	cls = None
	clsname = None

	@staticmethod
	def encode(obj):
		res = {"t":(obj.type_id,obj.id), "s":str(obj)}
		return res

	@staticmethod
	def decode(t=None,s=None,x=None,**_):
		from .objtyp import ObjType
		return ObjType.get(t[0],t[1])

_tables = [] # A list of new tables
_refs = [] # A list of "any-table" references (tableobject,columnname)
class ObjectMeta(type(db.Model)):
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
			dct['id'] = cls.id = db.Column(Integer, primary_key=True)
		cls._refs = []
		cls.__table_args__ = list(dct.get('__table_args__',[])) # collect indices for foreign-key tables here

		# Now walk through all our (base) classes.
		# This is necessary to collect ObjectRef entries in subclasses
		seen = set()
		_alias = cls._alias

		for ccls in cls.__mro__:
			for k,v in ccls.__dict__.items():
				if k == "_alias":
					# merge _alias content
					for kk,vv in v.items():
						_alias.setdefault(kk,vv)
					continue
				if k.startswith('_'): continue
				if k in seen: continue
				seen.add(k)

				if ObjectRef is not None and isinstance(v,ObjectRef):
					if v.typ is None: ## any table
						from .objtyp import ObjType

						## Create a new composite.
						if v.declared_attr:
							col_typ = declared_attr((lambda k,v: lambda cls: Column(k+'_typ_id',Integer, ForeignKey(ObjType.id),nullable=v.nullable, doc=v.doc, unique=v.unique))(k,v))
							col_id = declared_attr((lambda k,v: lambda cls: Column(k+'_id',Integer, nullable=v.nullable))(k,v))
						else:
							col_typ = db.Column(k+'_typ_id',Integer, ForeignKey(ObjType.id),nullable=v.nullable, doc=v.doc, unique=v.unique)
							col_id = db.Column(k+'_id',Integer, nullable=v.nullable)
						setattr(cls,k+"_typ_id", col_typ)
						setattr(cls,k+"_id", col_id)
						if v.declared_attr:
							setattr(cls,k, declared_attr((lambda col_typ,col_id: lambda cls: composite(ObjectRef, col_typ,col_id, deferred=True))(col_typ,col_id)))
						else:
							setattr(cls,k, composite(ObjRefComposer, col_typ,col_id, deferred=True))
						_refs.append((cls,k))
						cls.__table_args__.append(Index("i_%s_%s"%(name,k),col_typ,col_id))
					else: ## specific table
						rem = {'lazy': v.lazy}
						if v.backref:
							rem['back_populates'] = v.backref
						if isinstance(v.typ,(int,long)):
							v.typ = ObjType.get_mod(v.typ)
							v.typ_id = v.typ.id
						elif isinstance(v.typ,string_types):
							if v.typ == "self":
								col_typ = db.Column(k+'_id',Integer, ForeignKey(cls.__tablename__+'.id'),nullable=v.nullable, doc=v.doc, unique=v.unique)
								col_ref = db.relationship(cls, remote_side=[cls.id], foreign_keys=(col_typ,), **rem)
								setattr(cls,k+"_id", col_typ)
								setattr(cls,k, col_ref)
								cls._refs.append((cls,k))
								cls.__table_args__.append(Index("i_%s_%s"%(name,k),col_typ))
								if v.backref:
									setattr(cls,v.backref, db.relationship(cls, primaryjoin = col_typ==cls.id, back_populates=k, uselist=not v.unique))
								continue
							else:
								v.typ = ObjType.q.get_by(path=v.typ).mod
								v.typ_id = v.typ.id
						else:
							v.typ_id = v.typ.id
							rem['remote_side'] = v.typ.__name__+'.id'
						if v.declared_attr:
							col_typ = declared_attr((lambda k,v: lambda cls: Column(k+'_id',Integer, ForeignKey(v.typ_id),nullable=v.nullable, doc=v.doc, unique=v.unique))(k,v))
							col_ref = declared_attr((lambda k,v,r: lambda cls: db.relationship(v.typ, primaryjoin = col_typ==v.typ_id, **r))(k,v,rem))
						else:
							col_typ = db.Column(k+'_id',Integer, ForeignKey(v.typ_id),nullable=v.nullable, doc=v.doc, unique=v.unique)
							col_ref = db.relationship(v.typ, primaryjoin = col_typ==v.typ_id, **rem)
						setattr(cls,k+"_id", col_typ)
						setattr(cls,k, col_ref)
						v.typ._refs.append((cls,k))
						cls.__table_args__.append(Index("i_%s_%s"%(name,k),col_typ))
						if v.backref:
							if isinstance(v.typ,string_types):
								setattr(v.typ,v.backref, db.relationship(cls, primaryjoin = "%s_id==%s" % (k,v.typ_id), back_populates=k))
							else:
								setattr(v.typ,v.backref, db.relationship(cls, primaryjoin = col_typ==v.typ.id, back_populates=k, uselist=not v.unique))
					
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

class get_type(object):
	_type = {}
	def __get__(self, obj, cls):
		if obj:
			cls = obj.__class__
		t = self._type.get(id(cls),None)
		if t is None:
			from .objtyp import ObjType
			self._type[id(cls)] = t = ObjType.get(cls)
			return t
		else:
			return refresh(t)
get_type = get_type()

class get_type_id(object):
	"""Optimized get_type.id"""
	_type = {}
	def __get__(self, obj, cls):
		if obj:
			cls = obj.__class__
		t = self._type.get(id(cls),None)
		if t is None:
			from .objtyp import ObjType
			self._type[id(cls)] = t = ObjType.get(cls)
		k = inspect(t).key
		if k is None:
			raise NoDataExc("ObjType for {}".format(cls))
		return inspect(t).key[1][0]
get_type_id = get_type_id()

class ObjRefComposer(object):
	def __new__(cls,type=None,id=None):
		if type is None:
			return object.__new__(cls)
		from .objtyp import ObjType
		return ObjType.get_mod(type).qq.cached('DB',type,id).get_by(id=id)

class Object(db.Model,Rendered):
	__metaclass__ = ObjectMeta
	__abstract__ = True

	_rec_str = 0 ## marker for possibly-recursive __str__ calls
	_deleting = False ## marker for skipping some do-not-modify tests
	_is_new = False ## marker for just having been created

	_no_crumbs = False ## if True, don't create Breadcrumb data when visiting

	## Default permissions
	_site_perm=None
	_site_add_perm=()
	_anon_perm=None
	_anon_add_perm=()
	_admin_perm=PERM_ADMIN
	_admin_add_perm=()
	_alias = {}
	## The *_add_perm entries denote to which objects the user can add this type,
	## so
	##		class Comment(Object):
	##		_site_add_perm=('Site','Wikipage',)
	## means that anybody may by default add comments to these objects
	## This only applies when initially setting up the root site

	## Overriding these lists means adding to them, not replacing.
	form_hidden = ('deleted',)
	form_readonly = ('id',)
	@hybridmethod
	def form_mod(self, fs,parent=None):
		"""\
			Override this for specific form changes.

			:Note: your code is run twice when copying a record, so it must be idempotent.
			"""
		if parent is not None:
			f = self._alias.get('parent','parent')
			fs.set(f,parent)

	def __composite_values__(self):
		return self.type_id, self.id
	def __init__(self, type=None,id=None):
		if type is not None:
			assert self.type==type
		if id is not None:
			assert self.id==id

	type = get_type
	type_id = get_type_id

	@hybridmethod
	def fieldset(obj, parent=None):
		"""Helper to generate a FormAlchemy fieldset for this object/class"""
		from .objtyp import ObjType
		hide = []
		opts = []
		if isinstance(obj,Object) and not isinstance(obj,ObjType) and not parent: # it's new
			fs = FieldSet(obj)
			cls = type(obj)
			for fn,f in fs._fields.items():
				if getattr(cls,'_pybble_block_'+fn, False):
					opts.append(f.readonly())
		
		elif isinstance(obj,Object) and not isinstance(obj,ObjType): # it's a copy
			assert parent is not None
			fs = obj.fieldset() # get a fieldset with the original data
			data = fs.to_dict(with_prefix=False) # copy it
			fs = fs.bind(model=type(obj),data=data,with_prefix=False, session=db.session())
			obj.form_mod(fs,parent)
			return fs
		else:
			if isinstance(obj,ObjType):
				cls = obj.mod
			else:
				cls = obj
			obj = None
			fs = FieldSet(cls, session=db.session())

		seen = set()
		for c in cls.__mro__:
			for k in getattr(c,'form_readonly',()):
				if k not in seen:
					opts.append(getattr(fs,k).readonly())
					seen.add(k)
			for k in getattr(c,'form_hidden',()):
				if k not in seen:
					hide.append(getattr(fs,k))
					seen.add(k)

		if hasattr(fs,'config'):
			hide.append(fs.config)
		if hasattr(fs,'modified'):
			opts.append(fs.modified.readonly())
		fs.configure(options=opts, exclude=hide)
		if obj is not None:
			fs.reconfigure(pk=True)
		(obj or cls).form_mod(fs,parent)
		return fs

	def setup(self,**k):
		super(Object,self).setup(**k)
		self._is_new = True

	@hybridmethod
	def __getattr__(self,k):
		"""Observe _alias array"""
		try:
			return getattr(self,self._alias[k])
		except KeyError:
			raise AttributeError(k)

	@property
	def mimetype(self):
		return self.type.mimetype
		
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
			db.session.flush()
		return "%d.%d.%s" % (self.type_id,
		                     self.id, 
		                     urlsafe_b64encode(md5(str(self.type_id) +'.'+ str(self.id) + current_app.config['SECRET_KEY'])\
		                                          .digest()).strip('\n =')[:10])

	def _dump_attrs(self):
		res = super(Object,self)._dump_attrs()
		res.add('oid')
		return res

	@staticmethod
	def by_oid(oid):
		"""Given an object ID, return the object"""
		from .objtyp import ObjType

		try:
			cid,id,hash = oid.split(".")
			cid=int(cid)
			id=int(id)
			obj = ObjType.get_mod(cid).q.get_by(id=id)
		except ValueError:
			pass
		except NoData:
			pass
		else:
			if oid == obj.oid:
				return obj
		# Intentionally does not distinguish between format and value errors
		raise ValueError("This object does not exist: ‘{}’".format(oid))

	## membership, somewhat generalized

	_member_rules = []
	class _rules(object):
		"""Storage object"""
		def __init__(self, table,src,dst, args):
			self.table = table
			self.src = src
			self.dst = dst
			self.args = args

	@property
	def ancestors(self):
		while self:
			yield self
			self = getattr(self,'parent',None)

	def all_memberships(self, typ=None):
		"""Return all objects (of some type?) I am a member of."""
		from .objtyp import ObjType

		if typ is not None:
			typ = ObjTyp.get(typ)
		for t in self._member_rules:
			q = dict(t.args)
			q[t.src] = self
			for m in t.table.q.filter_by(**q):
				mm = getattr(m,t.dst)
				if typ is None or mm.type is typ:
					yield m,mm

	def has_children(self,typ):
		return self.all_children(typ).count()

	def all_children(self,typ):
		from .objtyp import ObjType

		if is_undefined(typ):
			from sqlalchemy.sql import false
			return ObjType.q.filter(false())
		return ObjType.get_mod(typ).q.filter_by(parent=self)

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

	def member_of(self,obj):
		"""Am I a member of this?"""
		for t in self._member_rules:
			q = dict(t.args)
			q[t.src] = self
			q[t.dst] = obj
			for m in t.table.q.filter_by(**q):
				return not getattr(m,"excluded",False)

		# Not directly. See if there's any group with self in it
		from .user import Group

		for g in Group.q.filter_by(parent=obj):
			r = self.member_of(g)
			if r is not None:
				return r
			
		return None

	@property
	def all_refs(self, typ=None):
		"""\
			Return all (obj,attr) tuples where getattr(obj,attr)==self.
			if typ != None, also limit to isinstance(obj,typ).
			"""
		from .objtyp import ObjType

		if typ is not None and (not isinstance(typ,type) or not issubclass(typ,Object)):
			typ = ObjType.get_mod(objtyp)

		for t,k in chain(_refs,self._refs):
			if typ is not None and typ is not t:
				continue
			for r in t.q.filter(getattr(t,k) == self):
				yield r,k

	def _dump(self, add_none=False, cols=None):
		res = super(Object,self)._dump(add_none=add_none,cols=cols)
		res['_refs'] = r = {}
		for t,k,c in self.count_refs():
			r[t.__name__+'_'+k] = tuple(self.get_refs(t,k))
		return res

	def count_refs(self):
		"""Return #references as (objtype,key,num) tuples"""
		for t,k in chain(_refs,self._refs):
			c = t.q.filter(getattr(t,k) == self).count()
			if c:
				yield t,k,c
	
	def get_refs(self,cls,key):
		"""Return all references to me from this object+key"""
		from .objtyp import ObjType

		if isinstance(cls,ObjType):
			cls = cls.mod
		for r in cls.q.filter(getattr(cls,key)==self):
			yield r

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

	def before_insert(self):
		"""Create the type"""
		from .objtyp import ObjType
		ObjType.get(self)

		super(Object,self).before_insert()

	def after_update(self):
		"""Clear cache"""
		delete_cache('DB', self.type_id,self.id)
		super(Object, self).after_update()

	@property
	def as_str(self):
		if hasattr(self,"name"):
			return self.name
		else:
			return None

class ObjectRef(object):
	def __init__(self, typ=None,backref=None, nullable=False, doc=None, declared_attr=False, unique=False, lazy=True):
		self.typ = typ
		self.backref = backref
		self.nullable = nullable
		self.unique = unique
		self.doc = doc
		self.lazy = lazy
		self.declared_attr = declared_attr

