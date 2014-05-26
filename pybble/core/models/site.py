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
import logging

from sqlalchemy import Integer, Unicode, ForeignKey, DateTime, event, Table
from sqlalchemy.orm import relationship,backref

from werkzeug.utils import cached_property
from flask import request
from flask._compat import string_types,text_type

from ... import ROOT_SITE_NAME,ANON_USER_NAME,ROOT_USER_NAME
from .. import config
from ..db import Base, Column, db, NoData, maybe_stale, no_update,check_unique
from ..signal import app_list, ConfigChanged,NewSite
from ._module import Module
from .object import Object,ObjectRef
from .objtyp import ObjType
from .config import ConfigData
from ._const import PERM_SUB_ADMIN,PERM_READ,PERM_ADMIN

logger = logging.getLogger('pybble.core.models.site')

#t_storage_site = Table(
#	'ref_storage_site', Base.metadata,
#	Column('site_id', Integer, ForeignKey('sites.id')),
#	Column('storage_id', Integer, ForeignKey('storage.id'))
#)

## App

class App(Module):
	"""An App known to pybble."""
	## Part of the object system so that it can be access-controlled if necessary.
	__tablename__ = "apps"

	config = ObjectRef(ConfigData)

## Blueprint

class Blueprint(Module):
	"""A Flask blueprint known to pybble. Usually a child of the master site"""
	## Part of the object system so that it can be access-controlled if necessary.
	__tablename__ = "blueprints"

	config = ObjectRef(ConfigData)


## Site

class Site(Object):
	"""A web domain / app."""
	__tablename__ = "sites"
	_is_new = False
	_site_perm=PERM_READ
	_anon_perm=PERM_READ

	@classmethod
	def __declare_last__(cls):
		check_unique(cls, "name parent")
		super(Site,cls).__declare_last__()

	parent = ObjectRef("self","sub_sites", nullable=True)
	config = ObjectRef(ConfigData)
	app = ObjectRef(App)

	domain = Column(Unicode(100), nullable=False, unique=True)
	name = Column(Unicode(30), nullable=False, unique=True)
	tracked = Column(DateTime,nullable=False, default=datetime.utcnow)
	## Datestamp of newest fully-processed Tracker

	#storages = relationship(Storage, secondary=t_storage_site, backref="sites")

	@property
	@maybe_stale
	def all_sites(self):
		yield self
		for s in self.sub_sites:
			for ss in s.all_sites:
				yield ss
	# we don't have "yield from" in PY2

	def setup(self,domain, name=None, parent=None,app=None, superuser=None):
		if name is None:
			name=u"Here be "+domain
		self.domain=unicode(domain)
		if isinstance(app,string_types):
		    app = App.q.get_by(name=text_type(app))
		self.name=name
		self.parent=parent
		self.app=app
		self.config = ConfigData.new("Site "+name,parent=parent.config if parent is not None else None)
		self._superuser = superuser

		super(Site,self).setup()
	
	def before_insert(self):
		if self.name == ROOT_SITE_NAME:
			if self.parent is not None:
				raise RuntimeError("The new root site must be named ‘{}’, not ‘{}’.".format(ROOT_SITE_NAME,name))
			try:
				r = self.parent = Site.q.get(Site.parent==None)
			except NoData:
				pass
			else:
				raise RuntimeError("There already is a root site: {}.".format(r))
		elif self.parent is None:
			try:
				self.parent = Site.q.get(Site.parent==None)
			except NoData:
				raise RuntimeError("The new root site must be named ‘{}’, not ‘{}’.".format(ROOT_SITE_NAME,name))
		elif self.parent is None:
			self.parent = Site.q.get_by(name=ROOT_SITE_NAME)

	def after_insert(self):
		super(Site,self).after_insert()

		self.config = ConfigData.new(parent=self.parent.config if self.parent else None, name="for "+str(self))

		app_list.send(NewSite)
		self.signal.connect(self.config_changed, ConfigChanged)

		if self._superuser is not None:
			self.initial_permissions(self._superuser)
	
	def initial_permissions(self,root):
		from .permit import permit
		from .user import Group,Member

		## anon group
		try:
			anon = Group.q.get_by(parent=self, name=ANON_USER_NAME)
		except NoData:
			anon = Group.new(parent=self, name=ANON_USER_NAME)
			logger.debug("An anon user group for {} has been created.".format(self))

		## admin group
		try:
			admin = Group.q.get_by(parent=self, name=ROOT_USER_NAME)
		except NoData:
			admin = Group.new(parent=self, name=ROOT_USER_NAME)
			logger.debug("An admin user group for {} has been created.".format(self))
		
		Member.add_to(root,admin)
		
		def gen(typ,perm,who):
			if perm is None: return
			if perm < 0:
				permit(who,self,perm,typ)
				if who is admin:
					perm = PERM_ADMIN
				else:
					perm = PERM_SUB_ADMIN
			permit(who,self,perm,typ)
		for typ in ObjType.q.all():
			gen(typ,typ.site_permission,self)
			gen(typ,typ.admin_permission,admin)
			gen(typ,typ.anon_permission,anon)

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
	def blueprints(self):
		return SiteBlueprint.q.filter_by(site=self)

#	@cached_property
#	def config(self):
#		from .config import ConfigDict
#		res = ConfigDict(self)
#		res._load(vars="GLOBALS")
#		res._load(recurse="parent")
#		res._load(recurse="parent",vars="app")
#		return res
	
	@maybe_stale
	def config_changed(self, sender=None, name=None):
		## TODO: invalidate caches, as soon as we have any
		for s in self.all_sites:
			if s is not self: # don't recurse
				s.signal.send(ConfigChanged, name=name)

## SiteBlueprint

class SiteBlueprint(Object):
	"""A blueprint attached to a site's path"""
	__tablename__ = "site_blueprint"

	site = ObjectRef(Site)
	blueprint = ObjectRef(Blueprint)
	config = ObjectRef(ConfigData)

	@classmethod
	def __declare_last__(cls):
		check_unique(cls, "site name")
		super(SiteBlueprint,cls).__declare_last__()

	name = Column(Unicode(30), required=True, nullable=False, doc="blueprint's name, for url_for() et al.")
	endpoint = Column(Unicode(30), nullable=False, default="", doc="Endpoint to attach as. May be empty.")
	path = Column(Unicode(1000), nullable=False, default="", doc="URL path where to attach this ")

	def setup(self, site,blueprint, endpoint=None, name=None,path=None):
		if isinstance(blueprint,string_types):
			blueprint = Blueprint.q.get_by(name=text_type(blueprint))
		if site is None:
			from ...globals import current_site
			self.site = current_site
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
		self.config = ConfigData.new("SiteBlueprint "+name,parent=blueprint.config)

		super(SiteBlueprint,self).setup()

	def after_insert(self):
		super(SiteBlueprint,self).after_insert()
		self.blueprint.signal.connect(self.config_changed, ConfigChanged)
		self.signal.connect(self.config_changed, ConfigChanged)
	def after_load(self):
		super(SiteBlueprint,self).after_insert()
		self.blueprint.signal.connect(self.config_changed, ConfigChanged)
		self.signal.connect(self.config_changed, ConfigChanged)

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

