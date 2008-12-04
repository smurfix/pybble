# -*- coding: utf-8 -*-

from datetime import datetime,timedelta
from sqlalchemy import Table, Column, String, Unicode, Boolean, DateTime, Integer, ForeignKey, \
	UniqueConstraint, Text
from sqlalchemy.orm import relation,backref
from sqlalchemy.sql import select,func
from pybble.utils import random_string, current_request, AuthError
from pybble.database import db, NoResult
from sqlalchemy.databases.mysql import MSTinyInteger as TinyInteger
from sqlalchemy.databases.mysql import MSTimeStamp as TimeStamp
from sqlalchemy.sql import and_, or_, not_
from pybble.decorators import add_to
from werkzeug import import_string
import settings

try:
    from hashlib import md5
except ImportError:
	from md5 import md5


# Template detail levels
TM_DETAIL = {1:"Page", 2:"Subpage", 3:"String"}
for _x,_y in TM_DETAIL.items():
	globals()["TM_DETAIL_"+_y.upper()] = _x

def TM_DETAIL_name(id):
	return TM_DETAIL[int(id)]


# Permission levels

PERM = {0:"None", 1:"List", 2:"Read", 3:"Add", 4:"Write", 5:"Delete", 9:"Admin"}
for _x,_y in PERM.items():
	globals()["PERM_"+_y.upper()] = _x

def PERM_name(id):
	return PERM[int(id)]


class DbRepr(object):
	def __unicode__(self):
		if getattr(self,"name",None):
			return u'‹%s %s:%s›' % (self.__class__.__name__, self.id, self.name)
		else:
			return u'‹%s %s›' % (self.__class__.__name__, self.id)
	def __str__(self):
		if getattr(self,"name",None):
			return '<%s %s:%s>' % (self.__class__.__name__, self.id, self.name)
		else:
			return '<%s %s>' % (self.__class__.__name__, self.id)
	__repr__ = __str__


class Discriminator(db.Base,DbRepr):
	"""Discriminator for Object"""
	__tablename__ = "discriminator"
	__table_args__ = {'useexisting': True}
	q = db.session.query_property(db.Query)
	id = Column(TinyInteger(1), primary_key=True)
	name = Column(String(30), nullable=False, unique=True)

	def __init__(self, cls):
		self.id = cls.__mapper__.polymorphic_identity
		self.name = cls.__name__
	
	@staticmethod
	def get(discr, obj=None):
		if isinstance(discr, Discriminator):
			return discr
		elif isinstance(discr, basestring):
			return Discriminator.q.get_by(name=discr)
		elif discr is None:
			return Discriminator.q.get_by(id=obj.discriminator)
		else:
			assert isinstance(discr, int)
			return Discriminator.q.get_by(id=discr)

