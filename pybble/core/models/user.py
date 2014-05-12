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
from ..db import Base, Column, db, NoData, check_unique,no_update
from . import Object,ObjectRef, PERM,PERM_NONE,PERM_ADMIN,PERM_READ,PERM_ADD,PERM_name, Discriminator
from .site import Site
from .tracking import Breadcrumb,Delete
from ._descr import D

import sys

import logging
logger = logging.getLogger('pybble.core.models.user')

access_logger = logging.getLogger('pybble.access')
def log_access(*args):
	access_logger.debug(" ".join(str(x) for x in args))

## Auth
#class Role(ObjectRef, RoleMixin):
#	name = db.StringField(max_length=80, unique_with=('site',))
#	description = db.StringField(max_length=255)
#
#	@classmethod
#	def createrole(cls, name,site=None, description=None):
#		if site is None:
#			site = g.site
#		return cls.objects.create(
#			name=name,
#			site=site,
#			description=description
#		)
#
#	def __unicode__(self):
#		return u"{0} ({1})".format(self.name, self.description or 'Role')
#
#class User(db.DynamicDocument, UserMixin):
#	name = db.StringField(max_length=255, unique=True)
#	email = db.EmailField(max_length=255, unique=True)
#	password = db.StringField(max_length=255)
#	active = db.BooleanField(default=True)
#	changed_at = db.DateTimeField()
#	roles = db.ListField(
#		db.ReferenceField(Role, reverse_delete_rule=db.DENY), default=[]
#	)
#
#	@queryset_manager
#	def objects(cls, q):
#		return q(roles__site__in=g.site.parents)
#
#	last_login_at = db.DateTimeField()
#	current_login_at = db.DateTimeField()
#	last_login_ip = db.StringField(max_length=255)
#	current_login_ip = db.StringField(max_length=255)
#	login_count = db.IntField()
#
#	username = db.StringField(max_length=50, required=False, unique=True)
#
#	remember_token = db.StringField(max_length=255)
#	authentication_token = db.StringField(max_length=255)
#
#	def clean(self, *args, **kwargs):
#		if not self.username:
#			self.username = User.generate_username(self.email)
#
#		 super(User, self).clean(*args, **kwargs)
##		try:
##			super(User, self).clean(*args, **kwargs)
##		except Exception:
##			pass
#
#	@classmethod
#	def generate_username(cls, email):
#		username = email.lower()
#		for item in ['@', '.', '-', '+']:
#			username = username.replace(item, '_')
#		return username
#
#	def set_password(self, password, save=False):
#		self.password = encrypt_password(password)
#		if save:
#			self.save()
#
#	@classmethod
#	def createuser(cls, name, email, password,
#				   site=None, active=True, roles=None, username=None):
#
#		username = username or cls.generate_username(email)
#		if site is None:
#			site = request.site
#		return cls.objects.create(
#			name=name,
#			email=email,
#			password=encrypt_password(password),
#			active=active,
#			roles=roles,
#			username=username
#		)
#
#	@property
#	def display_name(self):
#		return self.name or self.email
#
#	def __unicode__(self):
#		return u"{0} <{1}>".format(self.name or '', self.email)
#
#	@property
#	def connections(self):
#		return Connection.objects(user_id=str(self.id))
#
#class Connection(db.Document):
#	user_id = db.ObjectIdField()
#	provider_id = db.StringField(max_length=255)
#	provider_user_id = db.StringField(max_length=255)
#	access_token = db.StringField(max_length=255)
#	secret = db.StringField(max_length=255)
#	display_name = db.StringField(max_length=255)
#	full_name = db.StringField(max_length=255)
#	profile_url = db.StringField(max_length=512)
#	image_url = db.StringField(max_length=512)
#	rank = db.IntField(default=1)
#
#	@property
#	def user(self):
#		return User.objects(id=self.user_id).first()

## User

