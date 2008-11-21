# -*- coding: utf-8 -*-

from datetime import datetime
from sqlalchemy import Table, Column, String, Unicode, Boolean, DateTime, Integer, ForeignKey, \
	UniqueConstraint, Text
from sqlalchemy.orm import relation,backref
from pybble.utils import url_for, random_string
from pybble.database import db
from datetime import datetime
from sqlalchemy.databases.mysql import MSTinyInteger as TinyInteger
from sqlalchemy.databases.mysql import MSTimeStamp as TimeStamp
from sqlalchemy.sql import and_, or_, not_
from pybble.decorators import add_to


class Discriminator(db.Base):
	"""Discriminator for Object"""
	__tablename__ = "discriminator"
	__table_args__ = {'useexisting': True}
	q = db.session.query_property(db.Query)
	id = Column(TinyInteger(1), primary_key=True)
	name = Column(String(30), nullable=False, unique=True)

	def __init__(self, cls):
		self.id = obj_discr(cls)
		self.name = cls.__name__


class Object(db.Base):
	"""The base type of all pointed-to objects"""
	__tablename__ = "obj"
	__table_args__ = {'useexisting': True}
	q = db.session.query_property(db.Query)

	id = Column(Integer(20), primary_key=True)

	discriminator = Column(TinyInteger, ForeignKey('discriminator.id',name="obj_discr"))
	__mapper_args__ = {'polymorphic_on': discriminator}

	owner_id = Column(Integer(20),ForeignKey('obj.id',name="obj_owner"))        # creating object/user
	parent_id = Column(Integer(20),ForeignKey('obj.id',name="obj_parent"))      # direct ancestor (replied-to comment)
	superparent_id = Column(Integer(20),ForeignKey('obj.id',name="obj_super"))  # indirect ancestor (replied-to wiki page)

	#all_children = relation('Object', backref=backref("superparent", remote_side="Object.id")) 

	def __unicode__(self):
		return u'‹%s %d›' % (self.__class__.__name__,self.id)
	def __str__(self):
		return '<%s %d>' % (self.__class__.__name__,self.id)
	__repr__ = __str__

Object.owner = relation(Object, remote_side=Object.id, primaryjoin=(Object.owner_id==Object.id))
Object.parent = relation(Object, remote_side=Object.id, primaryjoin=(Object.parent_id==Object.id))
Object.superparent = relation(Object, remote_side=Object.id, primaryjoin=(Object.superparent_id==Object.id))

Object.children = relation(Object, remote_side=Object.parent_id, primaryjoin=(Object.id==Object.parent_id)) 

def obj_class(id):
	"""Given a discriminator ID, return the referred object's class."""
	return Object.__mapper__.polymorphic_map[id].class_

def obj_discr(cls):
	"""Given a class, return the objects' discriminator."""
	return cls.__mapper__.polymorphic_identity

class URL(Object):
	"""Test table which links to external URLs."""
	__tablename__ = "urls"
	__table_args__ = {'useexisting': True}
	__mapper_args__ = {'polymorphic_identity': 1}
	q = db.session.query_property(db.Query)
	id = Column(Integer, ForeignKey('obj.id',name="URL_id"), primary_key=True,autoincrement=False)
	        
	uid = Column(Unicode(140), nullable=False, unique=True)
	target = Column(Unicode(500), nullable=False)
	added = Column(DateTime, nullable=False)
	public = Column(Boolean, nullable=False)

	def __init__(self, target, public=True, uid=None, added=None):
		self.target = target
		self.public = public
		self.added = added or datetime.utcnow()
		if not uid:
			while 1:
				uid = get_random_uid()
				if not URL.q.get(uid):
					break
		self.uid = uid

	@property
	def short_url(self):
		return url_for('link', uid=self.uid, _external=True)

	def __repr__(self):
		return '<URL %r>' % self.uid

	def __unicode__(self):
		return u'‹URL %r›' % self.uid

class UserQuery(db.Query):
	pass # defined below

class User(Object):
	"""\
		Authorized users.
		Owner: Managing user; some sort of root for anon users.
		SuperParent: for anon users, the site they're used with.
		"""
	__tablename__ = "users"
	__table_args__ = {'useexisting': True}
	__mapper_args__ = {'polymorphic_identity': 2}
	q = db.session.query_property(UserQuery)
	id = Column(Integer, ForeignKey('obj.id',name="user_id"), primary_key=True,autoincrement=False)
	        
	username = Column(Unicode(30), nullable=False)
	first_name = Column(Unicode(30))
	last_name = Column(Unicode(30))
	email = Column(String(100))
	password = Column(String(30), nullable=False)
	verified = Column(Boolean, nullable=False)
	first_login = Column(DateTime, nullable=False)
	last_login = Column(DateTime)

	def __init__(self, username, password=None):
		self.username=username
		if password is None:
			password = random_string(9)
		self.password=password
		self.first_login = datetime.utcnow()
	
	@property
	def anon(self):
		return self.password == ""
	
	def __unicode__(self):
		if self.username != "":
			return u"‹User %d:%s›" % (self.id,self.username)

		try:
			return u"‹User %d:anon @%s›" % (self.id, self.superparent.domain)
		except Exception:
			return u"‹User %d:anon @ ???›" % (self.id,)

