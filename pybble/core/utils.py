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

import gevent.monkey
gevent.monkey.patch_all()

import logging
import sys
import pytz
import locale

import gevent
from gevent.queue import Queue
from signal import SIGINT

locale.setlocale(locale.LC_ALL, "de_DE.UTF-8")
logger = logging.getLogger('zuko.base')

## time zones
UTC = pytz.UTC
with open("/etc/localtime", 'rb') as tzfile:
	TZ = pytz.tzfile.build_tzinfo('local', tzfile)

# Default timeout for the cache.
# An audit watcher auto-clears it aggressively,
# so we can keep a longer ranger here.
TIMEOUT=24*3600*7

class DupKeyError(KeyError):
	"Attributes may only be set once"
	pass

class Dataset(object):
	"""Only for inheritance check, i.e. test if a field references another record"""
	pass

class ddict(dict):
	"""a dictionary with default"""
	def __getitem__(self,k):
		r = super(ddict,self).get(k,None)
		if r is None:
			r = super(ddict,self).get("*",None)
		return r

class itemgetter(object):
	def __init__(self,*items):
		self.items = items
	def __call__(self,x):
		res = []
		for k in self.items:
			for kk in k:
				x = x[kk]
			res.append(x)
		if len(res) == 1:
			res = res[0]
		return res
				

class attrdict(dict):
	def __init__(self,*a,**k):
		super(attrdict,self).__init__(*a,**k)
		self._done = set()

	def __getattr__(self,a):
		return self[a]
	def __setattr__(self,a,b):
		if a.startswith("_"):
			super(attrdict,self).__setattr__(a,b)
		else:
			self[a]=b
	def __setitem__(self,a,b):
		if a in self:
			raise DupKeyError(a)
		super(attrdict,self).__setitem__(a,b)
	def __delattr__(self,a):
		del self[a]
	
	def grab(self,k):
		v = self.get(k,None)
		if v is None:
			return None
		assert k not in self._done
		self._done.add(k)
		return v

	def open_keys(self):
		for k in self.keys():
			if k not in self._done:
				yield k
	
	def _set(self,k,v):
		super(attrdict,self).__setitem__(k,v)

class Main(object):
	_plinker = None
	_sigINT = None
	_main = None
	_stops = []
	_stopping = False

	### Methods you override
	def setup(self):
		"""Override this to initialize everything"""
		pass
	def main(self):
		"""Override this with your main code"""
		raise NotImplementedError("You forgot to override %s.main" % (self.__class__.__name__,))
	def stop(self,task):
		"""Override this if you don't just want a killed task"""
		logger.debug("Killing main task")
		if task:
			task.kill(timeout=5)
	def cleanup(self):
		"""Override this to clean up after yourself. 'task' is the gevent task of the main loop"""
		pass
	
	### Public methods
	def __init__(self):
		self.stops = []

	def run(self):
		"""Start the main loop"""
		try:
			logger.debug("Setting up")
			self._setup()
			logger.debug("Main program starting")
			self._main = gevent.spawn(self.main)
			self._main.join()
		except Exception:
			logger.exception("Main program died")
		else:
			logger.debug("Main program ended")
		finally:
			self._cleanup()
			logger.debug("Cleanup ended")

	def end(self):
		"""Stop the main loop"""
		logger.info("Stop call received.")
		self._cleanup()
		logger.debug("End handler done.")
		
	def register_stop(self,job,*a,**k):
		"""Pass a function for cleanup code"""
		self._stops.insert(0,(job,a,k))
	
	### Internals
	def _setup(self):
		self._sigINT = gevent.signal(SIGINT,self._sigquit)
		self._plinker = gevent.spawn(self._plink)
		self.setup()
		self.register_stop(self.cleanup)

	def _plink(self):
		i=1
		while True:
			gevent.sleep(i)
			#logger.debug("I am running")
			i += 1

	def _sigquit(self):
		logger.info("Signal received, trying to terminate.")
		gevent.spawn(self._cleanup)
	
	def _cleanup(self):
		if self._stopping:
			if self._stopping == gevent.getcurrent():
				try:
					raise RuntimeError()
				except RuntimeError:
					logger.exception("Cleanup entered from cleanup task.")
				return
			else:
				logger.debug("Cleanup entered again.")
		else:
			self._stopping = gevent.spawn(self._real_cleanup)
		self._stopping.join()

	def _real_cleanup(self):
		logger.debug("Cleanup entered.")
		if self._sigINT:
			self._sigINT.cancel()
			self._sigINT = None

		try:
			self.stop(self._main)
		except Exception:
			logger.exception("Cleanup code")
		finally:
			logger.debug("Killing main task again(?)")
			if self._main:
				self._main.kill(timeout=5)

		for j,a,k in self._stops:
			logger.debug("Running %s",j)
			try:
				j(*a,**k)
			except Exception:
				logger.exception("Running %s",j)
			else:
				logger.debug("Running %s",j)

		if self._plinker:
			self._plinker.kill()
			self._plinker = None
		logger.debug("Cleanup done.")

class noURLdebug(object):
	def filter(self,record):
		if record.levelno > logging.INFO:
			return True
		if record.name.startswith("urllib3."):
			return False
		if record.name.startswith("requests.packages.urllib3."):
			return False
		return True

def init_logging():
	logging.basicConfig(stream=sys.stderr,level=logging.DEBUG)
	for h in logging.getLogger().handlers: h.addFilter(noURLdebug())

def format_dt(value, format='%Y-%m-%d %H:%M:%S'):
	try:
		return value.astimezone(TZ).strftime(format)
	except ValueError: ## naïve time: assume UTC
		return value.replace(tzinfo=UTC).astimezone(TZ).strftime(format)

from pprint import PrettyPrinter,_safe_repr
import datetime as _dt
try:
    from cStringIO import StringIO as _StringIO
except ImportError:
    from StringIO import StringIO as _StringIO

class UTFPrinter(PrettyPrinter,object):
	def _format(self, object, *a,**k):
		typ = type(object)
		if hasattr(object,"values"):
			object = dict(object.items())
		return super(UTFPrinter,self)._format(object, *a,**k)

	def format(self, object, context, maxlevels, level):
		typ = type(object)
		if typ is str:
			object = object.decode("utf-8")
		elif typ is _dt.datetime:
			return "DT( %s )"%(format_dt(object),),True,False
		elif typ is not unicode:
			return _safe_repr(object, context, maxlevels, level)

		if "'" in object and '"' not in object:
			closure = '"'
			quotes = {'"': '\\"'}
		else:
			closure = "'"
			quotes = {"'": "\\'"}
		qget = quotes.get
		sio = _StringIO()
		write = sio.write
		for char in object:
			if char.isalpha():
				write(char)
			else:
				write(qget(char, repr(char)[2:-1]))
		return ("%s%s%s" % (closure, sio.getvalue(), closure)), True, False

def pprint(object, stream=None, indent=1, width=80, depth=None):
    """Pretty-print a Python object to a stream [default is sys.stdout]."""
    UTFPrinter(stream=stream, indent=indent, width=width, depth=depth).pprint(object)

def pformat(object, indent=1, width=80, depth=None):
    """Format a Python object into a pretty-printed representation."""
    return UTFPrinter(indent=indent, width=width, depth=depth).pformat(object)

