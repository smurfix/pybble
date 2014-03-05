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

from __future__ import print_function,absolute_import
import sys
from time import mktime
from json.encoder import JSONEncoder
from json.decoder import JSONDecoder
import datetime as dt
from flask import current_app

##
## This code is used to package some objects into JSON which usually don't.
##

type2cls = {}
name2cls = {}
def _reg(cls):
	type2cls[cls.cls.__name__] = cls
	name2cls[cls.clsname] = cls
	return cls

@_reg
class _datetime(object):
	cls = dt.datetime
	clsname = "datetime"

	@staticmethod
	def encode(obj):
		## the string is purely for human consumption and therefore does not have a time zone
		return {"t":mktime(obj.timetuple()),"s":obj.strftime('%Y-%m-%d %H:%M:%S')}

	@staticmethod
	def decode(t=None,s=None):
		return dt.datetime.utcfromtimestamp(t).replace(tzinfo=UTC).astimezone(TZ)

@_reg
class _timedelta(object):
	cls = dt.timedelta
	clsname = "timedelta"

	@staticmethod
	def encode(obj):
		## the string is purely for human consumption and therefore does not have a time zone
		return {"t":obj.total_seconds(),"s":"%d.%d.%d" % (obj.days,obj.seconds,obj.microseconds)}

	@staticmethod
	def decode(t=None,s=None):
		return dt.timedelta(0,t)

@_reg
class _date(object):
	cls = dt.date
	clsname = "date"

	@staticmethod
	def encode(obj):
		return {"d":obj.toordinal(), "s":obj.strftime("%Y-%m-%d")}

	@staticmethod
	def decode(d=None,s=None):
		return dt.date.fromordinal(d)

@_reg
class _time(object):
	cls = dt.time
	clsname = "time"

	@staticmethod
	def encode(obj):
		ou = obj.replace(tzinfo=UTC)
		secs = ou.hour*3600+ou.minute*60+ou.second
		return {"t":secs,"s":"%02d:%02d:%02d" % (ou.hour,ou.minute,ou.second)}

	@staticmethod
	def decode(t=None,s=None):
		return dt.datetime.utcfromtimestamp(t).time()

def rec_encode(obj):
	if isinstance(obj,(tuple,list)):
		return [rec_encode(x) for x in obj]
	elif isinstance(obj,dict):
		res = {}
		for k,v in obj.items():
			res[k] = rec_encode(v)
		return res
	else:
		enc = type2cls.get(obj.__class__.__name__,None)
		if enc is not None:
			obj = enc.encode(obj)
			obj["_o"] = enc.clsname
		return obj

class Encoder(JSONEncoder):
	def __init__(self,tablespace,main=()):
		super(Encoder,self).__init__(skipkeys=False, ensure_ascii=False,
			check_circular=False, allow_nan=False, sort_keys=False,
			indent=(2 if current_app.config.DEBUG else None),
			separators=((', ', ': ') if current_app.config.DEBUG else (',', ':')),
			encoding='utf-8')

	def default(self, data):
		obj = type2cls.get(data.__class__.__name__,None)
		if obj is not None:
			data = obj.encode(data)
			data["_o"] = obj.clsname
			return data

		return super(Encoder,self).default(data)

def encode(data,tablespace=None):
	return Encoder().encode(data)

##
## Decoding part
##

def rec_decode(obj):
	if isinstance(obj,(tuple,list)):
		return [rec_decode(x) for x in obj]
	elif not isinstance(obj,dict):
		return obj
	else:
		ev = obj.pop('_o',None)
		if ev is not None:
			return name2cls[ev].decode(**obj)

		res = {}
		for k,v in obj.items():
			res[k] = rec_decode(v)
		return res

class Decoder(JSONDecoder):
	def __init__(self):
		super(Decoder,self).__init__(object_hook=self.hook)

	def hook(self,data):
		if not isinstance(data,dict):
			return data

		ev = data.pop('_o',None)
		if ev is not None:
			return name2cls[ev].decode(**data)

		return data
	
def decode(data, proxy=None, p1=None):
	d = Decoder()
	if p1:
		d.objcache[1] = p1
	return d.decode(data)
