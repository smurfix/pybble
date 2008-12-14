# -*- coding: utf-8 -*-

from datetime import datetime,timedelta
from sqlalchemy import Table, Column, String, Unicode, Boolean, DateTime, Integer, ForeignKey, \
	UniqueConstraint, Text
from sqlalchemy.orm import relation,backref
from sqlalchemy.sql import select,func
from pybble.utils import random_string, current_request, AuthError
from pybble.database import db, NoResult
from sqlalchemy.databases.mysql import MSTinyInteger as TinyInteger
from sqlalchemy.databases.mysql import MSSmallInteger as SmallInteger
from sqlalchemy.databases.mysql import MSTimeStamp as TimeStamp
from sqlalchemy.sql import and_, or_, not_
from pybble.decorators import add_to
from werkzeug import import_string
import settings
import sys,os

try:
    from hashlib import md5
except ImportError:
	from md5 import md5


# Template detail levels
TM_DETAIL = {1:"Page", 2:"Subpage", 3:"String", 4:"Detail"}
for _x,_y in TM_DETAIL.items():
	globals()["TM_DETAIL_"+_y.upper()] = _x

def TM_DETAIL_name(id):
	return TM_DETAIL[int(id)]


# Permission levels
## Negative values need to match exactly.
## Positive one accumulate, i.e. somebody who can write is obviously able to read

PERM = {0:"None", 1:"List", 2:"Read", -3:"Add", 4:"Write", 5:"Delete", 9:"Admin"}
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
		if isinstance(discr, basestring):
			try: discr = int(discr)
			except ValueError: pass
		if isinstance(discr, Discriminator):
			return discr
		elif isinstance(discr, basestring):
			return Discriminator.q.get_by(name=discr)
		elif discr is None and obj is not None:
			return Discriminator.q.get_by(id=obj.discriminator)
		else:
			assert isinstance(discr, int)
			return Discriminator.q.get_by(id=discr)

class Object(db.Base):
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

	def __unicode__(self):
		if self.deleted: d = "DEL "
		else: d = ""
		if getattr(self,"name",None):
			return u'‹%s%s %s:%s›' % (d,self.__class__.__name__, self.id, self.name)
		else:
			return u'‹%s%s %s›' % (d,self.__class__.__name__, self.id)
	def __str__(self):
		if self.deleted: d = "DEL "
		else: d = ""
		if getattr(self,"name",None):
			return '<%s%s %s:%s>' % (d,self.__class__.__name__, self.id, self.name)
		else:
			return '<%s%s %s>' % (d,self.__class__.__name__, self.id)
	__repr__ = __str__

	@property
	def deleted(self):
		return self.parent is None and self.superparent is None and self.owner is None
	
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
	def trackings(self):
		return WantTracking.q.filter_by(parent=self, user=current_request.user)

	@property
	def classname(self):
		return self.__class__.__name__

	@property
	def classdiscr(self):
		return self.__class__.__mapper__.polymorphic_identity

	@classmethod
	def cls_name(cls):
		"""Necessary because underscore names don't work in templates."""
		return cls.__name__

	@classmethod
	def cls_discr(cls):
		return cls.__mapper__.polymorphic_identity

	@property
	def change_obj(self):
		"""\
			For objects which return change records, return whatever was changed.
			Other objects return themselves.
			"""
		return self

	@property
	def pso(self): # parent/super/owner
		if self.deleted:
			try:
				d = Delete.q.get_by(parent=self)
			except NoResult:
				return (None,None,None,None)
			else:
				return (d.superparent, d.old_superparent, d.old_owner,"DEL ")
		return (self.parent,self.superparent,self.owner,"")

	def oid(self):
		"""
			Return a crypto ID of an object.
			This is done so that simply enumerating object IDs off the web pages wont work.
			"""
		return "%d.%d.%s" % (self.discriminator, self.id, 
		                        md5(self.__class__.__name__ + str(self.id) + settings.SECRET_KEY)\
		                            .digest().encode('base64').strip('\n =')[:10].replace("+","/-").replace("/","_"))

	def get_template(self, detail=TM_DETAIL_PAGE):
		"""Return this object's template at a given detail level"""
		discr = self.discriminator

		no_inherit = True
		obj = self
		seen = set()
		while obj:
			seen.add(obj)
			try:
				t = TemplateMatch.q.filter(or_(TemplateMatch.inherit != no_inherit, TemplateMatch.inherit == None)).\
									get_by(obj=obj, discr=discr, detail=detail).template
			except NoResult:
				pass
			else:
				return t

			if obj is current_request.site:
				break
			elif obj.parent is not None and obj.parent not in seen:
				obj = obj.parent
			elif obj.superparent is not None and obj.superparent not in seen:
				obj = obj.superparent
			else:
				obj = current_request.site

			no_inherit = False

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
	try:
		return Object.__mapper__.polymorphic_map[int(id)].class_
	except ValueError:
		for f in Object.__mapper__.polymorphic_map.values():
			if f.class_.__name__ == id:
				return f.class_
		raise KeyError(id)