class Password(TypeDecorator):
	"""Represents any Python object as a json-encoded string.
	"""
	impl = VARCHAR(1000)

	def process_bind_param(self, value, dialect):
		if value: # covers both "" and None
			if ':' not in value:
				value = security.generate_password_hash(value)

		return value

class PasswordValue(object):
	password = Column(Password)
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

class User(PasswordValue,ObjectRef):
	"""\
		Authorized users.
		Owner: Managing user; some sort of root for anon users.
		Parent: the site they first logged in on.
		SuperParent: for anon users, the site they're used with.
		"""
	__tablename__ = "users"
	_descr = D.User
	@classmethod
	def __declare_last__(cls):
		if not hasattr(cls,'site'):
			cls.site = cls.parent
		no_update(cls.username)
		no_update(cls.parent)
		# Uniqueness of username+site is handled in __init__,
		# which works because none of these may be updated
	        
	# A simple way to make 'username' read-only
	username = Column(Unicode(30), nullable=False)

	first_name = Column(Unicode(50), nullable=True)
	last_name = Column(Unicode(50), nullable=True)
	email = Column(Unicode(200), nullable=True)

	first_login = Column(DateTime, nullable=True) ## ever
	last_login = Column(DateTime, nullable=True)  ## the one before this session
	this_login = Column(DateTime, nullable=True)  ## this session start
	cur_login = Column(DateTime, nullable=True)   ## this session end

	feed_age = Column(Integer, nullable=False, default=10)
	feed_pass = Column(Unicode(30), nullable=True)
	feed_read = Column(DateTime, nullable=True)

	@classmethod
	def new_anon_user(cls,site=None):
		if site is None:
			site = request.site
		try:
			g = Group.q.get_by(name=ANON_USER_NAME,owner=site,parent=site)
		except NoData:
			g = Group(name=ANON_USER_NAME,owner=site,parent=site,superparent=site)
		u = User.q.filter_by(site=site).order_by(cls.cur_login).join(Member,Member.parent_id==User.id).filter(Member.owner==site).first()
		#u = cls.q.filter_by(username=ANON_USER_NAME, site=site).order_by(cls.cur_login).first()
		if u is not None and u.cur_login is not None and u.cur_login >= datetime.now()-timedelta(0,current_app.config.SESSION_COOKIE_AGE):
			u = None
		if u is None:
			u = cls(username=ANON_USER_NAME, site=site)
			Member(group=g,user=u)
			logger.info("New anon user {} for {}".format(u,site))
		else:
			logger.info("Recycling anon user {} for {}".format(u,site))
			from .tracking import Delete, TrackingObjectRef
			for c in u.all_children(want=None):
				if not isinstance(c,TrackingObjectRef):
					Delete(c,comment="ANON user cleanup")
			for c in u.all_superchildren(want=None):
				if not isinstance(c,TrackingObjectRef):
					Delete(c,comment="ANON user cleanup")
			for c in u.all_owned(want=None):
				if not isinstance(c,TrackingObjectRef):
					Delete(c,comment="ANON user cleanup")
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

	def __init__(self, username=ANON_USER_NAME, password=None, **kw):
		super(User,self).__init__(**kw)
		if username == ANON_USER_NAME:
			if password is None:
				password = ""
			assert password == ""
		else:
			## there may be more than one anon user
			try:
				User.q.get_by(parent=request.site, username=username)
			except (AttributeError,NoData):
				pass
			else:
				raise RuntimeError(u"User '%s' already exists in %s" % (username,request.site))
		self.username=username
		self.password=password

		db.flush()
		if self.parent is None:
			self.parent = request.site
		db.flush()
	
	@property
	def tracks(self):
		return Tracker.q.filter_by(owner=self).order_by(Desc(Tracker.timestamp))

	@property
	def trackers(self):
		return WantTracking.q.filter_by(owner=self)

	@property
	def anon(self):
		return self.username == ANON_USER_NAME

	@property
	def name(self):
		if self.first_name and self.last_name:
			return u"%s %s" % (self.first_name,self.last_name)
		elif self.first_name:
			return self.first_name
		elif self.last_name:
			return self.last_name
		elif self.username:
			return self.username
		else:
			return "·ANONYM·"

	def visits(self,obj):
		if getattr(obj,"_no_crumbs",False):
			return # no recursive or similar nonsense, please
		q = { "owner":self, "discr":obj.discr }
		try:
			s = Breadcrumb.q.get_by(parent=obj, **q)
		except NoData:
			Breadcrumb(self,obj)
		else:
			s.visit()
			if not s.superparent: # bugfix
				s.superparent = request.site
	
	def last_visited(self,cls=None):
		q = { "owner":self, "superparent":request.site }
		if cls:
			q["discr"] = cls.cls_discr()
		try:
			r = Breadcrumb.q.filter_by(**q).order_by(Breadcrumb.visited.desc()).first()
		except NoData:
			return None
		if r:
			return r.parent
	
	def all_visited(self, cls=None):
		q = { "owner":self, "superparent":request.site }
		if cls:
			q["discr"] = cls.cls_discr()
		return Breadcrumb.q.filter_by(**q).order_by(Breadcrumb.visited.desc())

	def is_verified(self, site=None):
		if site is None:
			site = request.site
		try:
			m = Member.q.get_by(user=self,group=site)
		except NoData:
			return False
		else:
			return not m.excluded

	def add_verified(self,v,site=None):
		anon = Group.q.get_by(name=ANON_USER_NAME,owner=site,parent=site)
		if site is None:
			site = request.site
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

	def can_do(user,obj, discr=None, new_discr=None, want=None):
		"""Recursively get the permission of this user for that (type of) object."""

		ru = getattr(request,"user",None)
		if obj is not request.site and \
		   ru and ru.can_admin(request.site, discr=request.site.classdiscr):
			if current_app.config.DEBUG_ACCESS:
				log_access("ADMIN",obj)
			return want if want and want < 0 else PERM_ADMIN

		if want>0 and want<=PERM_READ and obj.owner==user:
			if current_app.config.DEBUG_ACCESS:
				log_access("OWN",obj)
			return want

		if current_app.config.DEBUG_ACCESS:
			log_access("PERM", Discriminator.get(discr).name if discr else "-", Discriminator.get(new_discr) if new_discr else "-", (PERM_name(want) if want else "-")+":",obj,"FOR",user,"AT",request.site, u"⇒")

		pq = []
		if want is not None:
			if want >= PERM_NONE:
				pq.append(Permission.right >= want)
			else:
				pq.append(Permission.right == want)
		else:
			pq.append(Permission.right >= 0)
		if discr is None and want < 0:
			discr = obj

		if discr is not None:
			discr = Discriminator.get(discr)
			pq.append(Permission.for_discr == discr)

		if new_discr is not None:
			new_discr = Discriminator.get(new_discr)
			pq.append(Permission.new_discr == new_discr)

		inherited = False
		done = set()
		while obj:
			if obj in done:
				raise ValueError("Parent recursion on "+repr(obj))
			done.add(obj)
			if discr is None:
				ds = Permission.for_discr == None
			else:
				ds = or_(Permission.for_discr == None, Permission.for_discr == discr)

			p = Permission.q.filter(and_(or_(Permission.for_discr == None, Permission.for_discr == discr) if discr is not None else (Permission.for_discr == None),
			                             or_(Permission.inherit == inherited, Permission.inherit == None),
			                             Permission.parent == obj,
			                             or_(Permission.owner == u for u in user.groups), ## includes the user itself!
			                             *pq)).order_by(Permission.right.desc())
			if current_app.config.DEBUG_ACCESS:
				log_access("Checking",obj)
			p = p.first()
			if p is not None:
				if current_app.config.DEBUG_ACCESS:
					log_access(p)
				p = p.right
				return p

			inherited = True
			obj = obj.parent

		if current_app.config.DEBUG_ACCESS:
			log_access("NONE")
		return PERM_NONE

	def will_do(user,obj,discr=None, perm=PERM_NONE):
		if user.can_do(obj,discr) < perm:
			raise AuthError(obj,perm)

	def permit(user,obj, right, discr=None, inherit=None):
		discr = Discriminator.get(discr,obj).id
		p = list(Permission.q.filter(Permission.owner==u, Permission.parent==obj, Permission.for_discr==discr))
		
		if len(p) > 0:
			if inherit is None:
				while p:
					p.pop().delete()
				p = None
			elif len(p) > 1 and p[1].inherit == inherit:
				p = p[1]
			else:
				p = p[0]
				if p.inherit is None:
					p.inherit = not inherit
					p = None
				elif p.inherit != inherit:
					p = None

		if p:
			p.right = right
		else:
			p = Permission(user,obj,discr,right,inherit)

	def forbid(user,obj, discr=None, inherit=None):
		discr = Discriminator.get(discr,obj).id
		p = list(Permission.q.filter_by(owner=u, parent=obj, for_discr=discr))
		
		if not p:
			return
		if inherit is None:
			while p:
				db.delete(p.pop())
			return
		elif len(p) > 1 and p[1].inherit == inherit:
			p = p[1]
		else:
			p = p[0]

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

