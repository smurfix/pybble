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

from datetime import datetime,timedelta

from sqlalchemy import Integer, Unicode, ForeignKey, DateTime, event
from sqlalchemy.orm import relationship,backref

from werkzeug.utils import cached_property
from flask import request
from flask._compat import string_types

from ... import ROOT_SITE_NAME,ANON_USER_NAME
from .. import config
from ..db import Base, Column, db, NoData, maybe_stale, no_update,check_unique
from ..signal import app_list, ConfigChanged,NewSite
from . import Object, ObjectRef, TM_DETAIL_PAGE, Loadable
from ._descr import D

## App

class App(Loadable,ObjectRef):
	"""An App known to pybble."""
	## Part of the object system so that it can be access-controlled if necessary.
	__tablename__ = "apps"
	_descr = D.App

	@classmethod
	def __declare_last__(cls):
		no_update(cls.path)

	name = Column(Unicode(30), nullable=False, unique=True, doc="Human-readable short name")
	doc = Column(Unicode(1000), nullable=True, doc="Docstring")

	@property
	def as_str(self):
		return u"‘%s’ @ %s" % (self.name, self.path)

## Blueprint

class Blueprint(Loadable,ObjectRef):
	"""A Flask blueprint known to pybble. Usually a child of the master site"""
	## Part of the object system so that it can be access-controlled if necessary.
	__tablename__ = "blueprints"
	_descr = D.Blueprint

	@classmethod
	def __declare_last__(cls):
		no_update(cls.path)

	name = Column(Unicode(30), unique=True, nullable=False, doc="Human-readable short name")
	doc = Column(Unicode(1000), nullable=True, doc="docstring")

	@property
	def as_str(self):
		return u"‘%s’ @ %s" % (self.name, self.path)

## Site

class Site(ObjectRef):
	"""A web domain / app."""
	__tablename__ = "sites"
	_descr = D.Site
	_is_new = False
	#id = Column(None, ForeignKey(Object.id), primary_key=True)
	#__mapper_args__ = {'polymorphic_identity':D.Site, 'inherit_condition': id == Object.id}
	@classmethod
	def __declare_last__(cls):
		if not hasattr(cls,'superuser'):
			cls.superuser = cls.owner
		if not hasattr(cls,'app'):
			cls.app = cls.superparent
		check_unique(cls, "name parent")

	domain = Column(Unicode(100), nullable=False, unique=True)
	name = Column(Unicode(30), nullable=False, unique=True)
	tracked = Column(DateTime,nullable=False, default=datetime.utcnow)
	## Datestamp of newest fully-processed Tracker object

	## XXX convert to relationship
	@property
	@maybe_stale
	def storages(self):
		return self.all_children("Storage")

	## XXX convert to relationship
	@property
	@maybe_stale
	def blueprints(self):
		return self.all_children("SiteBlueprint", want=None)

	@property
	@maybe_stale
	def all_sites(self):
		yield self
		for s in self.all_children(D.Site):
			for ss in s.all_sites:
				yield ss
	# we don't have "yield from" in PY2

	def setup(self,domain, name=None, parent=None,app=None):
		if name is None:
			name=u"Here be "+domain
		self.domain=unicode(domain)
		if isinstance(app,string_types):
		    app = App.q.get_by(name=text_type(app))
		self.name=name
		self.parent=parent
		self.app=app

		super(Site,self).setup()
	
	def before_insert(self):
		if self.name == ROOT_SITE_NAME:
			if self.parent is not None:
				raise RuntimeError("The new root site must be named ‘{}’, not ‘{}’.".format(ROOT_SITE_NAME,name))
			try:
				r = self.parent = Site.q.get(Site.parent==None,Site.owner!=None)
			except NoData:
				pass
			else:
				raise RuntimeError("There already is a root site: {}.".format(r))
		elif self.parent is None:
			try:
				self.parent = Site.q.get(Site.parent==None,Site.owner!=None)
			except NoData:
				raise RuntimeError("The new root site must be named ‘{}’, not ‘{}’.".format(ROOT_SITE_NAME,name))
		elif self.parent is None:
			self.parent = Site.q.get_by(name=ROOT_SITE_NAME)

		if self.owner is None:
			try:
				self.owner = request.user
			except (AttributeError,RuntimeError):
				self.owner = None if self.parent is None else self.parent.owner

	def after_insert(self):
		super(Site,self).after_insert()

		app_list.send(NewSite)
		self.signal.connect(self.config_changed, ConfigChanged)

	def after_update(self):
		super(Site,self).after_update()
		self.signal.connect(self.config_changed, ConfigChanged)

	@property
	@maybe_stale
	def anon_user(self):
		from .user import User
		## create a new anon user.
		return User.new_anon_user(site=self)

		
	@property
	@maybe_stale
	def as_str(self):
		return u"‘%s’ @ %s" % (self.name, self.domain)

	@property
	@maybe_stale
	def data(self):
		return u"""\
name: %s
domain: %s
""" % (self.name,self.domain)

	@cached_property
	def config(self):
		from .config import ConfigDict
		res = ConfigDict(self)
		res._load(vars="GLOBALS")
		res._load(recurse="parent")
		res._load(recurse="parent",vars="app")
		return res
	
	@maybe_stale
	def config_changed(self, sender=None, name=None):
		## TODO: invalidate caches, as soon as we have any
		for s in self.all_sites:
			if s is not self: # don't recurse
				s.signal.send(ConfigChanged, name=name)

