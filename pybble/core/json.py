#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function,absolute_import
import sys
from time import mktime
from json.encoder import JSONEncoder
from json.decoder import JSONDecoder
from . import config
from .utils import attrdict, TZ,UTC, format_dt
from ..utils import NotGiven
import datetime as dt

class SupD(dict):
	def get(self,k,default=NotGiven):
		if hasattr(k,"__mro__"):
			for x in k.__mro__:
				try:
					return self.__getitem__(x.__module__+"."+x.__name__)
				except KeyError:
					pass
		if default is NotGiven:
			raise KeyError(k)
		return default

type2cls = SupD()
name2cls = {}
def json_adapter(cls):
	type2cls[cls.cls.__module__+"."+cls.cls.__name__] = cls
	name2cls[cls.clsname] = cls
	return cls

@json_adapter
class _datetime(object):
	cls = dt.datetime
	clsname = "datetime"

	@staticmethod
	def encode(obj):
		## the string is purely for human consumption and therefore does not have a time zone
		return {"t":mktime(obj.timetuple()),"s":format_dt(obj)}

	@staticmethod
	def decode(t=None,s=None,a=None,k=None,**_):
		if t:
			return dt.datetime.utcfromtimestamp(t).replace(tzinfo=UTC).astimezone(TZ)
		else: ## historic
			assert a
			return dt.datetime(*a).replace(tzinfo=TZ)

@json_adapter
class _timedelta(object):
	cls = dt.timedelta
	clsname = "timedelta"

	@staticmethod
	def encode(obj):
		## the string is purely for human consumption and therefore does not have a time zone
		return {"t":obj.total_seconds(),"s":str(obj)}

	@staticmethod
	def decode(t,s=None,**_):
		return dt.timedelta(0,t)

@json_adapter
class _date(object):
	cls = dt.date
	clsname = "date"

	@staticmethod
	def encode(obj):
		return {"d":obj.toordinal(), "s":obj.strftime("%Y-%m-%d")}

	@staticmethod
	def decode(d=None,s=None,a=None,**_):
		if d:
			return dt.date.fromordinal(d)
		## historic
		return dt.date(*a)

@json_adapter
class _time(object):
	cls = dt.time
	clsname = "time"

	@staticmethod
	def encode(obj):
		ou = obj.replace(tzinfo=UTC)
		secs = ou.hour*3600+ou.minute*60+ou.second
		return {"t":secs,"s":"%02d:%02d:%02d" % (ou.hour,ou.minute,ou.second)}

	@staticmethod
	def decode(t=None,s=None,a=None,k=None,**_):
		if t:
			return dt.datetime.utcfromtimestamp(t).time()
		return dt.time(*a)

class Encoder(JSONEncoder):
	def __init__(self):
		self.objcache = {}
		super(Encoder,self).__init__(skipkeys=False, ensure_ascii=False,
			check_circular=False, allow_nan=False, sort_keys=False,
			indent=(2 if config.DEBUG else None),
			separators=((', ', ': ') if config.DEBUG else (',', ':')),
			encoding='utf-8')

	def default(self, data):
		obj = type2cls.get(data.__class__,None)
		if obj is not None:
			data = obj.encode(data)
			data["_o"] = obj.clsname
			return data
		return super(Encoder,self).default(data)

def encode(data):
	return Encoder().encode(data)

class Decoder(JSONDecoder):
	def __init__(self, proxy):
		self.objcache = {}
		self.proxy = proxy
		super(Decoder,self).__init__(object_hook=self.hook)

	def hook(self,data):
		if not isinstance(data,dict):
			return data

		ev = data.pop('_o',None)
		if ev is not None:
			return name2cls[ev].decode(**data)

		cr = data.pop('_cr',None)
		if cr is None:
			data = attrdict(data)
			return data
		d = self.objcache.get(cr,None)
		if d is None:
			d = self.proxy()
			self.objcache[cr]=d

		try:
			t = data.pop('_table')
			idx = data.pop('_index')
			idx = tuple(tuple(x) for x in idx) # convert from nested list
		except KeyError:
			pass # recursive or whatever
		else:
			d = d._set(t,idx,**data)
			self.objcache[cr] = d
		return d
	
def decode(data, proxy=None, p1=None):
	d = Decoder(proxy)
	if p1:
		d.objcache[1] = p1
	return d.decode(data)