def obj_get(oid):
	"""Given an object ID, return the object"""
	cid,id,hash = oid.split(".")
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
		Parent: the site they first logged in on.
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
		if getattr(obj,"_no_crumbs",False):
			return # no recursive or similar nonsense, please
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


	def can_do(user,obj, discr=None, new_discr=None, want=None):
		"""Recursively get the permission of this user for that (type of) object."""

		#print >>sys.stderr,"PERM",discr,new_discr,want,obj,"AT",current_request.site,u"⇒",
		if obj is not current_request.site and \
		   current_request.user.can_admin(current_request.site):
			#print >>sys.stderr,"ADMIN"
			return want if want and want < 0 else PERM_ADMIN

		pq = Permission.q
		if want is not None:
			if want >= PERM_NONE:
				pq = pq.filter(Permission.right >= want)
			else:
				pq = pq.filter(Permission.right == want)
		if discr is not None:
			discr = Discriminator.get(discr).id
			pq = pq.filter_by(discr=discr)
		if new_discr is not None:
			new_discr = Discriminator.get(new_discr).id
			pq = pq.filter_by(new_discr=new_discr)

		ul = getattr(current_request.user,"_memberships",None)
		if ul is None:
			ul = [user]
			uld = set((user,))

			ulq = [user]
			while ulq:
				u = ulq.pop(0)
				for m in u.memberships:
					g = m.group
					if m.excluded:
						uld.add(g)
						continue
					if g not in uld:
						ul.append(g)
					ulq.append(g)
					uld.add(g)
			current_request.user._memberships = ul

		no_inh = True

		done = set()
		while obj:
			if obj in done:
				raise ValueError("Parent recursion on "+repr(obj))
			done.add(obj)

			try:
				p = pq.filter(or_(Permission.inherit != no_inh, Permission.inherit == None)).filter(or_(*(Permission.owner == u for u in ul))).filter_by(parent=obj).order_by().value(Permission.right)
			except NoResult:
				pass
			else:
				if p is not None:
					#print >>sys.stderr,p
					return p

			no_inh = False
			obj = obj.parent

		#print >>sys.stderr,"NONE"
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

class Member(Object):
	"""\
		Indicates membership of one object of another.
		owner: the individual who's the member.
		parent: the group
		"""
	__tablename__ = "groupmembers"
	__table_args__ = {'useexisting': True}
	__mapper_args__ = {'polymorphic_identity': 13}
	_no_crumbs = True
	q = db.session.query_property(db.Query)
	id = Column(Integer, ForeignKey('obj.id',name="Group_id"), primary_key=True,autoincrement=False)

	excluded = Column(Boolean, nullable=False)

	def __init__(self,user,group):
		self.owner = user
		self.parent = group
		self.excluded = False

	def __unicode__(self):
		p,s,o,d = self.pso
		if not self.owner or not self.parent: return super(Member,self).__unicode__()
		return u'‹%s%s %s: %s%s in %s›' % (d,self.__class__.__name__, self.id, unicode(self.owner), " NOT" if self.excluded else "", unicode(p))
	def __str__(self):
		p,s,o,d = self.pso
		if not self.owner or not self.parent: return super(Member,self).__str__()
		return '<%s%s %s: %s%s in %s>' % (d,self.__class__.__name__, self.id, str(self.owner), " NOT" if self.excluded else "", str(p))
	def __repr__(self):
		if not self.owner or not self.parent: return super(Member,self).__repr__()
		return self.__str__()