## SiteBlueprint

class SiteBlueprint(ObjectRef):
	"""A blueprint attached to a site's path"""
	__tablename__ = "site_blueprint"
	_descr = D.SiteBlueprint
	@classmethod
	def __declare_last__(cls):
		if not hasattr(cls,'site'):
			cls.site = cls.parent
		if not hasattr(cls,'blueprint'):
			cls.blueprint = cls.superparent
		check_unique(cls, "parent name")

	name = Column(Unicode(30), required=True, nullable=False, doc="blueprint's name, for url_for() et al.")
	endpoint = Column(Unicode(30), nullable=False, default="", doc="Endpoint to attach as. May be empty.")
	path = Column(Unicode(1000), nullable=False, default="", doc="URL path where to attach this ")

	def setup(self, site,blueprint, endpoint=None, name=None,path=None):
		if isinstance(blueprint,string_types):
			blueprint = Blueprint.q.get_by(name=text_type(blueprint))
		if site is None:
			self.site = request.site
		else:
			if isinstance(site,string_types):
				try:
					site = Site.q.get_by(name=text_type(site))
				except NoData:
					site = Site.q.get_by(domain=text_type(site))
			self.site = site

		if name is None:
			name = blueprint.name
		if endpoint is None:
			endpoint = name

		self.blueprint = blueprint
		self.name = name
		self.path = path
		self.endpoint = endpoint

		super(SiteBlueprint,self).setup()

	def after_insert(self):
		super(SiteBlueprint,self).after_insert()
		self.blueprint.signal.connect(self.config_changed, ConfigChanged)
		self.signal.connect(self.config_changed, ConfigChanged)
	def after_load(self):
		super(SiteBlueprint,self).after_insert()
		self.blueprint.signal.connect(self.config_changed, ConfigChanged)
		self.signal.connect(self.config_changed, ConfigChanged)

	@cached_property
	def config(self):
		from .config import ConfigDict
		res = ConfigDict(self)
		res._load(vars="superparent")
		return res

	def config_changed(self, sender=None, name=None):
		self.config._reload(name=name)

	@property
	def as_str(self):
		return u"‘%s’: %s @ %s%s" % (self.name, self.blueprint.name, self.site.domain, self.path)

@event.listens_for(SiteBlueprint.path, 'set')
def block_bad_path(target, value, oldvalue, initiator):
	if value == "/":
		return
	if value == "" or value[0] != '/' or value[-1] == '/' or "//" in value or "/../" in value:
		raise RuntimeError("You cannot set a blueprint path to ‘{}’)".format(value))

