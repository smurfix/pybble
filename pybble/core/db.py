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

from functools import update_wrapper

from sqlalchemy import create_engine, Integer, types, util, exc as sa_exc, event, or_, Boolean
from sqlalchemy.orm import scoped_session, sessionmaker,query
from sqlalchemy.inspection import inspect
from sqlalchemy.orm.session import Session
from sqlalchemy.orm.base import NO_VALUE,NEVER_SET
from sqlalchemy.orm.attributes import instance_state
from sqlalchemy.orm.exc import NoResultFound as NoData, MultipleResultsFound
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.pool import AssertionPool
from sqlalchemy.types import TypeDecorator, VARCHAR
from sqlalchemy.util import IdentitySet

from formalchemy import Column, helpers
from formalchemy.fields import IntegerFieldRenderer

from flask import Markup, url_for, escape, g, request
from flask._compat import implements_to_string as py2_unicode, text_type
from flask.ext.migrate import Migrate

from . import json
from .models import LEN_JSON

import logging
logger = logging.getLogger('pybble.core.db')

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

from . import config
#from zuko.db.logger import logged_session

def db_engine(**kw):
	kw.setdefault('pool_recycle',255)
	kw.setdefault('uri',config.sql_uri)
	if config.TRACE:
		kw.setdefault('echo',True)
		kw.setdefault('poolclass',AssertionPool)
	uri = kw.pop('uri')
	if uri.startswith("mysql"):
		uri += "?charset=utf8"
	return create_engine(uri, **kw)
engine = db_engine()

# don't keep database connections open for more than 5min

class PybbleSession(Session):
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
		super(PybbleSession,self).flush(*a,**k)
		for obj in done:
			obj.after_insert()
#
#	def merge(self,obj):
#		if self._flushing:
#			return obj
#		s = instance_state(obj)
#		if not s.expired:
#			return obj
#		return super(PybbleSession,self).merge(obj)

db = scoped_session(sessionmaker(autocommit=False,
                                 class_=PybbleSession,
                                 #autoflush=False,
                                 bind=engine))

class IDrenderer(IntegerFieldRenderer):
	"""A renderer which, when readonly, returns a URL pointing at the admin page"""
	
	def render_readonly(self,**kwargs):
		## this is fragile (it uses _property), but I don't see how else to get to the mapper
		try:
			return Markup('<a href="%s">%s</a>') % (url_for('admin.show', table=self.field._property.parent.local_table.name, id=self.value), super(IDrenderer,self).render_readonly(**kwargs))
		### + helpers.hidden_field(self.name, value=self.value, **kwargs)
		except Exception as e:
			return self.value

class GetQuery(query.Query):
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

def not_deleted(*a,**k):
	q = GetQuery(*a,**k)
	return q.filter_by(deleted=False)

def no_autoflush(fn):
	"""\
		Decorator to prevent database auto-flushing when the code
		thus decorated does database queries.

			@no_autoflush
			def check_if_new_record_is_ok(data):
				…

		"""
	def go(*args, **kw):
		autoflush = db.autoflush
		db.autoflush = False
		try:
			return fn(*args, **kw)
		finally:
			db.autoflush = autoflush

	return update_wrapper(go, fn)

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
		for k in i.dict.keys():
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

class _Base(Dumpable):
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
	@declared_attr
	def __tablename__(cls):
		return cls.__name__.lower()
	
	@classmethod
	def __declare_last__(cls):
		setup_events(cls)
		try:
			super(_Base,cls).__declare_last__()
		except AttributeError:
			pass

	id = Column(Integer, primary_key=True, label="ID", renderer=IDrenderer)
	deleted = Column(Boolean, nullable=False, default=False)

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
		self.add_db()
		return self

	def add_db(self):
		"""\
			Add this record to the database.
			"""
		db.add(self)
		db.flush()

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

	q = db.query_property(query_cls=not_deleted)

Base = declarative_base(cls=_Base)
Base.super_readonly = False
#logged_session(db,Base)


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
	migrate = Migrate(app, db)

	@app.teardown_request
	def shutdown_session(exception=None):
		if exception:
			db.rollback()
		else:
			db.commit()
		db.close()

def refresh(obj):
	"""\
		Return a current copy of my argument, if that is necessary.
		"""
	i = inspect(obj)
	if i.expired:
		obj = i.class_.q.get_by(id=i.identity[0])
	return obj

def maybe_stale(fn):
	"""\
		Decorator which refreshes its target's first argument.
		"""
	def refresh_first(self, *args, **kw):
		self = refresh(self)
		return fn(self, *args, **kw)

	return update_wrapper(refresh_first, fn)
	
@no_autoflush
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

	def check(mapper, connection, obj):
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

def _block_updates(target, value, oldvalue, initiator):
	if oldvalue not in (None,NO_VALUE,NEVER_SET,value) and not target._deleting:
		raise RuntimeError("You cannot change {}.{} (‘{}’ to ‘{}’)".format(target,initiator.parent_token.key,oldvalue,value))

def no_update(var):
	k = '_pybble_block_'+var.key
	if getattr(var.class_,k,False):
		return
	setattr(var.class_,k,True)
	event.listen(var, 'set', _block_updates)

