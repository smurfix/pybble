#!/usr/bin/python

# This is a small utility to dump pickled state from redis.

from pickle import Unpickler
from pybble.cache import config
from pybble.core.json import encode,json_adapter
from json.decoder import JSONDecoder
from pprint import pprint
from io import StringIO,BytesIO
from . import PrepCommand as Command
from . import Option, Manager

@json_adapter
class _obj(object):
	cls = type
	clsname = 'dummy.type'

	@staticmethod
	def encode(obj):
		return {"m":obj.__module__,'n':obj.__name__}

	@staticmethod
	def decode(a,k,s):
		r = Dummy(a,k)
		r.s = s
		return r

def DummyClass(module,name):
	class Dummy(object):
		s = None
		a = None
		k = None
		l = None
		def __init__(self,a,k=None):
			self.a = a
			self.k = k

		def __call__(self,*a,**k):
			import pdb;pdb.set_trace()
			#self._state = (a,k)
			#return self
			pass

		def __setstate__(self,state):
			self.s = state

		def append(self,x):
			if self.l is None:
				self.l = []
			self.l.append(x)

		def extend(self,x):
			if self.l is None:
				self.l = []
			self.l.extend(x)

	Dummy.__module__ = "dummy."+module
	Dummy.__name__ = name

	@json_adapter
	class _obj(object):
		cls = Dummy
		clsname = 'dummy.'+module+'.'+name

		@staticmethod
		def encode(obj):
			res = {}
			for k in "aksl":
				v = getattr(obj,k,None)
				if v is not None:
					res[k] = v
			return res

		@staticmethod
		def decode(a=None,k=None,s=None,l=None):
			r = Dummy(a,k)
			r.s = s
			r.l = l
			return r

	return Dummy
   
class DummyUnpickler(Unpickler):
	def find_class(self,module,name):
		if module == "datetime":
			return Unpickler.find_class(self,module,name)
		return DummyClass(module,name)

class DumpCache(Command):
	"""Dump whatever is cached"""
	add_help = False

	def __init__(self):
		super(DumpCache,self).__init__()
		self.add_option(Option("--db", dest="db", action="store", required=False, help="use this DB file"))
		self.add_option(Option("key", nargs='?', action="store",help="The key to emit"))

	def run(self, args=(), db=None,key=None, help=False):
		if help:
			self.parser.print_help()
			sys.exit(not help)
		if db is None:
			r = config.regions['default'].backend.client
		else:
			import dbm
			r = dbm.open(db,'r')
		if key is None:
			for k in r.keys() if db else r.keys('*'):
				print(k)
			return
		v = r.get(key)
		print(len(v),repr(v))
		v = BytesIO(v)
		d = DummyUnpickler(v)
		d = d.load()
		d = JSONDecoder().decode(encode(d))
		pprint(d)

class CacheManager(Manager):
	"""Manage web domains (a 'site') and their primary content (the 'app')."""
	def __init__(self):
		super(CacheManager,self).__init__()
		self.add_command("dump", DumpCache())

	def create_app(self, app):
		return app

