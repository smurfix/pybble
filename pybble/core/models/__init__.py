#!/usr/bin/env python
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

import json
import logging
import datetime
import random
import os

from blinker import NamedSignal
from mongoengine.errors import NotUniqueError,DoesNotExist
from flask import url_for, current_app, g
from flask.config import Config

from ... import ROOT_NAME
from ..db import db

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

class KeyValue(db.DynamicEmbeddedDocument):
	pass

class ConfigDict(Config):
	def __init__(self,site=None):
		self.root_path = os.curdir
		self.site = site
		self.set_db = bool(site)

	def __setitem__(self,k,v):
		try:
			cfv = ConfigVar.get(k)
		except DoesNotExist:
			if self.set_db:
				raise DoesNotExist(k)
			cfv = None
		if self.set_db:
			assert self.site
			cf = SiteConfigVar(site=self.site, var=cfv, value=v)
			try:
				cf.save()
			except NotUniqueError:
				cf = SiteConfigVar.objects.get(site=self.site, var=cfv)
				cf.value=v
				cf.save()
				if cfv is not None and cfv.prepend:
					self[k].pop(0)
		if cfv is None or not cfv.prepend:
			super(ConfigDict,self).__setitem__(k,v)
		elif k in self:
			self[k].insert(0,v)
		else:
			super(ConfigDict,self).__setitem__(k,[v])
		if self.set_db and self.site is not None:
			self.site.config_changed()

	def __delitem__(self,k):
		try:
			cfv = ConfigVar.get(k)
		except DoesNotExist:
			# can't delete values that are only read from settings
			raise DoesNotExist(k)
		if self.set_db:
			assert self.site
			try:
				cf = SiteConfigVar.objects.get(site=self.site, var=cfv)
			except DoesNotExist:
				pass
			else:
				cf.delete()
				self[k].pop(0)
		elif self.site.parent:
			super(ConfigDict,self).__setitem__(k,self.site.parent.config[k])
		else:
			super(ConfigDict,self).__setitem__(k,cfv.default)
		if self.set_db and self.site is not None:
			self.site.config_changed()
	
	def disarm(self):
		self.set_db = False
	def arm(self):
		self.set_db = True

class Site(db.Document):
	name = db.StringField(unique=True, required=True)
	domain = db.StringField(unique=True, required=True)
	parent = db.ReferenceField('Site', reverse_delete_rule=db.CASCADE)
	app = db.StringField(required=True, default=ROOT_NAME)
	meta = {
		'indexes': [('parent',)]
	}
	_parents = None

	def __repr__(self):
		return "<%s: %s>" % (self.__class__.__name__,self.name)
	def __unicode__(self):
		return "%s: %s" % (self.__class__.__name__,self.name)
	__str__=__unicode__

	@property
	def blueprints(self):
		return Blueprint.objects(site=self)
	
	@property
	def children(self):
		return Site.objects(parent=self)
	
	@property
	def parents(self):
		p = self._parents
		if p is None:
			self._parents = p = []
			while self:
				p.append(self)
				self = self.parent
		return p
	
	@property
	def children_tree(self):
		yield self
		for s in self.children:
			for ss in s.children_tree:
				yield ss

	@property
	def config(self):
		if self.parent:
			cfg = self.parent.config
			cfg.disarm()
		else:
			cfg = ConfigDict()
			for s in ConfigVar.objects:
				if s.prepend:
					cfg[s.name] = s.default or []
				else:
					cfg[s.name] = s.default
		for s in SiteConfigVar.objects(site=self):
			if s.var.prepend:
				cfg[s.var.name].insert(0,s.value)
			else:
				cfg[s.var.name] = s.value
		cfg.site = self
		cfg.arm()
		return cfg
	
	def config_changed(self, **kwargs):
		for s in self.children_tree:
			sig = _config_changed_sig(s.name)
			sig.send(self,**kwargs)

class Blueprint(db.Document):
	"""Attaches blueprints to a site"""
	name = db.StringField(required=True, unique_with=("site",))
	path = db.StringField(required=True, verbose_name="where to attach")
	site = db.ReferenceField('Site', reverse_delete_rule=db.CASCADE)
	blueprint = db.StringField(required=True, verbose_name="import the code at")
	params = db.EmbeddedDocumentField(KeyValue, required=True, default=KeyValue)
	meta = {
		'indexes': [('site',)]
	}
	def __repr__(self):
		return "<%s: %s @%s>" % (self.__class__.__name__,self.name,self.site.name)
	def __unicode__(self):
		return "%s:%s@%s" % (self.__class__.__name__,self.name,self.site.name)
	__str__=__unicode__

class ConfigVar(db.Document):
	"""Describes one configuration variable."""
	name = db.StringField(unique=True, required=True)
	info = db.StringField(required=True)
	default = db.StructField()
	prepend = db.BooleanField(default=False)

	def __init__(self,**kv):
		if kv.get("prepend",False):
			v = kv.get("default",[])
			if not hasattr(v,"prepend"):
				v = [v]
		super(ConfigVar,self).__init__(**kv)

	@staticmethod
	def get(name):
		try:
			return ConfigVar.objects.get(name=name)
		except DoesNotExist:
			raise DoesNotExist("ConfigVar:"+name)

	@staticmethod
	def exists(name,info,default=None,prepend=False):
		cf = ConfigVar(name=name,info=info,default=default,prepend=prepend)
		cf.save()
	meta = {
		'indexes': [('name',)]
	}
	def __repr__(self):
		return "<%s: %s>" % (self.__class__.__name__,self.name)
	def __unicode__(self):
		return "%s:%s" % (self.__class__.__name__,self.name)
	__str__=__unicode__
	
class SiteConfigVar(db.Document):
	"""This is one configuration variable's value for a site."""
	site = db.ReferenceField(Site, reverse_delete_rule=db.CASCADE)
	var = db.ReferenceField(ConfigVar, unique_with=("site",), reverse_delete_rule=db.CASCADE)
	value = db.StructField()
	meta = {
		'indexes': [('site', 'var')]
	}
	def __repr__(self):
		return "<%s: %s=%s @%s>" % (self.__class__.__name__,self.var.name,repr(self.value),self.site.name)
	def __unicode__(self):
		return "%s:%s=%s@%s" % (self.__class__.__name__,self.var.name,repr(self.value),self.site.name)
	__str__=__unicode__

