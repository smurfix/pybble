#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, division, unicode_literals
##
## This is part of Pybble, a WMS (Whatever Management System) based on
## Jinja2/Haml, Werkzeug, Flask, and Optimism.
##
## Pybble is Copyright © 2009-2014 by Matthias Urlichs <matthias@urlichs.de>,
## it is licensed under the GPLv3. See the file `README.md` for details
## as well as hopeful statements by the author.
##
## This paragraph is auto-generated and may self-destruct at any time.
## Please do not remove the next line, or insert any blank lines before it.
##BP

import logging
import datetime
import random
import os

from blinker import NamedSignal
from flask import url_for, current_app, g
from flask.config import Config
from flask._compat import string_types,text_type

from .. import json, config
from ..utils import attrdict
from ..db import db, Base, Column, NoData
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

## a list of config-change signals, per site name.
_config_changed = {}
def _config_changed_sig(name):
	sig = _config_changed.get(name)
	if sig is None:
		_config_changed[name] = sig = NamedSignal(name)
	return sig
def register_changed(app):
	sig = _config_changed_sig(app.site.name)
	sig.connect(app.read_config)

class ConfigDict(Config,attrdict):
	_parent = None
	_set_db = None
	_defaults = None
	def __init__(self,parent=None):
		self._parent = parent
		self._vars = {}
		
	def _load(self, parent=None, force=False, recurse=None, vars=None, name=None):
		"""\
			Load variable data.

			:param force: Overwrite existing values
			:param recurse: Recursively check parents (or whatever).
				Infinite loops are protected against.
			:param name: (re)load only this variable
			"""

		s = parent or self._parent
		seen = set()
		if recurse is True:
			recurse = "parent"
		while s:
			if s.id in seen: break
			seen.add(s.id)

			for v in SiteConfigVar.q.filter_by(parent=s):
				if force:
					if v.var.name not in seen:
						self[v.var.name] = v.value
						seen.add(v.var.name)
				else:
					self.setdefault(v.var.name, v.value)
			for v in ConfigVar.q.filter_by(parent=(getattr(s,vars) if vars else s)):
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
		super(ConfigDict,self).__setitem__(k,v)
		db.flush()
		if self._set_db and self._parent is not None:
			self._parent.config_changed()

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
		if cfv is not None:
			super(ConfigDict,self).__setitem__(k,cfv.value)
		else:
			super(ConfigDict,self).__delitem__(k)
		db.flush()

		if self._set_db and self._parent is not None:
			self._parent.config_changed()
	
	def _disarm(self):
		self._set_db = False
	def _arm(self):
		self._set_db = True

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

class ConfigVar(ObjectRef, JsonValue):
	"""Describes one configuration variable."""
	_descr = D.ConfigVar

	# Parent: the object this setting is known at

	name = Column(Unicode(30), index=True)
	doc = Column(Unicode(1000))
	# TODO: make sure that (name,parent_id) is unique

	def __init__(self, parent, name,value, **kw):
		super(ConfigVar,self).__init__(**kw)
		self.parent = parent
		self.name = name
		self.value = value

	@staticmethod
	def get(name):
		try:
			return ConfigVar.q.get_by(name=name)
		except NoData:
			raise NoData("ConfigVar:"+name)

	@staticmethod
	def exists(parent,name,doc=None,default=None):
		cf = ConfigVar(parent=parent, name=name,doc=doc,default=default)
		return cf

	@property
	def as_str(self):
		return u"%s=%s @%s" % (self.name,repr(self.value),self.parent.name)

class SiteConfigVar(ObjectRef, JsonValue):
	"""This is one configuration variable's value for a site (or some other object, in fact)."""
	_descr = D.SiteConfigVar

	@classmethod
	def __declare_last__(cls):
		cls.var = cls.superparent
	# Owner: the user who last set the variable

	@property
	def as_str(self):
		if self.var is None or self.parent is None:
			return "‽"
		return u"%s=%s @%s" % (self.var.name,repr(self.value),self.parent.name)

