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
from flask._compat import PY2

from ...compat import py2_unicode
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
	_set_db = False
	def __init__(self,parent=None):
		self.root_path = os.curdir
		self._parent = parent
		self._set_db = bool(parent)
		
		s = parent
		while s:
			for v in SiteConfigVar.q.filter_by(site=s):
				self.setdefault(v.var.name, v.value)
			s = s.parent

		# find defaults
		for v in ConfigVar.q.all():
			if v.deleted:
				continue
			self.setdefault(v.name, v.value)

#	def __setitem__(self,k,v):
#		s = self._parent
#		if PY2:
#			if isinstance(k,str):
#				k = unicode(k)
#		cfv = None
#		while s:
#			try:
#				cfv = ConfigVar.q.get_by(name=k,parent=self._parent)
#			except NoData:
#				s = s.parent
#			else:
#				break
#		if not cfv and self._set_db:
#			raise NoData(k)
#		if self._set_db:
#			assert self._parent
#			try:
#				cf = SiteConfigVar.q.get_by(parent=self._parent, var=cfv)
#			except NoData:
#				cf = SiteConfigVar(parent=self._parent, var=cfv, value=v)
#			else:
#				cf.value=v
#		super(ConfigDict,self).__setitem__(k,v)
#
#	def __delitem__(self,k):
#		try:
#			cfv = ConfigVar.get(k)
#		except NoData:
#			# can't delete values that are only read from settings
#			raise NoData(k)
#		if self._set_db:
#			assert self.site
#			try:
#				cf = SiteConfigVar.objects.get_by(site=self.site, var=cfv)
#			except NoData:
#				pass
#			else:
#				cf.delete()
#				self[k].pop(0)
#		elif self.site.parent:
#			super(ConfigDict,self).__setitem__(k,self.site.parent.config[k])
#		else:
#			super(ConfigDict,self).__setitem__(k,cfv.default)
#		if self._set_db and self.site is not None:
#			self.site.config_changed()
#	
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

@py2_unicode
class ConfigVar(ObjectRef, JsonValue):
	"""Describes one configuration variable."""
	_descr = D.ConfigVar

	# Parent: the object this setting is known at

	name = Column(Unicode(30), index=True)
	info = Column(Unicode(100))
	# TODO: make sure that (name,parent_id) is unique

	@staticmethod
	def get(name):
		try:
			return ConfigVar.q.get_by(name=name)
		except NoData:
			raise NoData("ConfigVar:"+name)

	@staticmethod
	def exists(name,info,default=None):
		cf = ConfigVar(name=name,info=info,default=default)
		cf.save()
	def __str__(self):
		if self.var is None or self.site is None:
			return super(ConfigVar).__str__()
		return u"‹%s: %s=%s @%s›" % (self.__class__.__name__,self.var.name,repr(self.value),self.site.name)
	def __repr__(self):
		if self.var is None or self.site is None:
			return super(ConfigVar).__repr__()
		return "%s:%s=%s@%s" % (self.__class__.__name__,self.var.name,repr(self.value),self.site.name)

@py2_unicode
class SiteConfigVar(ObjectRef, JsonValue):
	"""This is one configuration variable's value for a site (or some other object, in fact)."""
	_descr = D.SiteConfigVar

	@classmethod
	def __declare_last__(cls):
		cls.var = cls.superparent
	# Owner: the user who last set the variable

	def __str__(self):
		if self.var is None or self.parent is None:
			return super(SiteConfigVar).__str__()
		return u"‹%s: %s=%s @%s›" % (self.__class__.__name__,self.var.name,repr(self.value),self.parent.name)
	def __repr__(self):
		if self.var is None or self.parent is None:
			return super(SiteConfigVar).__repr__()
		return "%s:%s=%s@%s" % (self.__class__.__name__,self.var.name,repr(self.value),self.parent.name)