Member.user = relation(Object, remote_side=Object.id, uselist=False, primaryjoin=(Object.owner_id==Object.id))
Member.group = relation(Object, remote_side=Object.id, uselist=False, primaryjoin=(Object.parent_id==Object.id))

Object.memberships = relation(Member, remote_side=Member.owner_id, uselist=True, primaryjoin=(Member.owner_id==Object.id)) 
Object.members = relation(Member, remote_side=Member.parent_id, uselist=True, primaryjoin=(Member.parent_id==Object.id)) 

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
	_no_crumbs = True
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
		p,s,o,d = self.pso
		if not o or not p: return super(Permission,self).__unicode__()
		return u'‹%s%s %s: %s can %s %s %s %s %s›' % (d,self.__class__.__name__, self.id, unicode(o),PERM[self.right],Discriminator.q.get_by(id=self.discr).name,unicode(p), "*" if self.inherit is None else "Y" if self.inherit else "N", Discriminator.q.get_by(id=self.new_discr).name if self.new_discr is not None else "-")
	def __str__(self):
		p,s,o,d = self.pso
		if not o or not p: return super(Permission,self).__str__()
		return '<%s%s %s: %s can %s %s %s %s %s>' % (d,self.__class__.__name__, self.id, str(o),PERM[self.right],Discriminator.q.get_by(id=self.discr).name,str(p), "*" if self.inherit is None else "Y" if self.inherit else "N", Discriminator.q.get_by(id=self.new_discr).name if self.new_discr is not None else "-")
	def __repr__(self):
		if not self.owner or not self.parent: return super(Permission,self).__repr__()
		return self.__str__()


