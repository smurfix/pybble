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

from flask import current_app,g,request
from flask.ext.security import UserMixin, RoleMixin
from flask._compat import string_types

from werkzeug import security
from werkzeug.utils import cached_property

from datetime import datetime,timedelta

from sqlalchemy import Integer, Unicode, DateTime, Boolean, ForeignKey, and_,or_, event
from sqlalchemy.orm import relationship,backref
from sqlalchemy.orm.base import NO_VALUE,NEVER_SET
from sqlalchemy.types import TypeDecorator, VARCHAR

from ... import ANON_USER_NAME
from ...utils import random_string, AuthError
from ...core import config
from ..db import db, NoData,NoDataExc, check_unique,no_update
from ...globals import current_site
from . import LEN_NAME,LEN_USERNAME,LEN_PERSONNAME,LEN_CRYPTPW
from ._const import PERM,PERM_NONE,PERM_ADMIN,PERM_READ,PERM_ADD,PERM_name
from .objtyp import ObjType
from .site import Site
from .object import Object,ObjectRef

import sys

import logging
logger = logging.getLogger('pybble.core.models.user')

access_logger = logging.getLogger('pybble.access')
def log_access(*args):
	access_logger.debug(" ".join(str(x) for x in args))

## User

class Password(TypeDecorator):
	"""Represents any Python object as a json-encoded string.
	"""
	impl = VARCHAR(LEN_CRYPTPW)

	def process_bind_param(self, value, dialect):
		if value: # covers both "" and None
			if ':' not in value:
				value = security.generate_password_hash(value)

		return value

class PasswordValue(object):
	password = db.Column(Password)
	## empty: cannot be used.  None: not known.

	def check_password(self, password):
		if not self.password:
			return False
		if ':' not in self.password:
			# legacy database contents. Should not happen, but might if
			# somebody sets the password via SQL.
			if app.config.LEGACY_PASSWORDS:
				self.password = security.generate_password_hash(self.password)
			else:
				return False
		return security.check_password_hash(self.password,password)