class Object(db.Base,DbRepr):
	"""The base type of all pointed-to objects"""
	__tablename__ = "obj"
	__table_args__ = {'useexisting': True}
	q = db.session.query_property(db.Query)

	id = Column(Integer(20), primary_key=True)

	# This is intentionally not a reference to the Discriminator table
	discriminator = Column(TinyInteger, ForeignKey('discriminator.id',name="obj_discr"))
	__mapper_args__ = {'polymorphic_on': discriminator}

	owner_id = Column(Integer(20),ForeignKey('obj.id',name="obj_owner"))        # creating object/user
	parent_id = Column(Integer(20),ForeignKey('obj.id',name="obj_parent"))      # direct ancestor (replied-to comment)
	superparent_id = Column(Integer(20),ForeignKey('obj.id',name="obj_super"))  # indirect ancestor (replied-to wiki page)

	#all_children = relation('Object', backref=backref("superparent", remote_side=Object.id)) 

	@property
	def has_children(self, discr=None):
		if discr:
			n = len(self.children.filter_by(discriminator=discr))
		else:
			n = len(self.children)
		return n

	@property
	def has_superchildren(self, discr=None):
		if discr:
			n = len(self.superchildren.filter_by(discriminator=discr))
		else:
			n = len(self.superchildren)
		return n

	@property
	def has_slaves(self, discr=None):
		if discr:
			n = len(self.slaves.filter_by(discriminator=discr))
		else:
			n = len(self.slaves)
		return n

	@property
	def discr_children(self):
		s = select([Object.discriminator, func.count(Object.id)], Object.parent_id==self.id).\
		    group_by(Object.discriminator).order_by(Object.discriminator)
		for discr,num in db.engine.execute(s):
			c = obj_class(discr)
			yield c, c.q.filter_by(parent=self), num

	@property
	def discr_superchildren(self):
		s = select([Object.discriminator, func.count(Object.id)], Object.superparent_id==self.id).\
		    group_by(Object.discriminator).order_by(Object.discriminator)
		for discr,num in db.engine.execute(s):
			c = obj_class(discr)
			yield c, c.q.filter_by(superparent=self), num

	@property
	def discr_slaves(self):
		s = select([Object.discriminator, func.count(Object.id)], Object.owner_id==self.id).\
		    group_by(Object.discriminator).order_by(Object.discriminator)
		for discr,num in db.engine.execute(s):
			c = obj_class(discr)
			yield c, c.q.filter_by(owner=self), num

	@property
	def has_templates(self, discriminator=None):
		if discriminator:
			n = len(self.templates.filter_by(discriminator=discriminator))
		else:
			n = len(self.templates)
		return n

	@property
	def has_memberships(self):
		return self.memberships.count()

	@property
	def has_permissions(self):
		return self.permissions.count()

	@property
	def permissions(self):
		return Permission.q.filter_by(parent_id=self.id)

	@property
	def classname(self):
		return self.__class__.__name__

	@property
	def classdiscr(self):
		return self.__class__.__mapper__.polymorphic_identity

	@classmethod
	def cls_name(cls):
		return cls.__name__

	@classmethod
	def cls_discr(cls):
		return cls.__mapper__.polymorphic_identity

	def oid(self):
		"""
			Return a crypto ID of an object.
			This is done so that simply enumerating object IDs off the web pages wont work.
			"""
		return "%s.%d.%d.%s" % (self.classname, self.discriminator, self.id, 
		                        md5(self.__class__.__name__ + str(self.id) + settings.SECRET_KEY)\
		                            .digest().encode('base64').strip('\n =')[:10].replace("+","/-").replace("/","_"))

	def get_template(self, detail=TM_DETAIL_PAGE):
		"""Return this object's template at a given detail level"""
		discr = self.discriminator

		print "Search template at",self,"level",detail
		no_inherit = True
		obj = self
		while obj:
			try:
				t = TemplateMatch.q.filter(or_(TemplateMatch.inherit != no_inherit, TemplateMatch.inherit == None)).\
									get_by(obj=obj, discr=discr, detail=detail).template
			except NoResult:
				print "... not found for now"
				pass
			else:
				print "... found",t
				return t

			if obj is current_request.site:
				break
			elif obj.parent:
				obj = obj.parent
			elif obj.superparent:
				obj = obj.superparent
			else:
				obj = current_request.site

			print "... retry at",obj
			no_inherit = False

		print "... not found"
		raise NoResult("Template %d for %s" % (detail,str(self)))


	def uptree(self):
		while self:
			yield self
			self = self.parent

Object.owner = relation(Object, uselist=False, remote_side=Object.id, primaryjoin=(Object.owner_id==Object.id))
Object.parent = relation(Object, uselist=False, remote_side=Object.id, primaryjoin=(Object.parent_id==Object.id))
Object.superparent = relation(Object, uselist=False, remote_side=Object.id, primaryjoin=(Object.superparent_id==Object.id))

Object.children = relation(Object, remote_side=Object.parent_id, primaryjoin=(Object.id==Object.parent_id)) 
Object.superchildren = relation(Object, remote_side=Object.superparent_id, primaryjoin=(Object.id==Object.superparent_id)) 
Object.slaves = relation(Object, remote_side=Object.owner_id, primaryjoin=(Object.id==Object.owner_id)) 

def obj_class(id):
	"""Given a discriminator ID, return the referred object's class."""
	return Object.__mapper__.polymorphic_map[int(id)].class_

