#!/usr/bin/python
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

from functools import wraps, partial

from sqlalchemy import create_engine, Integer, types, util, exc as sa_exc, event, or_, Boolean
from sqlalchemy.orm import scoped_session, sessionmaker,query,class_mapper, ColumnProperty
from sqlalchemy.inspection import inspect
from sqlalchemy.orm.session import Session
from sqlalchemy.orm.base import NO_VALUE,NEVER_SET
from sqlalchemy.orm.attributes import instance_state
from sqlalchemy.orm.exc import NoResultFound as NoData, MultipleResultsFound
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.pool import AssertionPool
from sqlalchemy.types import TypeDecorator, VARCHAR,Unicode
from sqlalchemy.util import IdentitySet

from formalchemy import Column as FAColumn, helpers
from formalchemy.fields import IntegerFieldRenderer,TextAreaFieldRenderer, TextFieldRenderer

from flask import Markup, url_for, escape, g, request
from flask._compat import implements_to_string as py2_unicode, text_type
from flask.ext.migrate import Migrate
import flask.ext.sqlalchemy as flask_sqla
from flask.ext.sqlalchemy import SQLAlchemy as BaseSQLAlchemy, BaseQuery, _BoundDeclarativeMeta, UnmappedClassError, _SignallingSession

from . import json
from . import config
from .models import LEN_JSON
from ..cache import keystr
from ..cache.query import FromCache,CachingQuery
from ..cache import config as cache

import logging
logger = logging.getLogger('pybble.core.db')

def _BaseColumn(col, *a,**k):
	if "renderer" not in k and ((col in (Unicode,VARCHAR,JSON)) or isinstance(col,(Unicode,VARCHAR,JSON))):
		if col is JSON or col.length > 255:
			k['renderer'] = TextAreaFieldRenderer
		else:
			k['renderer'] = TextFieldRenderer
	return FAColumn(col,*a,**k)
BaseColumn = staticmethod(_BaseColumn)

class ManyDataExc(IntegrityError,MultipleResultsFound):
	"""Class for tests of unique constraint violations"""
	msg = None
	def __init__(self, msg):
		self.msg = msg
	def __str__(self):
		return "{}: {}".format(self.__class__.__name__,self.msg)
	def __repr__(self):
		return "<{}: {}>".format(self.__class__.__name__,self.msg)

class NoDataExc(NoData):
	"""Class for not finding results"""
	msg = None
	def __init__(self, msg):
		self.msg = msg
	def __str__(self):
		return "{}: {}".format(self.__class__.__name__,self.msg)
	def __repr__(self):
		return "<{}: {}>".format(self.__class__.__name__,self.msg)

ManyData = (ManyDataExc,)+ManyDataExc.__bases__
NoData = (NoDataExc,)+NoDataExc.__bases__

class _QueryProperty(object):
	"""copy from flask_sqlalchemy's code, but filters .deleted"""
	def __init__(self, sa,filtered=False):
		self.sa = sa
		self.filtered = filtered

	def __get__(self, obj, type):
		try:
			mapper = class_mapper(type)
			if mapper:
				q = type.query_class(mapper, session=self.sa.session())
				if self.filtered:
					q = q.filter_by(deleted=False)
					# This would require some extensive cache clearing
					#if cache.regions:
					#	q = q.options(FromCache())
				return q
		except UnmappedClassError:
			return None

class BaseSession(_SignallingSession):
	"""Ignore recursive calls to flush()"""
	def flush(self, *a,**k):
		if self._flushing:
			return
		try:
			self._flushing = True
			done = IdentitySet()
			while True:
				todo = self.new-done
				if not todo:
					break
				for obj in todo:
					obj.before_insert()
					done.add(obj)
		finally:
			self._flushing = False
		super(BaseSession,self).flush(*a,**k)
		for obj in done:
			obj.after_insert()