class User(PasswordValue,Object):
	"""\
		Users.

		Anonymous users are members of a group named ANON_USER_NAME
		associated with the current site. The 'main' anonymous user,
		used when no tracking is used, is named ANON_USER_NAME.

		Non-anonymous users are named … well … something else, should have
		a password, and will be members of the site they're allowed on as
		soon as they are verified.

		TODO: verification is fixed by Pybble code. It may or may not be
		actually necessary, this should be configurable.

		TODO: cleanup users who register but then do not verify themselves.
		"""
	__tablename__ = "users"
	@classmethod
	def __declare_last__(cls):
		no_update(cls.username)
		no_update(cls.site)
		check_unique(cls,"username site")
		super(User,cls).__declare_last__()
	_alias = {'parent':'site'}
	        
	# A simple way to make 'username' read-only
	username = db.Column(Unicode(LEN_USERNAME), nullable=False)

	first_name = db.Column(Unicode(LEN_PERSONNAME), nullable=True)
	last_name = db.Column(Unicode(LEN_PERSONNAME), nullable=True)
	email = db.Column(Unicode(200), nullable=True)

	first_login = db.Column(DateTime, nullable=True) ## ever
	last_login = db.Column(DateTime, nullable=True)  ## the one before this session
	this_login = db.Column(DateTime, nullable=True)  ## this session start
	cur_login = db.Column(DateTime, nullable=True)   ## this session end

	feed_age = db.Column(Integer, nullable=False, default=10)
	feed_pass = db.Column(Unicode(30), nullable=True)
	feed_read = db.Column(DateTime, nullable=True)

	site = ObjectRef(Site, doc="The site which the user registered at, otherwise not interesting")

	@classmethod
	def new_anon_user(cls,site=None, anon_id=None):
		if site is None:
			site = current_site
		g = Group.q.get_by(name=ANON_USER_NAME,parent=site)
		if anon_id is None:
			anon_id = random_string(10)

		anon_name = (ANON_USER_NAME or 'anon')+'_'+ anon_id
		try:
			u = cls.q.get_by(username=anon_name, site=site)
		except NoData:
			now = datetime.now()
			old = now - timedelta(0,current_app.config.SESSION_COOKIE_AGE)

			u = User.q.filter(User.site==site, or_(User.cur_login == None, User.cur_login < old)).order_by(cls.cur_login).join(Member,and_(Member.member_typ_id == ObjType.get(User).id, Member.member_id==User.id)).filter(Member.group==g).first()
			#u = cls.q.filter_by(username=ANON_USER_NAME, site=site).order_by(cls.cur_login).first()
			if u is None:
				u = cls.new(username=anon_name, site=site, anon=True)
				logger.info("New anon user {} for {}".format(u,site))
				u.first_login = now
				Member.add_to(u,g)
			else:
				logger.info("Recycling anon user {} for {}".format(u,site))
				from .tracking import Delete, TrackingObject
				for c,k in u.all_refs:
					if isinstance(c,TrackingObject):
						pass
					elif isinstance(c,Member) and c.group.name == ANON_USER_NAME and c.group.parent == site:
						pass
					else:
						Delete.new(c,comment="ANON user cleanup")
		else:
			u.last_login = u.this_login
		u.cur_login = now
		u.this_login = now
		return u
		
	@property
	def data(self):
		res="username: %s\n" % (self.username,)
		if self.first_name or self.last_name:
			res += self.first_name or ""
			res += " " if self.first_name and self.last_name else ""
			res += self.last_name or ""
			res += "\n"
		res += "First login: %s\nLast login: %s\n" % (self.first_login,self.last_login)
		return res

	_anon = None
	def setup(self, username=ANON_USER_NAME, password=None, site=None, anon=False, **kw):
		self._anon = anon
		self.username=username
		self.password=password
		self.site=site or current_site
		super(User,self).setup(**kw)

	def before_insert(self):
		super(User,self).before_insert()

		if self.site is None:
			self.site = current_site
	
	def after_insert(self):
		from .permit import Permission

		if self._anon:
			anon = Group.q.get_by(name=ANON_USER_NAME,parent=self.site)
			Member.add_to(self, anon)
		else:
			Member.add_to(self, self.site)

		if self.username != ANON_USER_NAME:
			# you can look at your own user record
			Permission.new(self,self, right=PERM_READ, inherit=False)
	
	@property
	def tracks(self):
		return Tracker.q.filter_by(owner=self).order_by(Desc(Tracker.timestamp))

	@property
	def trackers(self):
		return WantTracking.q.filter_by(owner=self)

	@property
	def anon(self):
		# for compatibility
		return self.anon_on()

	def anon_on(self, site=None):
		"""Check if this user is anonymous OR unverified, on this site."""
		if self.username == ANON_USER_NAME:
			return True
		if site is None:
			site = current_site
		anon = Group.q.get_by(name=ANON_USER_NAME,parent=site)
		return self.member_of(anon)

	@property
	def name(self):
		if self.username == ANON_USER_NAME:
			return "·ANONYM·"
		if self.first_name and self.last_name:
			return u"%s %s" % (self.first_name,self.last_name)
		if self.first_name:
			return self.first_name
		if self.last_name:
			return self.last_name
		if self.username:
			return self.username
		return "·UNNAMED·"

	def visits(self,obj):
		from .tracking import Breadcrumb

		if getattr(obj,"_no_crumbs",False):
			return # no recursive or similar nonsense, please
		try:
			s = Breadcrumb.q.get_by(user=self, obj=obj)
		except NoData:
			s = Breadcrumb.new(self,obj)
		s.visit()
	
	def last_visited(self,cls=None):
		from .tracking import Breadcrumb

		q = { "user":self, "site":current_site }
		if cls:
			q["obj_type_id"] = cls.cls_objtyp().id
		try:
			r = Breadcrumb.q.filter_by(**q).order_by(Breadcrumb.visited.desc()).first()
		except NoData:
			return None
		if r:
			return r.parent
	
	def all_visited(self, cls=None):
		from .tracking import Breadcrumb

		q = { "user":self, "site":current_site }
		if cls:
			q["objtyp"] = cls.cls_objtyp()
		return Breadcrumb.q.filter_by(**q).order_by(Breadcrumb.visited.desc())

	def is_verified(self, site=None):
		if site is None:
			site = current_site
		try:
			m = Member.q.get_by(member=self,group=site)
		except NoData:
			return False
		else:
			return not m.excluded

	def add_verified(self,v,site=None):
		if site is None:
			site = current_site
		anon = Group.q.get_by(name=ANON_USER_NAME,owner=site,parent=site)
		if site is None:
			site = current_site
		Member.add_to(self,site)
		Member.drop_from(self,anon)
	verified = property(is_verified,add_verified)
				
	@property
	def as_str(self):
		if self.username:
			return self.username

		try:
			return u"anon @%s" % (self.superparent.domain)
		except Exception:
			return u"anon @ ‽"

	@property
	def groups(self):
		ul = getattr(self,"_memberships",None)
		if ul is None:
			ul = [self]
			uld = set((self,))

			ulq = [self]
			while ulq:
				u = ulq.pop(0)
				for m,g in u.memberships:
					if getattr(m,"excluded",False):
						uld.add(g)
						continue
					if g not in uld:
						ul.append(g)
					ulq.append(g)
					uld.add(g)
			self._memberships = ul
		return ul

	def can_do(self,*a,**k):
		from .permit import can_do
		return can_do(self,*a,**k)
	def will_do(user,obj,objtyp=None, perm=PERM_NONE):
		if user.can_do(obj,objtyp) < perm:
			raise AuthError(obj,perm)
	@property
	def recent_tracks(self):
		latest = datetime.utcnow() - timedelta(self.feed_age,0)