def obj_get(oid):
	"""Given an object ID, return the object"""
	cls,cid,id,hash = oid.split(".")
	cls = obj_class(int(cid))
	obj = cls.q.get_by(id=int(id))
	if oid != obj.oid():
		raise ValueError("This object does not exist: " % (oid,))
	return obj

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

	def visited(self,obj):
		if obj.__class__ is Breadcrumb:
			return # no recursive nonsense, please
		q = Breadcrumb.q.filter_by(owner=self,discr=obj.discriminator)
		try:
			s = q.get_by(parent=obj)
		except NoResult:
			for b in q.order_by(Breadcrumb.visited)[10:]:
				db.session.delete(b)
			b = Breadcrumb(self,obj)
			db.session.add(b)
		else:
			s.visited = datetime.utcnow()
	
	def last_visited(self,cls):
		try:
			return Breadcrumb.q.filter_by(owner=self,discr=cls.cls_discr()) \
			                   .order_by(Breadcrumb.visited.desc()) \
			                   .first().parent
		except NoResult:
			return None
	
	def all_visited(self, cls=None):
		if cls:
			return Breadcrumb.q.filter_by(owner=self,discr=cls.cls_discr()).order_by(Breadcrumb.visited.desc())
		else:
			return Breadcrumb.q.filter_by(owner=self).order_by(Breadcrumb.visited.desc())

	def _get_verified(self):
		
		g = current_request.site
		try:
			m = Member.q.get_by(user=self,group=g)
		except NoResult:
			return False
		else:
			return not m.excluded
	def _set_verified(self,v):
		g = current_request.site
		try:
			m = Member.q.get_by(user=self,group=g)
		except NoResult:
			if v:
				db.session.add(Member(user=self,group=g))
		else:
			if not v:
				db.session.delete(m)
	verified = property(_get_verified,_set_verified)
				
	def __unicode__(self):
		if self.username != "":
			return u"‹User %d:%s›" % (self.id,self.username)

		try:
			return u"‹User %d:anon @%s›" % (self.id, self.superparent.domain)
		except Exception:
			return u"‹User %d:anon @ ???›" % (self.id,)


	def can_do(user,obj,discr=None, want=None):
		"""Recursively get the permission of this user for that (type of) object."""
		if obj is not current_request.site and current_request.user.can_admin(current_request.site):
			return PERM_ADMIN

		done = {}
		discr = Discriminator.get(discr,obj).id

		if want:
			pq = Permission.q.filter_by(p.right == want)
		else:
			pq = Permission.q

		ul = [user]
		ulq = [user]
		while ulq:
			u = ulq.pop(0)
			for m in Member.q.filter_by(user=u):
				g = m.group
				if not m.excluded and g not in ul:
					ul.append(g)
					ulq.append(g)

		no_inh = True

		while obj:
			if obj.id in done:
				raise ValueError("Parent recursion on "+repr(obj))
			done[obj.id]=1

			for u in ul:
				try:
					p = Permission.q.filter(or_(Permission.inherit != no_inh, Permission.inherit == None)).filter_by(owner=u,parent=obj,discr=discr).one()
				except NoResult:
					pass
				else:
					return p.right

			no_inh = False
			obj = obj.parent

		return PERM_NONE

	def will_do(user,obj,discr=None, perm=PERM_NONE):
		if user.can_do(obj,discr) < perm:
			raise AuthError(obj,perm)

	def permit(user,obj, right, discr=None, inherit=None):
		discr = Discriminator.get(discr,obj).id
		p = Permission.q.filter_by(owner=u,parent=obj,discr=discr).all()
		
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
			db.session.add(p)

	def forbid(user,obj, discr=None, inherit=None):
		discr = Discriminator.get(discr,obj).id
		p = Permission.q.filter_by(owner=u,parent=obj,discr=discr).all()
		
		if len(p) > 0:
			if inherit is None:
				while p:
					db.session.delete(p.pop())
				return
			elif len(p) > 1 and p[1].inherit == inherit:
				p = p[1]
			else:
				p = p[0]
			p.delete()

@add_to(UserQuery)
def get_anonymous_user(self, site):
	return self.get_one(and_(User.username=="", User.password=="",User.superparent==site))

