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

from sqlalchemy import Integer, Unicode, ForeignKey, DateTime, event, Table, Boolean, Enum
from sqlalchemy.orm import relationship,backref

from werkzeug.utils import cached_property
from flask import request
from flask._compat import string_types,text_type

from ... import ROOT_SITE_NAME,ANON_USER_NAME,ROOT_USER_NAME
from ...globals import root_site
from .. import config
from ..db import db, NoData, maybe_stale, no_update,check_unique
from ..utils import hybridmethod
from ..signal import app_list, ConfigChanged,NewSite
from . import LEN_NAME,LEN_DOMAIN,LEN_PATH
from ._module import Module
from .object import Object,ObjectRef
from .objtyp import ObjType
from .config import ConfigData
from ._const import PERM_SUB_ADMIN,PERM_READ,PERM_ADMIN,PERM_ADD

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

	config = ObjectRef(ConfigData, lazy="joined")

	@property
	def parent(self):
		return root_site
       
## Blueprint

class Blueprint(Module):
	"""A Flask blueprint known to pybble. Usually a child of the master site"""
	## Part of the object system so that it can be access-controlled if necessary.
	__tablename__ = "blueprints"

	config = ObjectRef(ConfigData, lazy="joined")

	@property
	def parent(self):
		return root_site

## Site

class Site(Object):
	"""A web domain / app."""
	__tablename__ = "sites"
	_is_new = False

	# default permissions
	_site_perm=PERM_READ
	_anon_perm=PERM_READ
	_admin_perm=PERM_ADMIN
	_admin_add_perm="Site"

	form_readonly = ('tracked',)
	form_hidden = ('sub_sites',)
	@hybridmethod
	def form_mod(self,fs,parent=None):
		if parent is not None:
			fs.set('parent',parent)
		else:
			fs.parent.required()
		super(Site,self).form_mod(fs)

	@classmethod
	def __declare_last__(cls):
		check_unique(cls, "name parent")
		super(Site,cls).__declare_last__()

	parent = ObjectRef("self","sub_sites", nullable=True)
	config = ObjectRef(ConfigData, lazy="joined")
	app = ObjectRef(App)

	inherit_parent = db.Column(Boolean, nullable=False, server_default='FALSE', default=False, doc="Inherit blueprints etc. from parent")
	domain = db.Column(Unicode(LEN_DOMAIN), nullable=False, unique=True)
	name = db.Column(Unicode(LEN_NAME), nullable=False, unique=True)
	tracked = db.Column(DateTime,nullable=False, default=datetime.utcnow)
	## Datestamp of newest fully-processed Tracker

	#TODO
	#sessioned = db.Column(Enum,name="sessiontype",enums=('ANON','ALWAYS'),nullable=False,default='ANON',server_default='ANON', doc='')

	@property
	@maybe_stale
	def all_sites(self):
		yield self
		for s in self.sub_sites:
			for ss in s.all_sites:
				yield ss
	# we don't have "yield from" in PY2

	def setup(self,domain, name=None, parent=None,app=None, superuser=None, inherit=True):
		if name is None:
			name=u"Here be "+domain
		self.domain=unicode(domain)
		if isinstance(app,string_types):
		    app = App.q.get_by(name=text_type(app))
		self.name=name
		self.parent=parent
		self.app=app
		self._superuser = superuser
		self.inherit_parent = inherit

		super(Site,self).setup()
	
	def before_insert(self):
		if self.name == ROOT_SITE_NAME:
			if self.parent is not None:
				raise RuntimeError("The new root site must be named ‘{}’, not ‘{}’.".format(ROOT_SITE_NAME,name))
			try:
				r = self.parent = root_site
			except NoData:
				pass
			else:
				raise RuntimeError("There already is a root site: {}.".format(r))
		elif self.parent is None:
			try:
				self.parent = root_site
			except NoData:
				raise RuntimeError("The new root site must be named ‘{}’, not ‘{}’.".format(ROOT_SITE_NAME,name))

		if self.config is None:
			self.config = ConfigData.new(parent=self.parent.config if self.parent else None, name="for "+str(self))
		super(Site,self).before_insert()

	def after_insert(self):
		super(Site,self).after_insert()

		sup = getattr(self,'_superuser',None)
		if sup is not None:
			self.initial_permissions(sup)

		app_list.send(NewSite)
		self.signal.connect(self.config_changed, ConfigChanged)

	def initial_permissions(self,root):
		from .permit import permit
		from .user import Group,Member,User

		## anon group
		try:
			anongroup = Group.q.get_by(parent=self, name=ANON_USER_NAME)
		except NoData:
			anongroup = Group.new(parent=self, name=ANON_USER_NAME)
			logger.debug("The anon group for {} has been created.".format(self))

		## anon user
		try:
			anonuser = User.q.get_by(site=self, username=ANON_USER_NAME)
		except NoData:
			anonuser = User.new(site=self, anon=True)
			logger.debug("The anon user for {} has been created.".format(self))
			Member.add_to(anonuser,anongroup)
			
		## admin group
		try:
			admin = Group.q.get_by(parent=self, name=ROOT_USER_NAME)
		except NoData:
			admin = Group.new(parent=self, name=ROOT_USER_NAME)
			logger.debug("The admin user group for {} has been created.".format(self))
		
			Member.add_to(root,admin)
		
		if self.parent is None:
			self._setup_root_perms()
		else:
			self.copy_perms(self.parent)

	def _setup_root_perms(self):

		for typ in ObjType.q.all():
			self.add_default_permissions(typ)

	def add_default_permissions(self,typ):
		from .permit import permit
		from .user import Group

		admin = Group.q.get_by(parent=self, name=ROOT_USER_NAME)
		anon = Group.q.get_by(parent=self, name=ANON_USER_NAME)

		for pm,actor in (('site',self),('admin',admin),('anon',anon)):
			perm = getattr(typ.mod,'_'+pm+'_perm',None)
			if perm is not None:
				permit(actor,self, objtyp=typ, right=perm,inherit=None)

			nts = getattr(typ.mod,'_'+pm+'_add_perm',())
			if isinstance(nts,string_types):
				if nts == "*":
					for nt in ObjType.q.all():
						permit(actor,self, objtyp=nt,new_objtyp=typ, right=PERM_ADD,inherit=None)
					continue

				nts = nts.split(" ")
			for nt in nts:
				nt = ObjType.get(nt)
				permit(actor,self, objtyp=nt,new_objtyp=typ, right=PERM_ADD,inherit=None)

		# Upload permissions for MIME types are added in pybble.manager.populate

	def copy_perms(self,parent):
		from .permit import Permission
		from .user import Group
		admin = Group.q.get_by(parent=self, name=ROOT_USER_NAME)
		anon = Group.q.get_by(parent=self, name=ANON_USER_NAME)
		oadmin = Group.q.get_by(parent=parent, name=ROOT_USER_NAME)
		oanon = Group.q.get_by(parent=parent, name=ANON_USER_NAME)
		for src,dst in ((oadmin,admin),(oanon,anon),(parent,self)):
			for p in Permission.q.filter_by(user=src):
				Permission.new(user=dst, target=p.target, for_objtyp=p.for_objtyp, inherit=p.inherit, right=p.right, new_objtyp=p.new_objtyp,new_mimetyp=p.new_mimetyp)

	def after_update(self):
		super(Site,self).after_update()
		self.signal.connect(self.config_changed, ConfigChanged)

	@maybe_stale
	def anon_user(self, anon_id=None):
		"""Return an anonymous user for this site."""
		from .user import User
		if anon_id is None:
			return User.q.get_by(username=ANON_USER_NAME, site=self)
		else:
			## create/recycle a new anon user.
			return User.new_anon_user(site=self, anon_id=anon_id)

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
			if s != self: # don't recurse
				s.signal.send(ConfigChanged, name=name)