### TODO test if that works with sqlalchemy
#		return UserTracker.q.filter(UserTracker.owner == self,
#		                            UserTracker.tracker.timestamp > datetime.utcnow() - timedelta(self.feed_age,0))\
#		                    .order_by(UserTracker.id.desc())
		for obj in UserTracker.q.filter_by(owner=self).order_by(UserTracker.id.desc()):
			if obj.parent.timestamp < latest:
				return
			yield obj

	@property
	def has_trackers(self):
		return WantTracking.q.filter_by(owner=self).count()

## Groups

class Group(Object):
	"""
		A group of users. (Usually.)
		"""
	__tablename__ = "groups"
	_admin_add_perm="User"

	name = db.Column(Unicode(LEN_NAME))
	parent = ObjectRef()

	def setup(self,name,parent):
		self.name = name
		self.parent = parent
		super(Group,self).setup()
	
	@property
	def members(self):
		return Member.q.filter_by(group=self)

	def add(self,member, fail=False):
		return Member.add_to(member,self, fail=fail)
	def delete(self,member, fail=False):
		return Member.drop_from(member,self, fail=fail)
	def __contains__(self,member):
		return Member.q.filter_by(group=self,member=member).count() > 0

## Membership

class Member(Object):
	"""\
		Indicates membership of one object of another.
		parent=group, owner=member
		"""
	__tablename__ = "groupmembers"
	_no_crumbs = True
	_admin_add_perm="Group"
	_alias = {'parent':'group'}

	@classmethod
	def __declare_last__(cls):
		check_unique(cls,"member group")
		super(Member,cls).__declare_last__()

	member = ObjectRef()
	group = ObjectRef(doc="Usually a group, but may be anything")

	excluded = db.Column(Boolean, nullable=False,default=False)

	def setup(self,member,group, excluded=False):
		if isinstance(member,User) and isinstance(group,Site) and member.username == ANON_USER_NAME:
			assert False
		self.member = member
		self.group = group
		self.excluded = excluded

		super(Member,self).setup()

	@classmethod
	def add_to(cls,member,group,fail=False):
		"""Adds the user to the group"""
		try:
			M = cls.q.get_by(member=member,group=group)
		except NoData:
			M = cls.new(member=member,group=group)
			logger.debug("Add: "+str(M))
		else:
			if fail:
				raise ManyDataExc("{} is already a member of {}".format(member,group))
		return M

	@classmethod
	def drop_from(cls,member,group,fail=False):
		from .tracking import Delete

		"""Remove the user from the group"""
		try:
			M = cls.q.get_by(member=member,group=group)
		except NoData:
			if fail:
				raise NoDataExc("{} is not a member of {}".format(member,group))
			return M
		else:
			logger.debug("Del: "+str(M))
			return Delete.new(M)

	@property
	def as_str(self):
		if self._rec_str or not self.group or not self.member: return "‽"
		try:
			self._rec_str += 1
			return u'%s%s in %s' % (self.member, " NOT" if self.excluded else "", self.group)
		finally:
			self._rec_str -= 1

Object.new_member_rule(Member, "member","group")

