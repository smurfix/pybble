#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import sys
import time
import datetime as dt

from ..core.utils import format_dt
from ..core.db import NoData

from flask._compat import text_type,string_types

__all__ = ("show","Cache")

def pr(v):
	if isinstance(v,time.struct_time):
		v = time.strftime("%Y-%m-%d %H:%M:%S",v)
	elif isinstance(v,dt.datetime):
		v = format_dt(v)
	elif isinstance(v,string_types):
		v = repr(v)
		if v[0] == 'u':
			v = v[1:]
	else:
		v = text_type(v)
	return v
	
class Cache(object):
	def __init__(self,*a):
		self.d = set()
		for x in a:
			self.d.add(self.id(x))

	def __call__(self,a):
		i = self.id(a)
		if i in self.d:
			return 1
		self.d.add(i)
		return 0

	def check(self,a):
		i = self.id(a)
		if i in self.d:
			return 1
		return 0

	def add(self,a):
		i = self.id(a)
		self.d.add(i)

	def id(self,a):
		if hasattr(a,"_pk"):
			return hash(a.__class__.__name__)+hash(tuple(str(x) for x in a._pk()))
		return hash(str(a))
	
def qref(k,v,t=None,seen=False):
	print(k+pr(v))

def show_(k,v,expand=None,cache=None):
	if k != "":
		k += " "
	if cache is None:
		cache = Cache()
	seen = cache.check(v) # already printed
	if seen:
		expand=None

	if expand is not None:
		if hasattr(v,'_dump'):
			qref(k,v, seen)
			k = " "*len(unicode(k))
			cache.add(v)
			try:
				v = v._dump()
				for kk in sorted(v.keys()):
					if kk in ('id','discr'):
						continue # included in str(), don't clutter the output
					vv = v[kk]
					ned = expand[kk] if expand else None
					show_(k+kk,vv,ned,cache)
			except NoData:
				print(k+"*** NoData ***",v._id)
			return

		if isinstance(v,(list,tuple)):
			i = 0
			for vx in sorted(v):
				i += 1
				ned = expand[str(i)] if expand else None
				show_(k+str(i),vx,ned,cache)
				k = " "*len(unicode(k))
			return
		
		if isinstance(v,dict):
			for kk in sorted(v.keys()):
				vv = v[kk]
				ned = expand[kk] if expand else None
				show_(k+str(kk),vv,ned,cache)
				k = " "*len(unicode(k))
			return

	if isinstance(v,(list,tuple)):
		v = "[%d items]" % len(v)
	elif isinstance(v,dict):
		v = "{%d entries}" % len(v)
	elif v is not None:
		v = pr(v)
	print(k,v, sep="")

class ddict(dict):
	"""a dictionary with default=None instead of KeyError"""
	def __getitem__(self,k):
		r = super(ddict,self).get(k,None)
		if r is None:
			r = super(ddict,self).get("*",None)
		return r

def show(obj, expand="*",cache=None):
	if expand:
		r = ddict()
		for a in expand.split(","):
			rr = r
			for e in a.split("."):
				if e in rr:
					rr = rr[e]
				else:
					rn = rr[e] = ddict()
					rr = rn
		expand = r

	show_("",obj, expand, cache)

