# -*- coding: utf-8 -*-

import os
import sys
import settings

from types import ModuleType, FunctionType
from werkzeug import cached_property
from sqlalchemy import MetaData, create_engine, Table, String, Boolean,\
    Integer, Column, Text, Float, ForeignKey, DateTime
from sqlalchemy.types import TypeDecorator, MutableType
from sqlalchemy.orm import scoped_session, create_session, relation, Query, \
    MapperExtension, scoped_session
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta
from pybble.utils import local_manager

if settings.DATABASE_TYPE == "sqlite":
	dsn = 'sqlite:///'+settings.DATABASE_FILE
elif settings.DATABASE_TYPE == "mysql":
	dsn = 'mysql://%s:%s@%s/%s?charset=utf8' % (
    settings.DATABASE_USER, settings.DATABASE_PASSWORD,
    settings.DATABASE_HOST, settings.DATABASE_NAME)
else:
	raise ValueError("unsupported ddatabase type: use 'sqlite' or 'mysql'")

from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

Session = scoped_session(lambda: create_session(db.engine,
                         autocommit=False), local_manager.get_ident)

engine = create_engine(dsn, pool_recycle=300, convert_unicode=True, echo=settings.DATABASE_DEBUG)
metadata = Base.metadata

Model = declarative_base(metadata=metadata,
                         mapper=Session.mapper)
#Model.query = session.query_property()

from sqlalchemy.orm import exc as orm_exc

NonUniqueResult = orm_exc.MultipleResultsFound
NoResult = orm_exc.NoResultFound

class GQuery(Query):
	def get_by(self,*a,**k):
		"""Make sure that there's exactly one result."""
		try:
			return self.filter_by(*a,**k).one()
		except NoResult:
			print >>sys.stderr,"Inputs: %s %s" % (repr(a),repr(k))
			raise
		
	def get_one(self,*a,**k):
		"""Make sure that there's exactly one result."""
		return self.filter(*a,**k).one()

def _make_module():
    import sqlalchemy
    from sqlalchemy import orm

    db = ModuleType('db')
    for mod in sqlalchemy, orm:
        for key in mod.__all__:
            setattr(db, key, getattr(mod, key))
    #db.File = File
    db.engine = engine
    db.session = Session
    db.Model = Model
    db.Query = GQuery
    db.Base = Base
    db.Metadata = metadata
    return db

db = _make_module()
del _make_module