class Group(ObjectRef):
	"""
		A group of users. (Usually.)
		superparent: the site this group belongs to.
		owner: the managing user; the site, for system groups.

		owner+parent+name should be unique.
		"""
	__tablename__ = "groups"
	_descr = D.Group
	        
	name = Column(Unicode(30))

	def __init__(self,name,owner,site=None, **kw):
		super(Group,self).__init__(**kw)
		if self.superparent is None:
			self.superparent = site or owner
		self.owner = owner
		self.name = name
	
## Membership

class Member(ObjectRef):
	"""\
		Indicates membership of one object of another.
		owner: the individual who's the member.
		parent: the group

		TODO: parent=member, superparent=group, owner=whodunit
		"""
	__tablename__ = "groupmembers"
	_descr = D.Member
	_no_crumbs = True
	@classmethod
	def __declare_last__(cls):
		if not hasattr(cls,'user'):
			cls.user = cls.owner
		if not hasattr(cls,'group'):
			cls.group = cls.parent

	excluded = Column(Boolean, nullable=False,default=False)

	def __init__(self,user=None,group=None, **kw):
		super(Member,self).__init__(**kw)
		if self.owner is None:
			self.owner = user
		else:
			assert user is None
		if self.parent is None:
			self.parent = group
		else:
			assert group is None
		assert self.owner and self.parent

		self.excluded = False
		try: del self._memberships
		except AttributeError: pass

	@classmethod
	def add_to(cls,user,group,fail=False):
		"""Adds the user to the group"""
		try:
			M = cls.q.get_by(user=user,group=group)
		except NoData:
			M = cls(user=user,group=group)
		else:
			if fail:
				raise ManyDataExc("{} is already a member of {}".format(user,group))
		return m

	@classmethod
	def drop_from(cls,user,group,fail=False):
		"""Remove the user from the group"""
		try:
			M = cls.q.get_by(user=user,group=group)
		except NoData:
			if fail:
				raise ManyDataExc("{} is not a member of {}".format(user,group))
			return M
		else:
			return Delete(M)

	@property
	def data(self):
		return """\
User: %s
Group: %s
Member: %s
""" % (self.owner, self.parent, "Yes" if not self.excluded else "No")

	@property
	def as_str(self):
		p,s,o,d = self.pso
		if self._rec_str or not o or not p: return "‽"
		try:
			self._rec_str = True
			return u'%s%s in %s' % (unicode(o), " NOT" if self.excluded else "", unicode(p))
		finally:
			self._rec_str = False

