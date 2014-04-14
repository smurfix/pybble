#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, division
##
## This is part of Pybble, a WMS (Whatever Management System) based on
## Jinja2/Haml, Werkzeug, Flask, and Optimism.
##
## Pybble is Copyright © 2014 by Matthias Urlichs <matthias@urlichs.de>,
## it is licensed under the GPLv3. See the file `README.md` for details
## as well as hopeful statements by the author.
##
## This paragraph is auto-generated and may self-destruct at any time.
## Please do not remove the next line, or insert any blank lines before it.
##BP

from sqlalchemy import create_engine, Integer, types, util, exc as sa_exc
from sqlalchemy.orm import scoped_session, sessionmaker,query
from sqlalchemy.orm.exc import NoResultFound as NoData, MultipleResultsFound as ManyData
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from formalchemy import Column, helpers
from formalchemy.fields import IntegerFieldRenderer
from flask import Markup, url_for, escape, g
from flask._compat import implements_to_string as py2_unicode

from . import config
#from zuko.db.logger import logged_session

engine = create_engine(config.mysql_uri+'?charset=utf-8', pool_recycle=100)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
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

class LimitQuery(query.Query):
	"""A query which allows limits on GET"""
##	TODO
#	def get(self, ident):
#		if not hasattr(g,'user') or g.user.superuser:
#			return super(LimitQuery,self).get(ident)
#
#		if hasattr(ident, '__composite_values__'):
#		    ident = ident.__composite_values__()
#
#		ident = util.to_list(ident)
#
#		mapper = self._only_full_mapper_zero("get")
#
#		if len(ident) != len(mapper.primary_key):
#		    raise sa_exc.InvalidRequestError(
#		    "Incorrect number of values in identifier to formulate "
#		    "primary key for query.get(); primary key columns are %s" %
#		    ','.join("'%s'" % c for c in mapper.primary_key))
#
#		key = mapper.identity_key_from_primary_key(ident)
#		key = (getattr(key[0],"id") == key[1][0])
#		return self.filter(key).one()

def limitedQuery(mapper,*a,**k):
	q = LimitQuery(mapper,*a,**k)
	if hasattr(g,'user') and not g.user.superuser:
		q = mapper.class_._q(q)
	return q

@py2_unicode
class Base(object):
	"""Base object for the system's tables; sets table name and ID automagically"""
	@declared_attr
	def __tablename__(cls):
		return cls.__name__.lower()
	
	id = Column(Integer, primary_key=True, label="ID", renderer=IDrenderer)

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

	q = db_session.query_property(query_cls=limitedQuery)

Base = declarative_base(cls=Base)
Base.query = db_session.query_property(query_cls=limitedQuery)
Base.super_readonly = False
#logged_session(db_session,Base)

def register(app):
	@app.teardown_request
	def shutdown_session(exception=None):
		if exception:
			db_session.rollback()
		else:
			db_session.commit()
		db_session.close()