for a,b in PERM.iteritems():
	def can_do_closure(a,b):
		def can_do(self, obj, discr=None, new_discr=None):
			if a > PERM_NONE:
				return self.can_do(obj, discr=discr, new_discr=new_discr) >= a
			else:
				return self.can_do(obj, discr=discr, new_discr=new_discr, want=a) == a
		can_do.__doc__ = "Check if this user/group/whatever can %s an object" % \
			(b.lower() if a > PERM_NONE else "do nothing with",)

		def will_do(self, obj, discr=None, new_discr=None):
			if not can_do(self, obj, discr=discr, new_discr=new_discr):
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
	tracked = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
	## Datestamp of newest fully-processed Tracker object

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
		superparent: Site or TemplateMatch
		             the template applies to.
		owner: user who created the template.
		"""
	__tablename__ = "templates"
	__table_args__ = ({'useexisting': True})
	__mapper_args__ = {'polymorphic_identity': 6}
	q = db.session.query_property(db.Query)
	id = Column(Integer, ForeignKey('obj.id',name="template_id"), primary_key=True,autoincrement=False)
	name = Column(String(50), nullable=True)
	data = Column(Text)
	modified = Column(TimeStamp,default=datetime.utcnow, onupdate=datetime.utcnow)

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
	id = Column(Integer, ForeignKey('obj.id',name="template_match_id"), primary_key=True,autoincrement=False)

	discr = Column(TinyInteger, ForeignKey('discriminator.id',name="templatematch_discr"), nullable=False)
	detail = Column(TinyInteger(1), nullable=False)
	inherit = Column(Boolean, nullable=True)

	def __init__(self, obj,discr,detail, data):
		if isinstance(data,Template):
			t = data
		else:
			t = Template("%s@%s.%s" % (Discriminator.q.get_by(id=discr).name,obj.classname,obj.id),data)
			db.session.add(t)
			db.session.flush()
		self.parent = obj
		self.discr = Discriminator.get(discr,obj).id
		self.detail = detail
		db.session.add(self)
		db.session.flush()
		if t.superparent is None:
			t.superparent = self
			db.session.flush()
		self.owner = t
		db.session.flush()
	
	def __unicode__(self):
		p,s,o,d = self.pso
		if not o or not p: return super(TemplateMatch,self).__unicode__()
		return u'‹%s%s %s: %s for %s %s %s %s›' % (d,self.__class__.__name__, self.id, unicode(o),TM_DETAIL[self.detail],Discriminator.q.get_by(id=self.discr).name,unicode(p), "*" if self.inherit is None else "Y" if self.inherit else "N")
	def __str__(self):
		p,s,o,d = self.pso
		if not o or not p: return super(TemplateMatch,self).__str__()
		return '<%s%s %s: %s for %s %s %s %s>' % (d,self.__class__.__name__, self.id, str(o),TM_DETAIL[self.detail],Discriminator.q.get_by(id=self.discr).name,str(p), "*" if self.inherit is None else "Y" if self.inherit else "N")
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

	added = Column(DateTime, default=datetime.utcnow, nullable=False)
	repeated = Column(DateTime, nullable=True)
	timeout = Column(DateTime, nullable=False)

	def __init__(self,base, obj, user=None, code=None, days=None):
		if isinstance(base, basestring):
			base = VerifierBase.q.get_by(name=base)
		self.base = base
		self.parent = obj
		self.owner = user or obj
		self.code = code or random_string(20,dash="-",dash_step=5)
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
	id = Column(Integer, ForeignKey('obj.id',name="wikipage.id"), primary_key=True,autoincrement=False)

	name = Column(String(50))
	data = Column(Text)
	modified = Column(TimeStamp,default=datetime.utcnow,onupdate=datetime.utcnow)

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
	_no_crumbs = True

	q = db.session.query_property(db.Query)
	id = Column(Integer, ForeignKey('obj.id',name="breadcrumb_id"), primary_key=True,autoincrement=False)

	discr = Column(TinyInteger, ForeignKey('discriminator.id',name="breadcrumb_discr"), nullable=False)
	#seq = Column(Integer)
	visited = Column(TimeStamp,default=datetime.utcnow)

	def __init__(self, user, obj):
		self.owner = user
		self.parent = obj
		self.discr = obj.discriminator
		#self.seq = 1+(db.engine.execute(select([func.max(Breadcrumb.seq)], and_(Breadcrumb.owner==user,Breadcrumb.discr==self.discr))).scalar() or 0)

	def __unicode__(self):
		p,s,o,d = self.pso
		if not o or not p: return super(Breadcrumb,self).__unicode__()
		return u'‹%s%s %s: %s saw %s on %s›' % (d,self.__class__.__name__, self.id, unicode(o), unicode(p), unicode(self.visited))
	def __str__(self):
		p,s,o,d = self.pso
		if not o or not p: return super(Breadcrumb,self).__str__()
		return '<%s%s %s: %s saw %s on %s>' % (d,self.__class__.__name__, self.id, str(o), str(p), str(self.visited))
	def __repr__(self):
		return self.__str__()


	
class Change(Object):
	"""\
		Track content changes.
		Owner: the user who did it.
		Parent: The page thus changed.
		"""
	__tablename__ = "changes"
	__table_args__ = ({'useexisting': True})
	__mapper_args__ = {'polymorphic_identity': 15}
	_no_crumbs = True

	q = db.session.query_property(db.Query)
	id = Column(Integer, ForeignKey('obj.id',name="change_id"), primary_key=True,autoincrement=False)

	timestamp = Column(TimeStamp,default=datetime.utcnow)
	data = Column(Text)
	comment = Column(Unicode(200), nullable=True)

	def __init__(self, user, obj, data):
		self.owner = user
		self.parent = obj
		self.data = data

		db.session.add(self)
		db.session.add(Tracker(user,self))

	def __unicode__(self):
		p,s,o,d = self.pso
		if not o or not p: return super(Change,self).__unicode__()
		return u'‹%s %s: %s changed %s on %s›' % (self.__class__.__name__, self.id, unicode(o), unicode(p), unicode(self.timestamp))
	def __str__(self):
		p,s,o,d = self.pso
		if not o or not p: return super(Change,self).__str__()
		return '<%s %s: %s changed %s on %s>' % (self.__class__.__name__, self.id, str(o), str(p), str(self.timestamp))
	def __repr__(self):
		return self.__str__()

	@property
	def change_obj(self):
		return self.parent

Object.changes = relation(Change, remote_side=Change.parent_id, uselist=True, primaryjoin=(Change.parent_id==Object.id)) 


class Delete(Object):
	"""\
		Track deleted content.
		Owner: the user who did it.
		Parent: The page thus changed.
		Superparent: the old parent.
		"""
	__tablename__ = "deleted"
	__table_args__ = ({'useexisting': True})
	_no_crumbs = True

	q = db.session.query_property(db.Query)
	id = Column(Integer, ForeignKey('obj.id',name="delete_id"), primary_key=True,autoincrement=False)

	__mapper_args__ = {'polymorphic_identity': 16, 'inherit_condition':id==Object.id}

	comment = Column(Unicode(200), nullable=True)

	## The old parent is in self.superparent
	old_superparent_id = Column(Integer(20), ForeignKey('obj.id',name="obj_super"))
	old_owner_id = Column(Integer(20), ForeignKey('obj.id',name="obj_owner"))

	timestamp = Column(TimeStamp,default=datetime.utcnow)

	def __init__(self, user, obj, comment):
		self.owner = user
		self.parent = obj
		self.old_owner = obj.owner
		self.superparent = obj.parent
		self.old_superparent = obj.superparent

		obj.owner = None
		obj.parent = None
		obj.superparent = None

		db.session.add(self)
		db.session.add(Tracker(user,self))

	def __unicode__(self):
		if not self.owner or not self.parent: return super(Delete,self).__unicode__()
		return u'‹%s %s: %s deleted %s on %s›' % (self.__class__.__name__, self.id, unicode(self.owner), unicode(self.parent), unicode(self.timestamp))
	def __str__(self):
		if not self.owner or not self.parent: return super(Delete,self).__str__()
		return '<%s %s: %s deleted %s on %s>' % (self.__class__.__name__, self.id, str(self.owner), str(self.parent), str(self.timestamp))
	def __repr__(self):
		return self.__str__()

	@property
	def change_obj(self):
		return self.parent

Delete.old_owner = relation(Object, uselist=False, remote_side=Object.id, primaryjoin=(Delete.old_owner_id==Object.id))
Delete.old_parent = relation(Object, uselist=False, remote_side=Object.id, primaryjoin=(Delete.superparent_id==Object.id))
Delete.old_superparent = relation(Object, uselist=False, remote_side=Object.id, primaryjoin=(Delete.old_superparent_id==Object.id))


class Tracker(Object):
	"""\
		Track any kind of change, for purpose of RSSification, Emails, et al.
		Owner: the user who did it.
		Parent: The Change/Delete object, or the new object.
		Superparent: The site.
		"""
	__tablename__ = "tracking"
	__table_args__ = ({'useexisting': True})
	__mapper_args__ = {'polymorphic_identity': 17}
	_no_crumbs = True

	q = db.session.query_property(db.Query)
	id = Column(Integer, ForeignKey('obj.id',name="tracker_id"), primary_key=True,autoincrement=False)

	timestamp = Column(TimeStamp,default=datetime.utcnow)

	def __init__(self, user, obj, site = None):
		self.owner = user
		self.parent = obj
		self.superparent = site or current_request.site

	def __unicode__(self):
		if not self.owner or not self.superparent: return super(Tracker,self).__unicode__()
		if self.parent:
			return u'‹%s %s: %s changed %s›' % (self.__class__.__name__, self.id, unicode(self.owner), unicode(self.parent))
		else:
			return u'‹%s %s: %s changed %s on %s›' % (self.__class__.__name__, self.id, unicode(self.owner), unicode(self.superparent), unicode(self.timestamp))
	def __str__(self):
		if not self.owner or not self.superparent: return super(Tracker,self).__str__()
		if self.parent:
			return '<%s %s: %s changed %s>' % (self.__class__.__name__, self.id, str(self.owner), str(self.parent))
		else:
			return '<%s %s: %s changed %s on %s>' % (self.__class__.__name__, self.id, str(self.owner), str(self.superparent), str(self.timestamp))
	def __repr__(self):
		return self.__str__()

	@property
	def change_obj(self):
		return self.parent.change_obj

Tracker.site = relation(Object, uselist=False, remote_side=Object.id, primaryjoin=(Tracker.superparent_id==Object.id))

	
class UserTracker(Object):
	"""\
		Record that a change be reported to a user. This will be auto-built from Tracker and WantTracking objects.
		Owner: the user in question.
		Parent: The tracker object.
		Superparent: The tracked object itself.
		"""
	__tablename__ = "usertracking"
	__table_args__ = ({'useexisting': True})
	__mapper_args__ = {'polymorphic_identity': 18}
	_no_crumbs = True

	q = db.session.query_property(db.Query)
	id = Column(Integer, ForeignKey('obj.id',name="usertracker_id"), primary_key=True,autoincrement=False)

	def __init__(self, user, tracker):
		self.owner = user
		self.superparent = tracker.superparent
		self.parent = tracker

	def __unicode__(self):
		if not self.owner or not self.parent: return super(Tracker,self).__unicode__()
		return u'‹%s %s: %s for %s›' % (self.__class__.__name__, self.id, unicode(self.parent), unicode(self.owner))
	def __str__(self):
		if not self.owner or not self.parent: return super(Tracker,self).__str__()
		return '<%s %s: %s for %s>' % (self.__class__.__name__, self.id, str(self.parent), str(self.owner))
	def __repr__(self):
		return self.__str__()

UserTracker.obj = relation(Object, remote_side=Object.id, uselist=False, primaryjoin=(Object.superparent_id==Object.id))
UserTracker.user = relation(Object, remote_side=Object.id, uselist=False, primaryjoin=(Object.owner_id==Object.id))
	

class WantTracking(Object):
	"""
		Record that a user wants changes reported.
		Parent: The object which should be tracked.
		Owner: The user who wants the tracking.
		email: send email when this happens.
		track_new/_mod/_del: track new / modified / deleted content
		"""
	__tablename__ = "wanttracking"
	__table_args__ = ({'useexisting': True})
	__mapper_args__ = {'polymorphic_identity': 19}
	q = db.session.query_property(db.Query)
	id = Column(Integer, ForeignKey('obj.id',name="Group_id"), primary_key=True,autoincrement=False)

	discr = Column(TinyInteger, ForeignKey('discriminator.id',name="wanttracking_discr"), nullable=True)
	email = Column(Boolean, nullable=False) # send mail, not just RSS/on-site?
	track_new = Column(Boolean, nullable=False) # alert for new data?
	track_mod = Column(Boolean, nullable=False) # alert for modifications?
	track_del = Column(Boolean, nullable=False) # alert for deletions?

	def __init__(self, user,obj, discr=None):
		self.parent = obj
		self.owner = user
		self.discr = Discriminator.get(discr,obj).id if discr else None
		self.email = False
		self.track_new = False
		self.track_mod = False
		self.track_del = False
		self.inherit = None
	
	def __unicode__(self):
		p,s,o,d = self.pso
		if not o or not p: return super(WantTracking,self).__unicode__()
		return u'‹%s%s %s: %s in %s for %s %s›' % (d,self.__class__.__name__, self.id, "-" if self.discr is None else Discriminator.q.get_by(id=self.discr).name, unicode(p),unicode(o), "-N"[self.track_new]+"-M"[self.track_mod]+"-D"[self.track_del])
	def __str__(self):
		p,s,o,d = self.pso
		if not o or not p: return super(WantTracking,self).__str__()
		return '<%s%s %s: %s in %s for %s %s>' % (d,self.__class__.__name__, self.id, "-" if self.discr is None else Discriminator.q.get_by(id=self.discr).name, str(p),str(o), "-N"[self.track_new]+"-M"[self.track_mod]+"-D"[self.track_del])
	def __repr__(self):
		return self.__str__()

WantTracking.obj = relation(Object, remote_side=Object.id, uselist=False, primaryjoin=(Object.parent_id==Object.id))
WantTracking.user = relation(Object, remote_side=Object.id, uselist=False, primaryjoin=(Object.owner_id==Object.id))


def add_mime(name,typ,subtyp,ext):
	try:
		t = MIMEtype.q.get_by(typ=typ,subtyp=subtyp)
	except NoResult:
		t=MIMEtype()
		t.name = unicode(name)
		t.typ = typ
		t.subtyp = subtyp
		t.ext = ext
		db.session.add(t)
		db.session.flush()
		return t
	else:
		assert name == t.name
		if ext != t.ext:
			try:
				tt = MIMEext.q.get_by(ext=ext)
			except NoResult:
				tt = MIMEext()
				tt.mime = t
				tt.ext = ext
				db.session.add(tt)
				db.session.flush()
		return t

def mime_ext(ext):
	try:
		return MIMEtype.q.get_by(ext=ext)
	except NoResult:
		return MIMEext.q.get_by(ext=ext).mime


class MIMEtype(db.Base,DbRepr):
	"""Known MIME Types"""
	__tablename__ = "mimetype"
	__table_args__ = {'useexisting': True}
	q = db.session.query_property(db.Query)
	id = Column(Integer(2), primary_key=True)
	name = Column(Unicode(30), nullable=False, unique=True)
	typ = Column(String(15), nullable=False)
	subtyp = Column(String(15), nullable=False)
	ext = Column(String(15), nullable=False) # primary extension
	
	@property
	def mimetype(self):
		return "%s/%s" % (self.typ,self.subtyp)

	def __str__(self):
		return "<%s %s: .%s %s>" % (self.__class__.__name__, self.id,self.ext,self.mimetype)
	def __unicode__(self):
		return u"‹%s %s: .%s %s›" % (self.__class__.__name__, self.id,self.ext,self.mimetype)
	__repr__ = __str__


class MIMEext(db.Base):
	"""Extensions for MIME types"""
	__tablename__ = "mimeext"
	__table_args__ = {'useexisting': True}
	q = db.session.query_property(db.Query)
	id = Column(Integer(2), primary_key=True)
	mime_id = Column(Integer, ForeignKey(MIMEtype.id,name="mimetype_id"))
	ext = Column(String(10), nullable=False, unique=True)

	def __str__(self):
		return "<%s %s: %s %s>" % (self.__class__.__name__, self.id,self.ext,str(self.mime))
	def __unicode__(self):
		return u"‹%s %s: %s %s›" % (self.__class__.__name__, self.id,self.ext,unicode(self.mime))
	__repr__ = __str__

MIMEext.mime = relation(MIMEtype, uselist=False, remote_side=MIMEtype.id, primaryjoin=(MIMEext.mime_id==MIMEtype.id))
MIMEtype.exts = relation(MIMEext, uselist=True, remote_side=MIMEext.mime_id, primaryjoin=(MIMEext.mime_id==MIMEtype.id))

class Storage(Object):
	"""A box for binary data files"""
	__tablename__ = "storage"
	__table_args__ = {'useexisting': True}
	__mapper_args__ = {'polymorphic_identity': 21}
	_no_crumbs = True

	q = db.session.query_property(db.Query)
	id = Column(Integer, ForeignKey('obj.id',name="storage_id"), primary_key=True,autoincrement=False)

	name = Column(Unicode(250), nullable=False, unique=True)
	path = Column(String(250), nullable=False, unique=True)
	url = Column(String(250), nullable=False, unique=True)

	def __init__(self, name,path,url):
		self.name = unicode(name)
		self.path = path
		self.url = url
		self.superparent = current_request.site
		try: os.makedirs(path)
		except OSError: pass

	def __str__(self):
		return "<%s %s: %s %s>" % (self.__class__.__name__, self.id,self.name,str(self.path))
	def __unicode__(self):
		return u"‹%s %s: %s %s›" % (self.__class__.__name__, self.id,self.name,unicode(self.path))
	__repr__ = __str__

class _ContentExists: pass
def hash_data(content):
	import sha
	from base64 import b64encode
	return b64encode(sha.sha(content).digest(),altchars="-_").rstrip("=")

class BinData(Object):
	"""
		Stores one data file
		owner: whoever uploaded the thing
		superparent: the storage
		"""
	__tablename__ = "bindata"
	__table_args__ = {'useexisting': True}
	__mapper_args__ = {'polymorphic_identity': 22}
	_no_crumbs = True
	q = db.session.query_property(db.Query)
	id = Column(Integer, ForeignKey('obj.id',name="bindata_id"), primary_key=True,autoincrement=False)
	mime_id = Column(Integer, ForeignKey(MIMEtype.id,name="mimetype_id"))
	name = Column(Unicode(50), nullable=False)
	hash = Column(String(30), nullable=False, unique=True)
	timestamp = Column(TimeStamp,default=datetime.utcnow)

	@staticmethod
	def lookup(content):
		return BinData.q.get_by(hash=hash_data(content))
			
	def __init__(self,storage,name,ext,content):
		self.superparent = storage
		self.name = name
		self._content = content
		self.owner = current_request.user
		self.mime = mime_ext(ext)
		self.hash = hash_data(content)

	def __str__(self):
		return "<%s %s: %s %s>" % (self.__class__.__name__, self.id,self.mimetype,self.path)
	def __unicode__(self):
		return u"‹%s %s: %s %s›" % (self.__class__.__name__, self.id,self.mimetype,self.path)
	__repr__ = __str__

	def _get_content(self):
		if hasattr(self,"_content"):
			return self._content
		return open(self.path).read()
	def _set_content(self, data):
		if self._content is None:
			self._content = data
		else:
			raise RuntimeError("Content already set")
	content = property(_get_content,_set_content)

	@property
	def mimetype(self):
		try:
			return self.mime.mimetype
		except Exception:
			return "???/???"
	@property
	def ext(self):
		try:
			return self.mime.ext
		except Exception:
			return "???"

	def _get_chars(self):
		if self.id is None:
			db.session.flush()
			if self.id is None:
				return "???"
		id = self.id-1
		chars = "23456789abcdefghjkmnopqrstuvwxyz"
		midchars = "abcdefghjkmnopq"
		fc = []
		flast = chars[id % len(chars)]
		id = id // len(chars)
		while id:
			c = chars[id % len(midchars)]
			id = id // len(midchars)
			c = chars[id % len(midchars)] + c
			id = id // len(midchars)
			fc.insert(0,c)
		fc.append("_")
		fc.append(self.name+"_"+self.hash[0:10]+flast)
		if self.mime.ext:
			fc[-1] += "."+self.mime.ext
		return fc

	@property
	def path(self):
		try:
			fn = self.superparent.path
		except Exception:
			return "???"
		fc = self._get_chars()
		dir = os.path.join(fn,*fc[:-1])
		if not os.path.isdir(dir):
			os.makedirs(dir)
		fn = os.path.join(dir,fc[-1])
		return fn

	def get_absolute_url(self):
		fc = self._get_chars()
		fn = self.superparent.url + "/".join(fc)
		return fn
	
	def delete(self):
		p = self.path
		if os.path.exists(p):
			os.remove(p)
		super(BinData,self).delete()

	def save(self):
		if self._content is None:
			raise RuntimeError("Need to set content before saving")
		try:
			self._save_content()
		except BaseException:
			raise

	def _save_content(self):
		if self._content is _ContentExists:
			return
		p = self.path
		try:
			open(p,"w").write(self.content)
		except BaseException:
			if os.path.exists(p):
				os.remove(p)
			raise

BinData.storage = relation(Object, remote_side=Object.id, uselist=False, primaryjoin=(Object.superparent_id==Object.id))
BinData.mime = relation(MIMEtype, uselist=False, remote_side=MIMEtype.id, primaryjoin=(BinData.mime_id==MIMEtype.id))



class StaticFile(Object):
	"""\
		Record that a static file belongs to a specific site.
		Superparent: The site.
		Parent: The storage.
		"""
	__tablename__ = "staticfile"
	__table_args__ = ({'useexisting': True})
	_no_crumbs = True

	q = db.session.query_property(db.Query)
	id = Column(Integer, ForeignKey('obj.id',name="staticfile_id"), primary_key=True,autoincrement=False)

	__mapper_args__ = {'polymorphic_identity': 20, 'inherit_condition':id==Object.id}

	path = Column(Unicode(200), nullable=False)
	modified = Column(TimeStamp, default=datetime.utcnow, onupdate=datetime.utcnow)

	def __init__(self, path, bin):
		self.path = path
		self.superparent = current_request.site
		self.parent = bin
		
	@property
	def hash(self):
		return self.bindata.hash
	@property
	def content(self):
		return self.bindata.content
	@property
	def mimetype(self):
		return self.bindata.mimetype

StaticFile.bindata = relation(Object, uselist=False, remote_side=Object.id, primaryjoin=(StaticFile.parent_id==Object.id))

BinData.static_files = relation(Object, uselist=True, remote_side=Object.parent_id, primaryjoin=(Object.parent_id==BinData.id))