class Group(Object):
	"""
		A group of users. (Usually.)
		superparent: the site this group belongs to.
		owner: the managing user; the site, for system groups.
		"""
	__tablename__ = "groups"
	__table_args__ = {'useexisting': True}
	__mapper_args__ = {'polymorphic_identity': 4}
	q = db.session.query_property(db.Query)
	id = Column(Integer, ForeignKey('obj.id',name="Group_id"), primary_key=True,autoincrement=False)
	        
	name = Column(Unicode(30))

	def __init__(self,name,owner,site=None):
		self.superparent = site or owner
		self.owner = owner
		self.name = name
	
def named_group(owner, name):
	"""Return the site-specific group with that name."""
	return Group.q.get_by(name==name, owner==site)

class Member(Object,DbRepr):
	"""\
		Indicates membership of one object of another.
		owner: the individual who's the member.
		parent: the group
		"""
	__tablename__ = "groupmembers"
	__table_args__ = {'useexisting': True}
	__mapper_args__ = {'polymorphic_identity': 13}
	q = db.session.query_property(db.Query)
	id = Column(Integer, ForeignKey('obj.id',name="Group_id"), primary_key=True,autoincrement=False)

	excluded = Column(Boolean, nullable=False)

	def __init__(self,user,group):
		self.owner = user
		self.parent = group
		self.excluded = False

	def __unicode__(self):
		if not self.owner or not self.parent: return super(Member,self).__unicode__()
		return u'‹%s %s: %s%s in %s›' % (self.__class__.__name__, self.id, unicode(self.owner), " NOT" if self.excluded else "", unicode(self.parent))
	def __str__(self):
		if not self.owner or not self.parent: return super(Member,self).__str__()
		return '<%s %s: %s%s in %s>' % (self.__class__.__name__, self.id, str(self.owner), " NOT" if self.excluded else "", str(self.parent))
	def __repr__(self):
		if not self.owner or not self.parent: return super(Member,self).__repr__()
		return self.__str__()

Member.user = relation(Object, remote_side=Object.id, uselist=False, primaryjoin=(Object.owner_id==Object.id))
Member.group = relation(Object, remote_side=Object.id, uselist=False, primaryjoin=(Object.parent_id==Object.id))

Object.memberships = relation(Member, remote_side=Member.owner_id, uselist=True, primaryjoin=(Member.owner_id==Object.id)) 

class Permission(Object):
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
	__table_args__ = {'useexisting': True}
	__mapper_args__ = {'polymorphic_identity': 10}
	q = db.session.query_property(db.Query)
	id = Column(Integer, ForeignKey('obj.id',name="Group_id"), primary_key=True,autoincrement=False)

	right = Column(Integer(1), nullable=False)
	inherit = Column(Boolean, nullable=True)
	discr = Column(TinyInteger, ForeignKey('discriminator.id',name="obj_discr"), nullable=False)
	new_discr = Column(TinyInteger, ForeignKey('discriminator.id',name="obj_new_discr"), nullable=True)

	def __init__(self, user, obj, discr, right, inherit=None, new_discr=None):
		self.owner = user
		self.parent = obj
		self.discr = Discriminator.get(discr,obj).id
		self.right = right
		self.inherit = inherit
	
	def __unicode__(self):
		if not self.owner or not self.parent: return super(Permission,self).__unicode__()
		return u'‹%s %s: %s can %s %s %s %s %s›' % (self.__class__.__name__, self.id, unicode(self.owner),PERM[self.right],Discriminator.q.get_by(id=self.discr).name,unicode(self.parent), "*" if self.inherit is None else "Y" if self.inherit else "N", Discriminator.q.get_by(id=self.new_discr).name if self.new_discr is not None else "-")
	def __str__(self):
		if not self.owner or not self.parent: return super(Permission,self).__str__()
		return '<%s %s: %s can %s %s %s %s %s>' % (self.__class__.__name__, self.id, str(self.owner),PERM[self.right],Discriminator.q.get_by(id=self.discr).name,str(self.parent), "*" if self.inherit is None else "Y" if self.inherit else "N", Discriminator.q.get_by(id=self.new_discr).name if self.new_discr is not None else "-")
	def __repr__(self):
		if not self.owner or not self.parent: return super(Permission,self).__repr__()
		return self.__str__()