## SiteBlueprint

class SiteBlueprint(Object):
	"""A blueprint attached to a site's path"""
	__tablename__ = "site_blueprint"
	_admin_add_perm=("Blueprint","Site")
	_alias = {'parent':'site'}

	site = ObjectRef(Site)
	blueprint = ObjectRef(Blueprint)
	config = ObjectRef(ConfigData, lazy="joined")

	@hybridmethod
	def form_mod(self,fs,parent=None):
		if parent is not None:
			if isinstance(parent,Site):
				f = 'site'
			elif isinstance(parent,Blueprint):
				f = 'blueprint'
			else:
				f = None
			if f is not None:
				fs.set(f,parent)
		super(self,SiteBlueprint).form_mod(fs)
	
	@classmethod
	def __declare_last__(cls):
		check_unique(cls, "site name")

		@event.listens_for(cls.path, 'set')
		def block_bad_path(target, value, oldvalue, initiator):
			if value == "":
				return
			if value == "" or value[0] != '/' or value[-1] == '/' or "//" in value or "/../" in value:
				raise RuntimeError("You cannot set a blueprint path to ‘{}’)".format(value))

		super(SiteBlueprint,cls).__declare_last__()

	name = db.Column(Unicode(LEN_NAME), required=True, nullable=False, doc="blueprint's name, for url_for() et al.")
	endpoint = db.Column(Unicode(LEN_NAME), required=False, null_as=("","impo.ssible"), nullable=False, default="", doc="Endpoint to attach as. May be empty.")
	path = db.Column(Unicode(LEN_PATH), required=False, null_as=("","impo.ssible"), nullable=False, default="", doc="URL path where to attach this ")

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
		return u"‘%s’: %s @ %s%s" % (self.name, self.blueprint.name if self.blueprint else '‽', self.site.domain if self.site else '‽', self.path)

	def before_insert(self):
		if self.config is None:
			self.config = ConfigData.new(parent=self.site.config if self.site else None, name="for {} {}".format(self.__class__.__name__,self.name))
		super(SiteBlueprint,self).before_insert()