class SQLAlchemy(BaseSQLAlchemy):
	Column = BaseColumn

	def make_declarative_base(self):
		"""Creates the declarative base."""
		base = declarative_base(cls=BaseModel, name=str('Model'), metaclass=_BoundDeclarativeMeta)
		base.qq = _QueryProperty(self,filtered=False)
		base.q = _QueryProperty(self,filtered=True)
		return base

	def apply_driver_hacks(self,app,info,options):
		options.setdefault('pool_recycle',255)
		if config.TRACE:
			options.setdefault('echo',True)
		super(SQLAlchemy,self).apply_driver_hacks(app,info,options)

	def create_scoped_session(self, options=None):
		"""Helper factory method that creates a scoped session."""
		if options is None:
			options = {}
		scopefunc=options.pop('scopefunc', None)
		return scoped_session(
			partial(BaseSession, self, **options), scopefunc=scopefunc
		)

class IDrenderer(IntegerFieldRenderer):
	"""A renderer which, when readonly, returns a URL pointing at the admin page"""
	
	def render_readonly(self,**kwargs):
		## this is fragile (it uses _property), but I don't see how else to get to the mapper
		try:
			return Markup('<a href="%s">%s</a>') % (url_for('admin.show', table=self.field._property.parent.local_table.name, id=self.value), super(IDrenderer,self).render_readonly(**kwargs))
		### + helpers.hidden_field(self.name, value=self.value, **kwargs)
		except Exception as e:
			return self.value

class Query(CachingQuery):
	"""\
		A query which provides `get` and `get_by` methods.

		These work like `filter` and `filter_by`, respectively, but
		expect exactly one row to be returned, otherwise they'll throw
		`NoData` / `ManyData` exceptions.
		"""
	def get(self,*a,**k):
		return self.filter(*a,**k).one()
		#return self._one(self.filter(*a,**k))
	def get_by(self,**k):
		return self.filter_by(**k).one()
		#return self._one(self.filter_by(**k))

	def one(self):
		"""A re-implementation of one() which can be breakpointed, to aid in debugging"""
		res = None
		for obj in self:
			if res is None:
				res = obj
			else:
				res = ManyDataExc
		if res is None:
			raise NoDataExc(self)
		elif res is ManyDataExc:
			raise ManyDataExc(self)
		else:
			return  res

	def cached(self, *key):
		return self.options(FromCache(cache_key=keystr(key)))

class JSON(TypeDecorator):
	"""Represents any Python object as a json-encoded string.
	"""
	impl = VARCHAR(LEN_JSON)

	def process_bind_param(self, value, dialect):
		if value is not None:
			value = json.encode(value)
		return value

	def process_result_value(self, value, dialect):
		if value is not None:
			value = json.decode(value)
		return value

def no_autoflush(fn):
	"""\
		Decorator to prevent database auto-flushing when the code
		thus decorated does database queries.

			@no_autoflush
			def check_if_new_record_is_ok(data):
				…

		"""
	@wraps(fn)
	def go(*args, **kw):
		autoflush = db.session.autoflush
		db.session.autoflush = False
		try:
			return fn(*args, **kw)
		finally:
			db.session.autoflush = autoflush

	return go

#def limitedQuery(mapper,session):
#	return session.query(mapper)

#	q = LimitQuery(mapper,*a,**k)
#	if hasattr(g,'user') and not g.user.superuser:
#		q = mapper.class_._q(q)
#	return q

def call_event(cls,method,code=None):
	"""\
		A helper which registers callbacks to `method` on `cls`
		"""
	if code is None:
		code = method
	def helper(mapper,connection,obj):
		getattr(obj,method)()
	event.listen(cls,code, helper)
		
def setup_events(cls):
	"""\
		Add (some of) the standard event listeners.

		Others are called in the flush() wrapper because the event code
		does that too late.
		"""
	call_event(cls,"before_update")
	call_event(cls,"after_update")
	@event.listens_for(cls, 'load')
	def receive_load(target, context):
		target.after_load()