for a,b in PERM.iteritems():
	def can_do_closure(a,b):
		def can_do(self, obj, discr = None):
			if a > PERM_NONE:
				return self.can_do(obj, discr) >= a
			else:
				return self.can_do(obj, discr, a) == a
		can_do.__doc__ = "Check if this user/group/whatever can %s an object" % \
			(b.lower() if a > PERM_NONE else "do nothing with",)

		def will_do(self, obj, discr = None):
			if not can_do(self, obj, discr):
				raise AuthError(obj,a)

		return can_do,will_do
	c,d = can_do_closure(a,b)
	setattr(Object,'can_'+b.lower(), c)
	setattr(Object,'will_'+b.lower(), d)


class Site(Object):
	"""A web domain. 'owner' is set to the domain's superuser."""
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
	"""
		A template for rendering.
		superparent: Site the template applies to.
		owner: user who created the template.
		"""
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


class TemplateMatch(Object):
	"""
		Associate a template to an object.
		Parent: The object which the template is for.
		Owner: The template.
		"""
	__tablename__ = "template_match"
	__table_args__ = ({'useexisting': True})
	__mapper_args__ = {'polymorphic_identity': 12}
	q = db.session.query_property(db.Query)
	id = Column(Integer, ForeignKey('obj.id',name="Group_id"), primary_key=True,autoincrement=False)

	discr = Column(TinyInteger, ForeignKey('discriminator.id',name="templatematch_discr"), nullable=False)
	detail = Column(TinyInteger(1), nullable=False)
	inherit = Column(Boolean, nullable=True)

	def __init__(self, obj,discr,detail, data):
		if isinstance(data,Template):
			t = data
		else:
			t = Template(None,data)
		self.parent = obj
		self.owner = t
		self.discr = Discriminator.get(discr,obj).id
		self.detail = detail
	
	def __unicode__(self):
		if not self.owner or not self.parent: return super(TemplateMatch,self).__unicode__()
		return u'‹%s %s: %s for %s %s %s %s›' % (self.__class__.__name__, self.id, unicode(self.owner),TM_DETAIL[self.detail],Discriminator.q.get_by(id=self.discr).name,unicode(self.parent), "*" if self.inherit is None else "Y" if self.inherit else "N")
	def __str__(self):
		if not self.owner or not self.parent: return super(TemplateMatch,self).__str__()
		return '<%s %s: %s for %s %s %s %s>' % (self.__class__.__name__, self.id, str(self.owner),TM_DETAIL[self.detail],Discriminator.q.get_by(id=self.discr).name,str(self.parent), "*" if self.inherit is None else "Y" if self.inherit else "N")
	def __repr__(self):
		if not self.owner or not self.parent: return super(TemplateMatch,self).__repr__()
		return self.__str__()

TemplateMatch.obj = relation(Object, remote_side=Object.id, uselist=False, primaryjoin=(Object.parent_id==Object.id))
TemplateMatch.template = relation(Object, remote_side=Object.id, uselist=False, primaryjoin=(Object.owner_id==Object.id))

Object.templates = relation(TemplateMatch, remote_side=TemplateMatch.parent_id, uselist=True, primaryjoin=(TemplateMatch.parent_id==Object.id)) 
Template.matches = relation(Object, remote_side=TemplateMatch.owner_id, uselist=True, primaryjoin=(Object.owner_id==Template.id), foreign_keys=[Object.owner_id]) 


VerifierBases = {}
class VerifierBase(db.Base,DbRepr):
	"""
		Class for verification subsystems.
		"""

	__tablename__ = "verifierbase"
	__table_args__ = {'useexisting': True}
	q = db.session.query_property(db.Query)
	id = Column(TinyInteger(1), primary_key=True)
	name = Column(String(30), nullable=False, unique=True)
	cls = Column(String(50), nullable=False, unique=True)
	_mod = None

	def __init__(self, name, cls):
		self.name = name
		self.cls = cls

	@property
	def _module(self):
		if self._mod is None:
			self._mod = import_string(self.cls)
		return self._mod


