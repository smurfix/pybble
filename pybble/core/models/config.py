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

import logging
import datetime
import random
import os

from flask import url_for, current_app, g
from flask.config import Config
from flask._compat import string_types,text_type

from .. import json, config
from ..utils import attrdict
from ..db import db, Base, Column, NoData, check_unique,no_update
from ..signal import ConfigChanged
from . import ObjectRef
from ._descr import D

from datetime import datetime,timedelta

from sqlalchemy import Integer, Unicode, DateTime, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship,backref
from sqlalchemy.types import TypeDecorator, VARCHAR

#from flask.ext.misaka import markdown
#
#from quokka.core import TEXT_FORMATS
#from quokka.core.fields import MultipleObjectsReturned
#from quokka.modules.accounts.models import User
#from quokka.utils.text import slugify
#from quokka.utils import get_current_user
#
#from .admin.utils import _l

logger = logging.getLogger()

## ConfigDict

class ConfigDict(Config,attrdict):
	_parent = None
	_set_db = None
	_defaults = None
	def __init__(self,parent=None):
		self._parent = parent
		self._vars = {}
		self._loads = []
		if parent:
			parent.signal.connect(self._reload, sender=ConfigChanged)
		
	def _load(self, parent=None, force=False, recurse=None, vars=None, name=None):
		"""\
			Load variable data.

			:param force: Overwrite existing values
			:param recurse: Recursively check parent objects.
				Infinite loops are protected against.
			:param vars: If the variable definitions are the children of
			    self.superparent instead of self, set this to "superparent".
				TODO: use an attrgetter function instead.
			:param name: (re)load only this variable

			This code remembers what you load, so that a .reload() will
			pull the same (kind of) data.
			"""

		self._loads.append(dict(recurse=recurse,vars=vars))
		if self._parent is not None:
			assert parent is None or parent is self._parent
		else:
			self._parent = parent
		self._load1(recurse=recurse,vars=vars, name=name)

	def _reload(self, sender=None, name=None):
		"""\
			Reload variable data from the database, after something
			was changed.
			"""
		for k in list(self.keys()) if name is None else (name,):
			super(ConfigDict,self).__delitem__(k)
		for kw in self._loads:
			self._load1(name=name, **kw)

	def _load1(self, force=False, recurse=None, vars=None, name=None):
		if vars is not None and vars == "GLOBALS":
			# Special hack to include the globals, esp. when reloading
			if name is None:
				for k,v in config.items():
					super(ConfigDict,self).__setitem__(k,v)
			elif name in config:
				super(ConfigDict,self).__setitem__(name,config[name])
			return

		s = db.merge(self._parent)
		seen = set()
		if recurse is True:
			recurse = "parent"
		while s:
			if s.id in seen: break
			seen.add(s.id)

			vf = SiteConfigVar.q.filter_by(parent=s)
			if name is not None:
				vf = vf.join(ConfigVar, SiteConfigVar.var).filter(ConfigVar.name==name)
			for v in vf:
				if force:
					if v.var.name not in seen:
						self[v.var.name] = v.value
						seen.add(v.var.name)
				else:
					self.setdefault(v.var.name, v.value)
			vf = ConfigVar.q.filter_by(parent=(getattr(s,vars) if vars else s))
			if name is not None:
				vf = vf.filter_by(name=name)
			for v in vf:
				self.setdefault(v.name, v.value)
				self._vars.setdefault(v.name,v)

			if recurse:
				s = getattr(s,recurse)
			else:
				break
		if self._parent:
			self._set_db = True
	
	def __setitem__(self,k,v):
		s = self._parent
		if isinstance(k,string_types):
			k = text_type(k)
		if self._set_db:
			cfv = self._vars[k]
			assert self._parent
			try:
				cf = SiteConfigVar.q.get_by(parent=self._parent, var=cfv)
			except NoData:
				cf = SiteConfigVar(parent=self._parent, var=cfv, value=v)
			else:
				cf.value=v
			db.flush()
		super(ConfigDict,self).__setitem__(k,v)

		if self._parent is not None:
			self._parent.signal.send(ConfigChanged, name=k)

	def __delitem__(self,k):
		cfv = self._vars.get(k,None)
		if self._set_db:
			assert self._parent and cfv
			try:
				cf = SiteConfigVar.q.get_by(parent=self._parent, var=cfv)
			except NoData:
				pass
			else:
				db.delete(cf)
			db.flush()
		if cfv is not None:
			super(ConfigDict,self).__setitem__(k,cfv.value)
		else:
			super(ConfigDict,self).__delitem__(k)

		if self._parent is not None:
			self._parent.signal.send(ConfigChanged, name=k)
	
	def _disarm(self):
		self._set_db = False
	def _arm(self):
		self._set_db = True

## JSON type

class JSON(TypeDecorator):
	"""Represents any Python object as a json-encoded string.
	"""
	impl = VARCHAR(100000)

	def process_bind_param(self, value, dialect):
		if value is not None:
			value = json.encode(value)
		return value

	def process_result_value(self, value, dialect):
		if value is not None:
			value = json.decode(value)
		return value

class JsonValue(object):
	value = Column(JSON)

## ConfigVar

class ConfigVar(ObjectRef, JsonValue):
	"""Describes one configuration variable."""
	_descr = D.ConfigVar

	@classmethod
	def __declare_last__(cls):
		check_unique(cls,"parent name")
		no_update(cls.name)
		no_update(cls.parent)

	# Parent: the object this setting is known at

	name = Column(Unicode(30), index=True)
	doc = Column(Unicode(1000))
	# TODO: make sure that (name,parent_id) is unique

	def __init__(self, parent, name,value, **kw):
		## cannot have a uniqueness constraint across inherited tables
		super(ConfigVar,self).__init__(**kw)
		self.parent = parent
		self.name = name
		self.value = value

	@staticmethod
	def get(parent,name):
		try:
			return ConfigVar.q.get_by(parent=parent, name=name)
		except NoData:
			raise NoData("ConfigVar:"+name)

	@staticmethod
	def exists(parent,name,doc=None,default=None):
		try:
			return ConfigVar.get(parent,name)
		except NoData:
			return ConfigVar(parent=parent, name=name,doc=doc,value=default)

	@property
	def as_str(self):
		return u"%s=%s @%s" % (self.name,repr(self.value),self.parent.name)

## SiteConfigVar

class SiteConfigVar(ObjectRef, JsonValue):
	"""This is one configuration variable's value for a site (or some other object, in fact)."""
	_descr = D.SiteConfigVar

	@classmethod
	def __declare_last__(cls):
		if not hasattr(cls,'var'):
			cls.var = cls.superparent
		check_unique(cls,"parent var")
		no_update(cls.name)
		no_update(cls.parent)
	# Owner: the user who last set the variable

	def __init__(self,parent,var=None,superparent=None,**kw):
		# assert that exactly one of var or superparent is set
		if var is None:
			var = superparent
		else:
			assert superparent is None
		assert var is not None

		super(SiteConfigVar,self).__init__(var=var,parent=parent,**kw)

	@property
	def as_str(self):
		if self.var is None or self.parent is None:
			return "‽"
		return u"%s=%s @%s" % (self.var.name,repr(self.value),self.parent.name)