class Dumpable(object):
	"""\
		A mix-in which declares a dict-like property that contains the
		actual object data.
		"""
	def _dump(self, add_none=False, cols=None):
		"""\
			Override with read-only one-to-many links
			"""
		return self._as_dict(add_none,cols)

	def _dump_attrs(self):
		"""Returns the set of names of attributes which should be included in a dump"""
		i = inspect(self)
		res = set()
		for k in i.attrs.keys():
			if k.startswith('_'):
				continue
			if k.endswith('_typ_id'):
				continue
			if k.endswith('_id'):
				k = k[:-3]
			res.add(k)
		return res
		
	def _as_dict(self, add_none=False, cols=None):
		"""\
			Override with extra settable properties

			:param add_none: Include keys whose value is None.
			:param cols: The list of columns to be dumped.
			             The default is `self.dump_attrs()`.
			"""
		if cols is None:
			cols = self._dump_attrs()
		res = {}
		for k in cols:
			v = getattr(self,k)
			if add_none or v is not None:
				res[k] = v
		return res

	@property
	def as_dict(self):
		return self._as_dict()

class BaseModel(Dumpable):
	"""\
		Base object for the system's tables; sets table name and adds ID column automagically

		Initialization of a new object proceeds in steps:
			* From a form, __init__() is called
			  - the form or whatever is responsible for adding the object to the database
			* From code, class_.new() is used
			  - new() will do the add-to-the-database step itself
			* .before_insert() will run automatically
			  - similarly, before an update, .before_update()
			  - use these to verify multi-table consistency etc.
			* .after_insert()/update() will run automatically
			  - dito .after_update()
			  - use these to insert additional tracking, permissions, or whatever
			* .after_load() will run after a record has been loaded from the database

		"""
	
	query_class = Query

	@declared_attr
	def __tablename__(cls):
		return cls.__name__.lower()
	
	@classmethod
	def __declare_last__(cls):
		setup_events(cls)
		try:
			super(BaseModel,cls).__declare_last__()
		except AttributeError:
			pass

	id = _BaseColumn(Integer, primary_key=True, label="ID", renderer=IDrenderer)
	deleted = _BaseColumn(Boolean, nullable=False, default=False)

	# canonical representation
	@property
	def _name(self):
		if hasattr(self,'name'):
			return self.name
		return "#"+str(self.id)
	def __repr__(self):
		if self.id is None:
			return "<%s:? %s>" % (self.__class__.__name__, self._name)
		return "<%s:%d %s>" % (self.__class__.__name__,self.id, self._name)
	def __str__(self):
		return "%s" % (self._name)
	def __html__(self):
		#return '<a href="%s">%s</a>' % (url_for('admin.show', table=self.__class__.__name__.lower(), id=self.id), escape(self._name))
		return escape(self._name)+'_'+text_type(self.id)

	def __init__(self, _new=False, **kw):
		"""\
			Basic record initialization.

			Do not call directly.
			"""
		if getattr(g,'naked_new',False):
			raise RuntimeError("Either use ‘.new’, or wrap your code with ‘with external_input:’")
		for k,v in kw.items():
			setattr(self,k,v)

	def __getstate__(self):
		"""\
			Returns the state which should be included in a pickle. Used for caching.
			Basically, use everything but lazy-loaded relationships.
			"""
		res = {}
		i = inspect(self)
		for p in i.mapper.iterate_properties:
			if p.is_property and getattr(p,'lazy',False) in (False,'joined'):
				res[p.key] = getattr(self,p.key)
		res['_sa_instance_state'] = self._sa_instance_state
		return res
		
	@classmethod
	@no_autoflush
	def new(cls,*a,**kw):
		"""\
			Add a new record. Override `setup` instead of this method.

			Usage:
				new_user = User.new(username="fred_flintstone")
				# do not use User(username="fred_flintstone")
				# that's reserved for form and REST handling
			"""
		with new_protect():
			self = cls()
		self.setup(*a,**kw)
		db.session.add(self)
		db.session.flush()
		return self

	def setup(self):
		"""\
			Fill a newly-created record.

			If you override this, consume any parameters you accept and
			pass the rest of the keywords along.

			This code sets `superparent` if it is not set, so that the new
			record is not marked as deleted.

			Do not add any other dependent database entries here: 
			this record does not yet have an ID. Use after_insert() for that.
			"""
		pass

	def before_insert(self):
		"""\
			Called after finalizing the object but before writing to the database.
			"""
		pass

	def after_insert(self):
		"""Called after inserting into the database; the ID is valid"""
		pass

	def after_load(self):
		"""Called after loading a record from the database"""
		pass

	def before_update(self):
		"""Called after finalizing the object but before updating the database"""
		pass

	def after_update(self):
		"""Called after writing to the database"""
		pass

