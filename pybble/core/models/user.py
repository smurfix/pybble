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

from flask import current_app,g,request
from flask.ext.security import UserMixin, RoleMixin

from werkzeug import security

from datetime import datetime,timedelta

from sqlalchemy import Integer, Unicode, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship,backref
from sqlalchemy.types import TypeDecorator, VARCHAR

from ... import ANON_USER_NAME
from ...utils import random_string, AuthError
from ...core import config
from ..db import Base, Column, db, NoData
from . import Object,ObjectRef, PERM,PERM_NONE, Discriminator
from .site import Site
from ._descr import D

import sys

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
#			site = current_app.site
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

class Password(TypeDecorator):
	"""Represents any Python object as a json-encoded string.
	"""
	impl = VARCHAR(1000)

	def process_bind_param(self, value, dialect):
		if value is not None:
			if ':' not in value:
				value = security.generate_password_hash(value)

		return value

class PasswordValue(object):
	password = Column(Password)
	def check_password(self, password):
		if ':' not in self.password:
			self.password = security.generate_password_hash(self.password)
		return security.check_password_hash(self.password,password)

class User(ObjectRef):
	"""\
		Authorized users.
		Owner: Managing user; some sort of root for anon users.
		Parent: the site they first logged in on.
		SuperParent: for anon users, the site they're used with.
		"""
	__tablename__ = "users"
	_descr = D.User
	        
	username = Column(Unicode(30), nullable=False)
	password = Column(Unicode(200), nullable=False)

	first_name = Column(Unicode(50), nullable=True)
	last_name = Column(Unicode(50), nullable=True)
	email = Column(Unicode(200), nullable=True)

	first_login = Column(DateTime, nullable=True)
	last_login = Column(DateTime, nullable=True)
	cur_login = Column(DateTime, nullable=True)

	feed_age = Column(Integer, nullable=False, default=10)
	feed_pass = Column(Unicode(30), nullable=True)
	feed_read = Column(DateTime, nullable=True)

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

	def __init__(self, username, password=None):
		super(User,self).__init__()
		self.username=username
		if username == ANON_USER_NAME:
			assert password is None
			password = ""
		elif password is None:
			password = unicode(random_string(9))
		self.password=password
		try:
			User.q.get_by(parent=request.site, username=username)
		except (AttributeError,NoData):
			pass
		else:
			raise RuntimeError(u"User '%s' already exists in %s" % (username,request.site))

		db.flush()
		self.parent = request.site
		if not self.anon:
			m = Member(self,request.site.anon_user)
		db.flush()
	
	@property
	def tracks(self):
		return db.store.find(Tracker, Tracker.owner_id==self.id).order_by(Desc(Tracker.timestamp))

	@property
	def trackers(self):
		return db.store.find(WantTracking, WantTracking.owner_id==self.id)

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
			return self.email

	def visits(self,obj):
		if getattr(obj,"_no_crumbs",False):
			return # no recursive or similar nonsense, please
		q = { "owner":self, "discr":obj.discriminator }
		try:
			s = Breadcrumb.q.get_by(parent=obj, **q)
		except NoData:
#			for b in db.filter_by(Breadcrumb,**q).order_by(Breadcrumb.visited)[10:]:
#				db.store.remove(b)
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
			r = db.filter_by(Breadcrumb, **q).order_by(Desc(Breadcrumb.visited)).first()
		except NoData:
			return None
		if r:
			return r.parent
	
	def all_visited(self, cls=None):
		q = { "owner":self, "superparent":request.site }
		if cls:
			q["discr"] = cls.cls_discr()
		return db.filter_by(Breadcrumb, **q).order_by(Desc(Breadcrumb.visited))

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
		if site is None:
			site = request.site
		try:
			m = Member.q.get_by(user_id=self.id,group_id=site.id)
		except NoData:
			if v:
				Member(user=self,group=site)
		else:
			if not v:
				db.store.remove(m)
	verified = property(is_verified,add_verified)
				
	@property
	def as_str__(self):
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
			if DEBUG_ACCESS:
				print("ADMIN",obj, file=sys.stderr)
			return want if want and want < 0 else PERM_ADMIN

		if want>0 and want<=PERM_READ and obj.owner==user:
			if DEBUG_ACCESS:
				print("OWN",obj, file=sys.stderr)
			return want

		if DEBUG_ACCESS:
			print("PERM", Discriminator.get(discr).name if discr else "-", Discriminator.get(new_discr) if new_discr else "-", (PERM_name(want) if want else "-")+":",obj,"FOR",user,"AT",request.site, u"⇒", file=sys.stderr)

		pq = []
		if want is not None:
			if want >= PERM_NONE:
				pq.append(Permission.right >= want)
			else:
				pq.append(Permission.right == want)
		else:
			pq.append(Permission.right >= 0)
		if discr is None and obj and want < 0:
			discr = obj.discriminator

		if discr is not None:
			if isinstance(discr,Discriminator):
				discr = discr.id
			elif isinstance(discr,type) and issubclass(discr,Object):
				discr = discr.cls_discr()
			elif isinstance(discr,Object):
				discr = discr.classdiscr
			else:
				discr = Discriminator.get(discr).id
			pq.append(Permission.for_discr == discr)

		if new_discr is not None:
			if isinstance(new_discr,Discriminator):
				new_discr = new_discr.id
			elif isinstance(new_discr,type) and issubclass(new_discr,Object):
				new_discr = new_discr.cls_discr()
			elif isinstance(new_discr,Object):
				discr = new_discr.classdiscr
			else:
				new_discr = Discriminator.get(new_discr).id
			pq.append(Permission.new_discr == new_discr)

		no_inh = True
		done = set()
		while obj:
			if obj in done:
				raise ValueError("Parent recursion on "+repr(obj))
			done.add(obj)

			p = db.store.find(Permission, And(Or(Permission.inherit != no_inh, Permission.inherit == None), Or(*(Permission.owner_id == u.id for u in user.groups)), Permission.parent_id == obj.id, *pq)).order_by(Desc(Permission.right))
			if DEBUG_ACCESS:
				print("Checking",obj, file=sys.stderr)
			p = p.first()
			if p is not None:
				if DEBUG_ACCESS:
					print(p, file=sys.stderr)
				p = p.right
				return p

			no_inh = False
			obj = obj.parent

		if DEBUG_ACCESS:
			print("NONE", file=sys.stderr)
		return PERM_NONE

	def will_do(user,obj,discr=None, perm=PERM_NONE):
		if user.can_do(obj,discr) < perm:
			raise AuthError(obj,perm)

	def permit(user,obj, right, discr=None, inherit=None):
		discr = Discriminator.get(discr,obj).id
		p = list(db.store.find(Permission, And(Permission.owner==u, Permission.parent==obj, Permission.for_discr==discr)))
		
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
		p = list(db.store_find(Permission, And(Permission.owner==u,Permission.parent==obj,Permission.for_discr==discr)))
		
		if p:
			if inherit is None:
				while p:
					db.store.remove(p.pop())
				return
			elif len(p) > 1 and p[1].inherit == inherit:
				p = p[1]
			else:
				p = p[0]
			p.delete()

	@property
	def recent_tracks(self):
		latest = datetime.utcnow() - timedelta(self.feed_age,0)
