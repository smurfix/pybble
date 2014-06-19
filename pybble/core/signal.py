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

from blinker import Signal,signal
from .db import db
from weakref import WeakValueDictionary

all_apps = signal("all-apps", doc="""\
					This signal will be triggered whenever something causes
					all apps' state to be invalidated.""")
app_list = signal("app-list", doc="""\
					This signal will be triggered whenever something causes
					the list of applications to change (e.g. create a new app).""")

## Senders
class ObjDeleted:
	"""This item has been deleted"""
class ConfigChanged:
	"""This item's configuration has changed"""
class NewSite:
	"""A new site has been created"""

class ObjSignal(Signal):
	"""A per-object signal which gets deleted when the last listener detaches"""
	## per-class
	_names = {} # frozen while there are registered senders or receivers
	_cached_names = WeakValueDictionary() # guarantee uniqueness

	# Marker for init
	_need_init = True
	def __new__(cls,parent):
		if parent.id is None:
			db.session.flush()
			assert parent.id > 0
		name = str(parent.type_id)+":"+str(parent.id)
		sig = cls._cached_names.get(name,None)
		if sig is None:
			sig = super(ObjSignal, cls).__new__(cls)
			cls._cached_names[name] = sig
			sig.name = name
		return sig

	def __init__(self,parent):
		if self._need_init:
			self._need_init = False
			super(ObjSignal,self).__init__()

	def connect(self,*a,**k):
		self._names[self.name] = self
		try:
			return super(ObjSignal,self).connect(*a,**k)
		finally:
			self.maybe_dispose()
			# usually not, but .connect() might hve raised an exception

	def send(self,*a,**k):
		try:
			return super(ObjSignal,self).send(*a,**k)
		finally:
			self.maybe_dispose()

	def _disconnected(*a,**k):
		super(ObjSignal,self)._disconnected(*a,**k)
		self.maybe_dispose()

	def maybe_dispose(self):
		if not self._by_receiver and not self._by_sender:
			self.dispose()

	def dispose(self):
		self._names.pop(self.name,None)