class Verifier(Object):
	"""
		Verification emails (or similar).
		Parent: the thing to be verified.
		Owner: the user who's asked.
		"""
	__tablename__ = "verifiers"
	__table_args__ = ({'useexisting': True})
	__mapper_args__ = {'polymorphic_identity': 8}
	q = db.session.query_property(db.Query)
	id = Column(Integer, ForeignKey('obj.id',name="verifier_id"), primary_key=True,autoincrement=False)

	base_id = Column(TinyInteger, ForeignKey('verifierbase.id',name="verifier_base"))
	code = Column(String(50), nullable=False, unique=True)

	added = Column(DateTime, nullable=False)
	repeated = Column(DateTime, nullable=True)
	timeout = Column(DateTime, nullable=False)

	def __init__(self,base, obj, user=None, code=None, days=None):
		if isinstance(base, basestring):
			base = VerifierBase.q.get_by(name=base)
		self.base = base
		self.parent = obj
		self.owner = user or obj
		self.code = code or random_string(20,dash="-",dash_step=5)
		self.added = datetime.utcnow()
		self.timeout = datetime.utcnow() + timedelta((days or 10),0) ## ten days

	@property
	def expired(self):
		return self.timeout < datetime.utcnow()
	
	def send(self,*a,**k):
		"""Send the data to the user"""
		return self.base._module.send(self,*a,**k)

	def entered(self,*a,**k):
		"""The user entered the code. Redirect to whatever."""
		return self.base._module.entered(self,*a,**k)

	def retry(self,*a,**k):
		"""The user entered the code too late, or whaveter. Redirect to request page."""
		return self.base._module.retry(self,*a,**k)

Verifier.base = relation(VerifierBase, remote_side=VerifierBase.id, primaryjoin=(Verifier.base_id==VerifierBase.id))

class WikiPage(Object):
	"""\
		A wiki (or similar) page.
		Parent: The "main" wikipage we're a parent of
		Superparent: Our site
		Owner: Whoever created the page
		"""
	__tablename__ = "wikipage"
	__table_args__ = ({'useexisting': True})
	__mapper_args__ = {'polymorphic_identity': 9}
	q = db.session.query_property(db.Query)
	id = Column(Integer, ForeignKey('obj.id',name="template_id"), primary_key=True,autoincrement=False)

	name = Column(String(50))
	data = Column(Text)
	modified = Column(TimeStamp)

	def __init__(self, name, data):
		self.name = name
		self.data = data
	
	def markup(self):
		import markdown
		return markdown.markdown(self.data)


class Breadcrumb(Object):
	"""\
		Track page visits.
		Owner: the user who did it.
		Parent: The page thus visited.
		discr: mirrors parent.discr for easier seekage
		"""
	__tablename__ = "breadcrumbs"
	__table_args__ = ({'useexisting': True})
	__mapper_args__ = {'polymorphic_identity': 14}
	q = db.session.query_property(db.Query)
	id = Column(Integer, ForeignKey('obj.id',name="template_id"), primary_key=True,autoincrement=False)

	discr = Column(TinyInteger, ForeignKey('discriminator.id',name="templatematch_discr"), nullable=False)
	#seq = Column(Integer)
	visited = Column(TimeStamp)

	def __init__(self, user, obj):
		self.owner = user
		self.parent = obj
		self.visited = datetime.utcnow()
		self.discr = obj.discriminator
		#self.seq = 1+(db.engine.execute(select([func.max(Breadcrumb.seq)], and_(Breadcrumb.owner==user,Breadcrumb.discr==self.discr))).scalar() or 0)

	def __unicode__(self):
		if not self.owner or not self.parent: return super(Breadcrumb,self).__unicode__()
		return u'‹%s %s: %s saw %s on %s›' % (self.__class__.__name__, self.id, unicode(self.owner), unicode(self.parent), unicode(self.visited))
	def __str__(self):
		if not self.owner or not self.parent: return super(Breadcrumb,self).__str__()
		return '<%s %s: %s saw %s on %s>' % (self.__class__.__name__, self.id, str(self.owner), str(self.parent), str(self.visited))
	def __repr__(self):
		if not self.owner or not self.parent: return super(Breadcrumb,self).__repr__()
		return self.__str__()

	