#		return db.filter_by(UserTracker,owner=self)\
#		                    .filter(UserTracker.tracker.timestamp > datetime.utcnow() - timedelta(self.feed_age,0))\
#		                    .order_by(UserTracker.id.desc())
		for obj in db.store.find(UserTracker, UserTracker.owner_id == self.id).order_by(Desc(UserTracker.id)):
			if obj.parent.timestamp < latest:
				return
			yield obj

	@property
	def has_trackers(self):
		return db.store.find(WantTracking, WantTracking.owner == self).count()

class GroupRef(ObjectRef):
	"""
		A group of users. (Usually.)
		superparent: the site this group belongs to.
		owner: the managing user; the site, for system groups.
		"""
	__tablename__ = "groups"
	_descr = D.GroupRef
	        
	name = Column(Unicode(30))

	def __init__(self,name,owner,site=None):
		super(Group,self).__init__()
		self.superparent = site or owner
		self.owner = owner
		self.name = name
	
def named_group(owner, name):
	"""Return the site-specific group with that name."""
	return Group.q.get_by(name=name, owner=site)

class Member(ObjectRef):
	"""\
		Indicates membership of one object of another.
		owner: the individual who's the member.
		parent: the group
		"""
	__tablename__ = "groupmembers"
	_descr = D.Member
	_no_crumbs = True
	@classmethod
	def __declare_last__(cls):
		cls.user = cls.owner
		cls.group = cls.parent

	excluded = Column(Boolean, nullable=False,default=False)

	def __init__(self,user,group):
		super(Member,self).__init__()
		self.owner = user
		self.parent = group
		self.excluded = False
		try: del self._memberships
		except AttributeError: pass

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

	right = Column(Integer, nullable=False)
	inherit = Column(Boolean, nullable=True)

	for_discr_id = Column("discr", Integer, ForeignKey(Discriminator.id), nullable=False)
	for_discr = relationship(Discriminator, primaryjoin=for_discr_id==Discriminator.id)

	new_discr_id = Column("new_discr", Integer, ForeignKey(Discriminator.id), nullable=True)
	new_discr = relationship(Discriminator, primaryjoin=new_discr_id==Discriminator.id)

	def __init__(self, user, obj, discr, right, inherit=None, new_discr=None):
		discr = Discriminator.get(discr,obj)
		super(Permission,self).__init__()
		self.for_discr = discr
		self.right = right
		self.inherit = inherit
		self.owner = user
		self.parent = obj

		if right == PERM_ADD:
			try: del user._can_add
			except AttributeError: pass
	
	@property
	def as_str(self):
		p,s,o,d = self.pso
		if self._rec_str or not o or not p: return "‽"
		try:
			self._rec_str = False
			return u'%s can %s %s %s %s %s' % (unicode(o),PERM[self.right],self.for_discr.name,unicode(p), "*" if self.inherit is None else "Y" if self.inherit else "N", Discriminator.q.get_by(id=self.new_discr).name if self.new_discr is not None else "-")
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
			if DEBUG_ACCESS:
				print("can_"+b+":", self,obj,discr,new_discr, file=sys.stderr)
			if a > PERM_NONE:
				return self.can_do(obj, discr=discr, new_discr=new_discr, want=a) >= a
			else:
				return self.can_do(obj, discr=discr, new_discr=new_discr, want=a) == a
		can_do.__doc__ = "Check if this user/group/whatever can %s an object" % \
			(b.lower() if a > PERM_NONE else "do nothing with",)

		def will_do(self, obj, discr=None, new_discr=None):
			if DEBUG_ACCESS:
				print("will_"+b+":", self,obj,discr,new_discr, file=sys.stderr)
			if not can_do(self, obj, discr=discr, new_discr=new_discr):
				raise AuthError(obj,a)

		return can_do,will_do
	
	c,d = can_do_closure(a,b)
	setattr(Object,'can_'+b.lower(), c)
	setattr(Object,'will_'+b.lower(), d)