@add_to(UserQuery)
def get_anonymous_user(self, site):
	return self.get_one(and_(User.username=="", User.password=="",User.superparent==site))

#class Group(Object):
#	"""A group of users. (Usually.)"""
#	__tablename__ = "groups"
#	__table_args__ = {'useexisting': True}
#	__mapper_args__ = {'polymorphic_identity': 4}
#	q = db.session.query_property(db.Query)
#	id = Column(Integer, ForeignKey('obj.id',name="Group_id"), primary_key=True,autoincrement=False)
#	        
#	name = Column(Unicode(30))
#	
#class Member(db.Base):
#	__tablename__ = "groupmembers"
#	q = db.session.query_property(db.Query)
#	id = Column(Integer, primary_key=True)
#
#	user_id = Column(Integer(20),ForeignKey(Obj.id,name="member_user"))    # one member
#	group_id = Column(Integer(20),ForeignKey(Obj.id,name="member_group"))   # membership group
#	
PERM_LIST=1
PERM_READ=2
PERM_WRITE=3
PERM_ADMIN=4

class Permission(db.Base):
	"""Permission checks"""
	__tablename__ = "permissions"
	__table_args__ = {'useexisting': True}
	q = db.session.query_property(db.Query)
	id = Column(Integer(20), primary_key=True)

	user_id = Column(Integer(20),ForeignKey(Object.id,name="permission_user"), nullable=False)        # acting user/group
	obj_id = Column(Integer(20),ForeignKey(Object.id,name="permission_obj"), nullable=False)         # affected object
	right = Column(Integer(1))

class Site(Object):
	"""A web domain."""
	__tablename__ = "sites"
	__table_args__ = {'useexisting': True}
	__mapper_args__ = {'polymorphic_identity': 5}
	q = db.session.query_property(db.Query)
	id = Column(Integer, ForeignKey('obj.id',name="site_id"), primary_key=True,autoincrement=False)

	domain = Column(Unicode(100), nullable=False, unique=True)
	name = Column(Unicode(50), nullable=False, unique=True)

	def __init__(self,domain,name=None):
		if name is None:
			name="Here be "+domain
		self.domain=domain
		self.name=name

	def __unicode__(self):
		return u"‹Site ‚%s‘ @ %s›" % (self.name, self.domain)

site_users = Table('site_users', db.Metadata,
	Column('site_id', Integer, ForeignKey(Site.id,name="site_users_site"), nullable=False),
	Column('user_id', Integer, ForeignKey(User.id,name="site_users_user"), nullable=False),
	UniqueConstraint('site_id', 'user_id'))

Site.users = relation(User, secondary=site_users, backref='sites',
	primaryjoin=(Site.id==site_users.c.site_id),
	secondaryjoin=(site_users.c.user_id==User.id))

class Template(Object):
	"""A template for rendering."""
	__tablename__ = "templates"
	__table_args__ = ({'useexisting': True})
	__mapper_args__ = {'polymorphic_identity': 6}
	q = db.session.query_property(db.Query)
	id = Column(Integer, ForeignKey('obj.id',name="template_id"), primary_key=True,autoincrement=False)
	name = Column(String(50), nullable=True)
	data = Column(Text)
	modified = Column(TimeStamp)

	def __init__(self, name, data):
		self.name = name
		self.data = data

	def __repr__(self):
		return "'<%s:%d>'" % (self.__class__.__name__,self.id)

class TemplateMatch(db.Base):
	"""Associate a template to an object."""
	__tablename__ = "template_match"
	__table_args__ = ({'useexisting': True})
	q = db.session.query_property(db.Query)

	id = Column(Integer(20), primary_key=True)
	obj_id = Column('obj_id', Integer, ForeignKey('obj.id',name="obj_templates_obj"), nullable=False)
	template_id = Column('template_id', Integer, ForeignKey('templates.id',name="obj_templates_template"), nullable=False)
	discriminator = Column(TinyInteger, ForeignKey('discriminator.id',name="templatematch_discr"))
	type = Column(TinyInteger(1), nullable=False)

	def __init__(self, obj,discriminator,type, data):
		t = Template(None,data)
		self.obj = obj
		self.template = t
		self.discriminator = discriminator
		self.type = type

TemplateMatch.obj = relation(Object, remote_side="Object.id", primaryjoin=(TemplateMatch.obj_id==Object.id))
TemplateMatch.template = relation(Template, remote_side=Template.id, foreign_keys=(TemplateMatch.template_id), primaryjoin=(TemplateMatch.template_id==Template.id))

TM_TYPE_PAGE=1
TM_TYPE_LIST=2
TM_TYPE_STRING=3

