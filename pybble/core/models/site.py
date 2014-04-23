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

from datetime import datetime,timedelta

from sqlalchemy import Integer, Unicode, ForeignKey, DateTime
from sqlalchemy.orm import relationship,backref
from sqlalchemy.orm.exc import NoResultFound

from werkzeug import import_string
from flask import request

from ... import ROOT_SITE_NAME,ANON_USER_NAME
from ...compat import py2_unicode
from .. import config
from ..db import Base, Column, db
from . import DummyObject,Object, ObjectRef, TM_DETAIL_PAGE
from ._descr import D

class DummySite(DummyObject):
	"""A site without content."""
	def __init__(self,domain,name=None):
		if name is None:
			name=u"Here be "+domain
		self.domain=unicode(domain)
		self.name=name
		try:
			self.parent = Site.q.get_by(domain=u"")
		except NoResultFound:
			pass
		else:
			self.parent_id = self.parent.id
	def oid(self): return "DummySite"
	def get_template(self, detail=TM_DETAIL_PAGE):
		if isinstance(self,DummySite) and detail == TM_DETAIL_SUBPAGE:
			raise MissingDummy
		if not self.parent:
			raise NoResultFound
		return self.parent.get_template(detail)

@py2_unicode
class App(ObjectRef):
	"""An App known to pybble."""
	## Part of the object system so that it can be access-controlled if necessary.
	__tablename__ = "apps"
	_descr = D.App
	_module = None

	path = Column(Unicode(1000), nullable=False)
	name = Column(Unicode(30), nullable=False)
	doc = Column(Unicode(1000), nullable=True)

	def __str__(self):
		return u"‹App ‚%s‘ @ %s›" % (self.name, self.path)
	__repr__ = __str__

	def load(self):
		"""Load the app's module"""
		if self._module is None:
			self._module = import_string(self.name)
		return self._module

@py2_unicode
class Blueprint(ObjectRef):
	"""A Flask blueprint known to pybble. Usually a child of the master site"""
	## Part of the object system so that it can be access-controlled if necessary.
	__tablename__ = "blueprints"
	_descr = D.Blueprint

	path = Column(Unicode(1000), nullable=False)
	name = Column(Unicode(30), nullable=False)
	doc = Column(Unicode(1000), nullable=True)

	def __str__(self):
		return u"‹Blueprint ‚%s‘ @ %s›" % (self.name, self.path)
	__repr__ = __str__

@py2_unicode
class Site(ObjectRef):
	"""A web domain / app."""
	__tablename__ = "sites"
	_descr = D.Site
	#id = Column(None, ForeignKey(Object.id), primary_key=True)
	#__mapper_args__ = {'polymorphic_identity':D.Site, 'inherit_condition': id == Object.id}

	domain = Column(Unicode(100), nullable=False)
	name = Column(Unicode(30), nullable=False)
	tracked = Column(DateTime,nullable=False, default=datetime.utcnow)
	## Datestamp of newest fully-processed Tracker object

	superuser = Object._alias("parent")
	app = Object._alias("superparent")

	## NOT YET WORKING
	@property
	def storages(self):
		return self.all_children("Storage")

	def __init__(self,domain,name=None):
		super(Site,self).__init__()
		if name is None:
			name=u"Here be "+domain
		self.domain=unicode(domain)
		self.name=name

		if name == ROOT_SITE_NAME:
			s = None
		else:
			s = Site.q.get_by(name=ROOT_SITE_NAME)
			self.parent = s

		try:
			self.owner = request.user
		except (AttributeError,RuntimeError):
			self.owner = None if s is None else s.owner

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

		
	def __str__(self):
		return u"‹Site ‚%s‘ @ %s›" % (self.name, self.domain)
	__repr__ = __str__

	@property
	def data(self):
		return u"""\
name: %s
domain: %s
""" % (self.name,self.domain)

@py2_unicode
class SiteBlueprint(ObjectRef):
	"""A blueprint attached to a site's path"""
	__tablename__ = "site_blueprint"
	_descr = D.SiteBlueprint

	path = Column(Unicode(1000), required=True) ## (, verbose_name="where to attach")

	site = Object._alias('parent')
	blueprint = Object._alias('superparent')