Object.new_member_rule(Member, "owner","parent")

## Permissions

class Permission(ObjectRef):
	"""
		Permission checks: This user can do that to objects of yonder type.
		Owner: the enabled user/group
		Parent: the object to be accessed
		Superparent: site

		Inherit=False: only this object
		inherit=True : only to child objects
		inherit=NULL : both.

		discr: The object type to be modified
		new_discr: The type of object that may be added
		"""
	__tablename__ = "permissions"
	_descr = D.Permission
	_no_crumbs = True
	@classmethod
	def __declare_last__(cls):
		#check_unique(cls, 'owner parent ???')
		no_update(cls.parent)
		no_update(cls.owner)

	right = Column(Integer, nullable=False)
	inherit = Column(Boolean, nullable=True, doc="three-valued: False:this, True:descendants, None:Both")

	for_discr_id = Column("discr", Integer, ForeignKey(Discriminator.id), nullable=True)
	for_discr = relationship(Discriminator, primaryjoin=for_discr_id==Discriminator.id)

	new_discr_id = Column("new_discr", Integer, ForeignKey(Discriminator.id), nullable=True)
	new_discr = relationship(Discriminator, primaryjoin=new_discr_id==Discriminator.id)

	def __init__(self, user=None, obj=None, discr=None, right=None, inherit=None, new_discr=None, **kw):
		assert right is not None
		if discr is not None:
			discr = Discriminator.get(discr)
		super(Permission,self).__init__(**kw)
		self.for_discr = discr
		self.right = right
		self.inherit = inherit
		if self.owner is None:
			self.owner = user
		else:
			assert user is None
		if self.parent is None:
			self.parent = obj
		else:
			assert obj is None
		assert self.owner and self.parent

		if right == PERM_ADD:
			try: del user._can_add
			except AttributeError: pass
	
	@property
	def as_str(self):
		p,s,o,d = self.pso
		if self._rec_str or not o or not p: return "‽"
		try:
			self._rec_str = False
			return u'%s can %s %s %s %s %s' % (unicode(o),PERM[self.right],self.for_discr.name,unicode(p), "*" if self.inherit is None else "Y" if self.inherit else "N", self.new_discr.name if self.new_discr is not None else "-")
		finally:
			self._rec_str = False

	@property
	def data(self):
		p,s,o,d = self.pso
		return """\
User: %s
Object: %s
Object Type: %s
New Object Type: %s
Right: %s
Inherited: %s
""" % (o, p, \
		self.for_discr.name, \
		self.new_discr.name if self.new_discr is not None else "-", \
		self.right, \
		"*" if self.inherit is None else "Y" if self.inherit else "N")

for a,b in PERM.iteritems():
	def can_do_closure(a,b):
		def can_do(self, obj, discr=None, new_discr=None):
			if discr is None and obj is not None:
				discr = obj.discr
			if current_app.config.DEBUG_ACCESS:
				log_access("can_"+b+":", self,obj,discr,new_discr)
			if a > PERM_NONE:
				return self.can_do(obj, discr=discr, new_discr=new_discr, want=a) >= a
			else:
				return self.can_do(obj, discr=discr, new_discr=new_discr, want=a) == a
		can_do.__doc__ = "Check if this user/group/whatever can %s an object" % \
			(b.lower() if a > PERM_NONE else "do nothing with",)

		def will_do(self, obj, discr=None, new_discr=None):
			if current_app.config.DEBUG_ACCESS:
				log_access("will_"+b+":", self,obj,discr,new_discr)
			if not can_do(self, obj, discr=discr, new_discr=new_discr):
				raise AuthError(obj,a)

		return can_do,will_do
	
	c,d = can_do_closure(a,b)
	setattr(Object,'can_'+b.lower(), c)
	setattr(Object,'will_'+b.lower(), d)


