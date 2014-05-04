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

from datetime import datetime,timedelta

from sqlalchemy import Integer, Unicode, ForeignKey, DateTime
from sqlalchemy.orm import relationship,backref

from werkzeug import import_string
from werkzeug.utils import cached_property
from flask import request
from flask._compat import string_types

from ... import ROOT_SITE_NAME,ANON_USER_NAME
from .. import config
from ..db import Base, Column, db, NoData
from . import Object, ObjectRef, TM_DETAIL_PAGE, Loadable
from ._descr import D

class App(Loadable,ObjectRef):
	"""An App known to pybble."""
	## Part of the object system so that it can be access-controlled if necessary.
	__tablename__ = "apps"
	_descr = D.App

	name = Column(Unicode(30), nullable=False, doc="Human-readable short name")
	doc = Column(Unicode(1000), nullable=True, doc="Docstring")

	@property
	def as_str(self):
		return u"‘%s’ @ %s" % (self.name, self.path)

class Blueprint(Loadable,ObjectRef):
	"""A Flask blueprint known to pybble. Usually a child of the master site"""
	## Part of the object system so that it can be access-controlled if necessary.
	__tablename__ = "blueprints"
	_descr = D.Blueprint

	name = Column(Unicode(30), nullable=False)
	doc = Column(Unicode(1000), nullable=True)

	@property
	def as_str(self):
		return u"‘%s’ @ %s" % (self.name, self.path)

class Site(ObjectRef):
	"""A web domain / app."""
	__tablename__ = "sites"
	_descr = D.Site
	#id = Column(None, ForeignKey(Object.id), primary_key=True)
	#__mapper_args__ = {'polymorphic_identity':D.Site, 'inherit_condition': id == Object.id}
	@classmethod
	def __declare_last__(cls):
		cls.superuser = cls.parent
		cls.app = cls.superparent

	domain = Column(Unicode(100), nullable=False, unique=True)
	name = Column(Unicode(30), nullable=False, unique=True)
	tracked = Column(DateTime,nullable=False, default=datetime.utcnow)
	## Datestamp of newest fully-processed Tracker object

	## XXX convert to relationship
	@property
	def storages(self):
		return self.all_children("Storage")

	## XXX convert to relationship
	@property
	def blueprints(self):
		return self.all_children("SiteBlueprint", want=None)

	@property
	def all_sites(self):
		yield self
		for s in self.all_children(D.Site):
			for ss in s.all_sites:
				yield ss
	# we don't have "yield from

	def __init__(self,domain, name=None, **kw):
		super(Site,self).__init__(**kw)
		if name is None:
			name=u"Here be "+domain
		self.domain=unicode(domain)
		self.name=name

		if name == ROOT_SITE_NAME:
			s = None
		elif self.parent is None:
			s = Site.q.get_by(name=ROOT_SITE_NAME)
			self.parent = s

		if self.owner is None:
			try:
				self.owner = request.user
			except (AttributeError,RuntimeError):
				self.owner = None if self.parent is None else self.parent.owner

	@property
	def anon_user(self):
		from .user import User
		while True:
			try:
				return User.q.get_by(parent=self, username=ANON_USER_NAME)
			except NoResultFound:
				if self.parent:
					self = self.parent
				else:
					raise

		
	@property
	def as_str(self):
		return u"‘%s’ @ %s" % (self.name, self.domain)

	@property
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
		res._load(recurse="parent",vars="superparent")
		return res
	
	def config_changed(self):
		## TODO: invalidate a bunch of caches, as soon as we have any
		for s in self.all_children("Site",None):
			s.config._reload()
			s.config_changed()


class SiteBlueprint(ObjectRef):
	"""A blueprint attached to a site's path"""
	__tablename__ = "site_blueprint"
	_descr = D.SiteBlueprint
	@classmethod
	def __declare_last__(cls):
		cls.site = cls.parent
		cls.blueprint = cls.superparent

	name = Column(Unicode(30), required=True) ## (, verbose_name="blueprint's name, for url_for() et al.")
	path = Column(Unicode(1000), nullable=False, default="") ## (, verbose_name="URL path where to attach this ")

	def __init__(self,site=None,blueprint=None,**kw):
		super(SiteBlueprint,self).__init__(**kw)

		if self.superparent is not None:
			assert blueprint is None
		else:
			assert blueprint is not None
			if isinstance(blueprint,string_types):
				blueprint = Blueprint.q.get_by(name=text_type(blueprint))
			self.blueprint = blueprint

		if self.parent is not None:
			assert site is None
		elif site is None:
			self.parent = current_app.site
		else:
			if isinstance(site,string_types):
				try:
					site = Site.q.get_by(name=text_type(site))
				except NoData:
					site = Site.q.get_by(domain=text_type(site))
			self.parent = site

	@cached_property
	def config(self):
		from .config import ConfigDict
		res = ConfigDict(self)
		res._load(vars="superparent")
		return res

