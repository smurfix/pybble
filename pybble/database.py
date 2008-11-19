import os
import settings

from types import ModuleType, FunctionType
from werkzeug import cached_property
from sqlalchemy import MetaData, create_engine, Table, String, Boolean,\
    Integer, Column, Text, Float, ForeignKey, DateTime
from sqlalchemy.types import TypeDecorator, MutableType
from sqlalchemy.orm import scoped_session, create_session, relation, Query, \
    MapperExtension
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta

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

engine = create_engine(dsn, pool_recycle=300, convert_unicode=True, echo=settings.DATABASE_DEBUG)
metadata = Base.metadata

session = scoped_session(lambda: create_session(engine, autoflush=True))

Model = declarative_base(metadata=metadata,
                         mapper=session.mapper)
Model.query = session.query_property()

class QueryError(RuntimeError):
	def __init__(self,base,*a,**k):
		self.base = base
		self.args = a
		self.kw = k
	def __str__(self):
		return "<%s: %s: %s %s>" % (self.__class__.__name__, str(self.base), str(self.args), str(self.kw))

class NonUniqueResult(QueryError):
	"""There's more than one result to this query."""
	pass
class NoResult(QueryError):
	"""There's no result to this query."""
	pass

class GQuery(Query):
	def get_one(self,*a,**k):
		"""Make sure that there's exactly one result."""
		res = iter(self.filter(*a,**k)[0:2])
		try:
			r = res.next()
		except StopIteration:
			raise NoResult(self,a,k)

		try:
			res.next()
		except StopIteration:
			return r
		else:
			raise NonUniqueResult(self,a,k)
		
		
def _make_module():
    import sqlalchemy
    from sqlalchemy import orm

    db = ModuleType('db')
    for mod in sqlalchemy, orm:
        for key in mod.__all__:
            setattr(db, key, getattr(mod, key))
    #db.File = File
    db.engine = engine
    db.session = session
    db.Model = Model
    db.Query = GQuery
    db.Base = Base
    return db

db = _make_module()
del _make_module
