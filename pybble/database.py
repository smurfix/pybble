# -*- coding: utf-8 -*-

import os
import sys
from pybble import _settings as settings

from types import ModuleType, FunctionType
from werkzeug import cached_property
from pybble.utils import local_manager
from storm.locals import create_database, And

if settings.DATABASE_TYPE == "sqlite":
	dsn = 'sqlite:///'+settings.DATABASE_FILE
elif settings.DATABASE_TYPE == "mysql":
	dsn = 'mysql://%s:%s@%s/%s?charset=utf8' % (
    settings.DATABASE_USER, settings.DATABASE_PASSWORD,
    settings.DATABASE_HOST, settings.DATABASE_NAME)
else:
	raise ValueError("unsupported ddatabase type: use 'sqlite' or 'mysql'")

database = create_database(dsn)

from storm.exceptions import NotOneError as NonUniqueResult
from storm.exceptions import StormError

class NoResult(StormError):
	pass

def _Get(cls, id):
	res = db.store.get(cls, id)
	if res is None:
		raise NoResult
	return res

def _ArgsList(cls,kw):
	args = []
	for k,v in kw.iteritems():
		try:
			w = (getattr(cls,k) == v)
		except TypeError:
			raise TypeError("Comp: %r.%s = %r" % (cls,k,v))
		if isinstance(w,bool):
			w = (getattr(cls,k+"_id") == (v.id if v else None))
		args.append(w)
	return args

def _GetBy(cls, **kw):
	args = _ArgsList(cls,kw)
	res = None
	for r in db.store.find(cls, And(*args)):
		if res is None:
			res = r
		else:
			raise NonUniqueResult()
	if res is None:
		raise NoResult
	return res

def _Filter(cls, *args, **kw):
	return db.store.find(cls, And(*args), **kw)

def _FilterBy(cls, **kw):
	args = _ArgsList(cls,kw)
	if not args:
		return db.store.find(cls)
	return db.store.find(cls, And(*args))

#	res = 0
#	for r in db.store.find(cls, *args):
#		yield r
#		res += 1
#	if not res:
#		raise NoResult

from pybble.utils import store

def _make_module():
    db = ModuleType('db')
    db.store = store
    db.get_one = _Get
    db.filter = _Filter
    db.get_by = _GetBy
    db.filter_by = _FilterBy
    return db

db = _make_module()

