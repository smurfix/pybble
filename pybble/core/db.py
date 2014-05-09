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

from sqlalchemy import create_engine, Integer, types, util, exc as sa_exc
from sqlalchemy.orm import scoped_session, sessionmaker,query
from sqlalchemy.orm.exc import NoResultFound as NoData, MultipleResultsFound
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base, declared_attr

from formalchemy import Column, helpers
from formalchemy.fields import IntegerFieldRenderer

from flask import Markup, url_for, escape, g
from flask._compat import implements_to_string as py2_unicode

class ManyDataExc(IntegrityError,MultipleResultsFound):
	"""Class for tests of unique constraint violations"""
	pass
ManyData = (ManyDataExc,)+ManyDataExc.__bases__

from . import config
#from zuko.db.logger import logged_session

def db_engine(**kw):
	kw.setdefault('pool_recycle',255)
	kw.setdefault('uri',config.sql_uri)
	if config.TRACE:
		kw.setdefault('echo',True)
	uri = kw.pop('uri')
	if uri.startswith("mysql"):
		uri += "?charset=utf8"
	return create_engine(uri, **kw)
engine = db_engine()

# don't keep database connections open for more than 5min

db = scoped_session(sessionmaker(autocommit=False,
                                 #autoflush=False,
                                 bind=engine))

class IDrenderer(IntegerFieldRenderer):
	"""An integer which, when readonly, displays the record"""
	
	def render_readonly(self,**kwargs):
		## this is fragile (it uses _property), but I don't see how else to get to the mapper
		try:
			return Markup('<a href="%s">%s</a>') % (url_for('admin.show', table=self.field._property.parent.local_table.name, id=self.value), super(IDrenderer,self).render_readonly(**kwargs))
		### + helpers.hidden_field(self.name, value=self.value, **kwargs)
		except Exception as e:
			return self.value

class GetQuery(query.Query):
	"""A query which allows .get and .get_by"""
	def get(self,*a,**k):
		return self.filter(*a,**k).one()
	def get_by(self,**k):
		return self.filter_by(**k).one()

#def limitedQuery(mapper,session):
#	return session.query(mapper)

#	q = LimitQuery(mapper,*a,**k)
#	if hasattr(g,'user') and not g.user.superuser:
#		q = mapper.class_._q(q)
#	return q

@py2_unicode
class Base(object):
	"""Base object for the system's tables; sets table name and ID automagically"""
	@declared_attr
	def __tablename__(cls):
		return cls.__name__.lower()
	
	id = Column(Integer, primary_key=True, label="ID", renderer=IDrenderer)

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
		return '<a href="%s">%s</a>' % (url_for('admin.show', table=self.__class__.__name__.lower(), id=self.id), escape(self._name))

	q = db.query_property(query_cls=GetQuery)

Base = declarative_base(cls=Base)
Base.super_readonly = False
#logged_session(db,Base)

def register(app):
	@app.teardown_request
	def shutdown_session(exception=None):
		if exception:
			db.rollback()
		else:
			db.commit()
		db.close()

def no_autoflush(fn):
	def go(*args, **kw):
		autoflush = db.autoflush
		db.autoflush = False
		try:
			return fn(*args, **kw)
		finally:
			db.autoflush = autoflush

	return update_wrapper(go, fn)

def maybe_stale(fn):
	def go(self, *args, **kw):
		self = db.merge(self)
		return fn(self, *args, **kw)

	return update_wrapper(go, fn)
	