class new_protect(object):
	"""\
		This is a ‘with’ wrapper to allow instantiation of an
		object without calling "new" on it, which does all kinds of input
		checks.
		"""
	def __enter__(self):
		self.naked_new = getattr(g,'naked_new',False)
		g.naked_new = True
	def __exit__(self, a,b,c):
		g.naked_new = self.naked_new

def init_db(app):
	db.init_app(app)
	migrate = Migrate(app, db)

#	@app.teardown_request
#	def shutdown_session(exception=None):
#		if exception:
#			db.rollback()
#		else:
#			db.session.commit()
#		db.close()

def refresh(obj, force=False):
	"""\
		Return a current copy of my argument, if that is necessary.
		"""
	i = inspect(obj)
	if i.expired or (not i.persistent and i.identity and i.identity[0]):
		s = db.session()
		if s._flushing or force:
			obj = i.class_.q.get_by(id=i.identity[0])
		else:
			obj = s.merge(obj, load=False)
	return obj

def maybe_stale(fn):
	"""\
		Decorator which refreshes its target's first argument.
		"""
	@wraps(fn)
	def refresh_first(self, *args, **kw):
		self = refresh(self)
		return fn(self, *args, **kw)

	return refresh_first
	
def check_unique(cls, *vars):
	"""\
		This is a before-insert/update verifier which tests for uniqueness
		across tables. A database-based constraint is not possible because 
		parent pointers are in a different table.

		Usage:

			class SomeObj(Object):
				name = ...
			check_unique(SomeObj,"name parent")
			# check_unique(SomeObj,"name","parent") ## same thing

		This verifier ignores deleted objects and understands "default"
		(there may be only one) and "inherit" (either True+False or None)
		fields.

		TODO: Add replacing behavior if possible.
		"""
	if len(vars) == 1:
		vars = vars[0].split(" ")
	assert vars

	k = '_pybble_unique_'+'_'.join(vars)
	if getattr(cls,k,False):
		return
	setattr(cls,k,True)

	@no_autoflush
	def check(mapper, connection, obj):
		if obj.deleted:
			return
		q = []
		for v in vars:
			if v == "inherit":
				if obj.inherit is not None:
					q.append(or_(cls.inherit == None, cls.inherit == obj.inherit))
			elif v == "default":
				if not obj.default:
					return
				q.append(cls.default == True)
			else:
				q.append(getattr(cls,v)==getattr(obj,v))
		if obj.id is not None:
			q.append(cls.id != obj.id)
		q.append(cls.id != None)
		if cls.q.filter(*q).count() > 0:
			raise ManyDataExc("Duplicate:{}:{} = {}".format(",".join(vars), str(obj), str(list(cls.q.filter(*q).all()))))
	event.listen(cls,"before_insert",check)
	event.listen(cls,"before_update",check)

class _block_updates(object):
	def __init__(self, cls=None):
		self.cls = cls
	def __call__(self, target, value, oldvalue, initiator):
		if oldvalue not in (None,NO_VALUE,NEVER_SET,value) and not target._deleting and (self.cls is None or isinstance(oldvalue,self.cls)):
			raise RuntimeError("You cannot change {}.{} (‘{}’ to ‘{}’)".format(target,initiator.parent_token.key,oldvalue,value))

def no_update(var,cls=None):
	k = '_pybble_block_'+var.key
	if getattr(var.class_,k,False):
		return
	setattr(var.class_,k,True)
	event.listen(var, 'set', _block_updates(cls))

db = SQLAlchemy()

