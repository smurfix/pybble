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

from flask import url_for, current_app, g,request
from flask.config import Config
from flask._compat import string_types,text_type

from .. import config as pybble_config
from ...globals import root_site
from ..utils import attrdict
from ..db import db, NoData,NoDataExc, check_unique,no_update, refresh, JSON, maybe_stale
from ..signal import ConfigChanged
from . import LEN_NAME,LEN_DOC
from .object import Object,ObjectRef
from ...core import config
from ... import cache

from datetime import datetime,timedelta

from sqlalchemy.orm import relationship,backref

logger = logging.getLogger('pybble.core.models.config')

## JSON type

class JsonValue(object):
	value = db.Column(JSON)

## ConfigVar

class ConfigVar(Object, JsonValue):
	"""Describes one configuration variable."""

	@classmethod
	def __declare_last__(cls):
		check_unique(cls,"parent name")
		no_update(cls.name)
		no_update(cls.parent)
		super(ConfigVar,cls).__declare_last__()

	parent = ObjectRef()
	name = db.Column(db.Unicode(LEN_NAME), index=True)
	doc = db.Column(db.Unicode(LEN_DOC))

	def setup(self, parent, name,value, doc=None):
		self.parent = parent
		self.name = name
		self.value = value
		if doc is not None: self.doc = doc
		super(ConfigVar,self).setup()

	@staticmethod
	def get(parent,name):
		try:
			return ConfigVar.q.get_by(parent=parent, name=name)
		except NoData:
			raise NoDataExc("ConfigVar:"+name)

	@staticmethod
	def exists(parent,name,doc=None,default=None):
		try:
			return ConfigVar.get(parent,name)
		except NoData:
			return ConfigVar.new(parent=parent, name=name,doc=doc,value=default)

	@property
	def as_str(self):
		return u"%s=%s @%s" % (self.name,repr(self.value),self.parent.name)

## ConfigData
class ConfigData(Object):
	"""This is a collection of configuration variables, referred to by some object or other"""

	super = ObjectRef("self", nullable=True, doc="inherited configuration")
	name = db.Column(db.Unicode(LEN_NAME), index=True, doc="informal name for this collection")

	@property
	@maybe_stale
	def parent(self):
		from .site import Site
		return self.super or root_site

	def setup(self, name, parent=None):
		self.name = name
		self.super = parent
		super(ConfigData,self).setup()

	def get(self, k, default=None):
		try:
			return self[k]
		except KeyError:
			return default

	def __getattr__(self,k):
		if k.startswith('_'):
			return super(ConfigData,self).__getattr__(k)
		return self[k]
		try:
			return self[k]
		except KeyError:
			raise AttributeError(k)

	def setdefault(self,k,d):
		try:
			res = self[k]
		except KeyError:
			self[k] = res = d
		return res

	def __contains__(self,k):
		if k in pybble_config:
			return True
		return ConfigVar.q.get_by(name=k).count()

	def __getitem__(self,k):
		if isinstance(k,ConfigVar):
			var = k
		else:
			k = text_type(k)
			if k in pybble_config and pybble_config._is_fixed(k):
				return pybble_config[k]
			try:
				var = ConfigVar.q.cache_key("VAR",k).get_by(name=k)
			except RuntimeError: # system not yet configured
				if k in pybble_config:
					return pybble_config[k]
				raise
			except NoData:
				raise KeyError(k)
		self = refresh(self)

		def gen():
			try:
				val = SiteConfigVar.q.get_by(parent=self, var=var).value
			except NoData:
				if self.super is None:
					return var.value
				val = self.super[k]
			return val
		return cache.cached(gen, "SVAR", self.id,var.id)
	
	def __setitem__(self,k,v):
		if isinstance(k,ConfigVar):
			var = k
		else:
			k = text_type(k)
			if k in pybble_config:
				pybble_config[k] = v
				if pybble_config._is_fixed(k):
					return

			try:
				var = ConfigVar.q.cache_key("VAR",k).get_by(name=k)
			except RuntimeError:
				if k in pybble_config:
					return
				raise

		self = refresh(self)
		try:
			ov = SiteConfigVar.q.get_by(parent=self, var=var)
		except NoData:
			SiteConfigVar.new(self,var,v)
		else:
			ov.value = v
		db.session.flush()
		cache.delete("SVAR",'*',var.id)

	@maybe_stale
	def __delitem__(self,k):
		k = text_type(k)
		assert k not in pybble_config, k

		var = ConfigVar.q.cache_key("VAR",k).get_by(name=k)
		try:
			ov = SiteConfigVar.q.get_by(parent=self, var=var)
		except NoData:
			pass
		else:
			db.session.delete(ov)
			cache.delete("SVAR",'*',var.id)
			db.session.flush()

	@maybe_stale
	def keys(self):
		for k in pybble_config.keys():
			yield k
		for k in ConfigVar.q.all():
			yield k.name
	@maybe_stale
	def values(self):
		for k in pybble_config.values():
			yield k
		for k in ConfigVar.q.all():
			yield self[k]
	@maybe_stale
	def items(self):
		for k in pybble_config.items():
			yield k
		for k in ConfigVar.q.all():
			yield (k.name,self[k])

## SiteConfigVar

class SiteConfigVar(Object, JsonValue):
	"""This is one configuration variable's value for a site (or some other object, in fact)."""

	var = ObjectRef(ConfigVar)
	parent = ObjectRef(ConfigData, lazy="joined")

	@classmethod
	def __declare_last__(cls):
		check_unique(cls,"parent var")
		no_update(cls.parent,ConfigData)
		no_update(cls.var)
		super(SiteConfigVar,cls).__declare_last__()
	# Owner: the user who last set the variable

	def setup(self,parent,var,value):
		# assert that exactly one of var or superparent is set
		self.parent = parent
		self.var = var
		self.value = value

		super(SiteConfigVar,self).setup()

	def before_insert(self):
		if not isinstance(self.parent,ConfigData):
			self.parent = self.parent.config
		super(SiteConfigVar,self).before_insert()
		
	@property
	def as_str(self):
		if self.var is None or self.parent is None:
			return "‽"
		return u"%s=%s @%s" % (self.var.name,repr(self.value),self.parent.name)

