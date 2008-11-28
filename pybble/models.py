# -*- coding: utf-8 -*-

from datetime import datetime,timedelta
from sqlalchemy import Table, Column, String, Unicode, Boolean, DateTime, Integer, ForeignKey, \
	UniqueConstraint, Text
from sqlalchemy.orm import relation,backref
from pybble.utils import url_for, random_string, current_request
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


class DbRepr(object):
	def __unicode__(self):
		if getattr(self,"name",None):
			return u'‹%s %d:%s›' % (self.__class__.__name__, self.id, self.name)
		else:
			return u'‹%s %d›' % (self.__class__.__name__, self.id)
	def __str__(self):
		if getattr(self,"name",None):
			return '<%s %d:%s>' % (self.__class__.__name__, self.id, self.name)
		else:
			return '<%s %d>' % (self.__class__.__name__, self.id)
	__repr__ = __str__


class Discriminator(db.Base,DbRepr):
	"""Discriminator for Object"""
	__tablename__ = "discriminator"
	__table_args__ = {'useexisting': True}
	q = db.session.query_property(db.Query)
	id = Column(TinyInteger(1), primary_key=True)
	name = Column(String(30), nullable=False, unique=True)

	def __init__(self, cls):
		self.id = cls.discr()
		self.name = cls.__name__


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

	def has_children(self, discriminator=None):
		if discriminator:
			n = len(self.children.filter_by(discriminator=discriminator))
		else:
			n = len(self.children)
		return n

	@property
	def classname(self):
		return self.__class__.__name__

	def oid(self):
		"""
			Return a crypto ID of an object.
			This is done so that simply enumerating object IDs off the web pages wont work.
			"""
		return "%s.%d.%d.%s" % (self.classname, self.discriminator, self.id, 
		                        md5(self.__class__.__name__ + str(self.id) + settings.SECRET_KEY)\
		                            .digest().encode('base64').strip('\n =')[:10].replace("+","/-").replace("/","_"))

	@classmethod
	def discr(cls):
		"""Given a class, return the objects' discriminator."""
		return cls.__mapper__.polymorphic_identity



Object.owner = relation(Object, remote_side=Object.id, primaryjoin=(Object.owner_id==Object.id))
Object.parent = relation(Object, remote_side=Object.id, primaryjoin=(Object.parent_id==Object.id))
Object.superparent = relation(Object, remote_side=Object.id, primaryjoin=(Object.superparent_id==Object.id))

Object.children = relation(Object, remote_side=Object.parent_id, primaryjoin=(Object.id==Object.parent_id)) 

def obj_class(id):
	"""Given a discriminator ID, return the referred object's class."""
	return Object.__mapper__.polymorphic_map[id].class_

def obj_get(oid):
	"""Given an object ID, return the object"""
	cls,cid,id,hash = oid.split(".")
	cls = obj_class(int(cid))
	obj = cls.q.get_by(id=int(id))
	if oid != obj.oid():
		raise ValueError("This object does not exist: " % (oid,))
	return obj

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
		return url_for('pybble.views.link', uid=self.uid, _external=True)

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
		if v:
			try:
				Member.q.get_by(user=self,group=g).delete()
			except NoResult:
				pass
		else:
			db.session.add(Member(user=self,group=g))
	verified = property(_get_verified,_set_verified)
				
	
	def __unicode__(self):
		if getattr(self,"name",None):
			return u'‹%s %d:%s›' % (self.__class__.__name__, self.id, self.name)
		elif getattr(self,"superparent",None):
			return u'‹%s %d (anon @ %s)›' % (self.__class__.__name__, self.id, unicode(self.superparent))
		else:
			return u'‹%s %d (anon?)›' % (self.__class__.__name__, self.id)
	def __str__(self):
		if getattr(self,"name",None):
			return '<%s %d:%s>' % (self.__class__.__name__, self.id, self.name)
		elif getattr(self,"superparent",None):
			return '<%s %d (anon @ %s)>' % (self.__class__.__name__, self.id, str(self.superparent))
		else:
			return '<%s %d (anon?)>' % (self.__class__.__name__, self.id)
	__repr__ = __str__

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

class Member(db.Base,DbRepr):
	__tablename__ = "groupmembers"
	q = db.session.query_property(db.Query)
	id = Column(Integer, primary_key=True)

	user_id = Column(Integer(20),ForeignKey(Object.id,name="member_user"))   # one member
	group_id = Column(Integer(20),ForeignKey(Object.id,name="member_group")) # membership group
	excluded = Column(Boolean, nullable=False)

	def __init__(self,user,group):
		self.user = user
		self.group = group
		self.excluded = False

## The user may in fact be another group
Member.user = relation(Object, remote_side=Object.id, primaryjoin=(Member.user_id==Object.id))
## The group may in fact be a site, or anything else
Member.group = relation(Object, remote_side=Object.id, primaryjoin=(Member.group_id==Object.id))

PERM_NONE=0   # Exclusion: cannot do anything with that thing
PERM_LIST=1   # object will show up in listings
PERM_READ=2   # object may be examined
PERM_ADD=3    # can add child objects
PERM_WRITE=4  # object may be modified
PERM_ADMIN=9  # can do anything at all to the thing

class Permission(db.Base,DbRepr):
	"""
		Permission checks: This user can do that to objects of yonder type.

		Inherit=False: only this object
		inherit=True : only to child objects
		inherit=NULL : both.
		"""
	__tablename__ = "permissions"
	__table_args__ = {'useexisting': True}
	q = db.session.query_property(db.Query)
	id = Column(Integer(20), primary_key=True)

	user_id = Column(Integer(20),ForeignKey(Object.id,name="permission_user"), nullable=False)        # acting user/group
	obj_id = Column(Integer(20),ForeignKey(Object.id,name="permission_obj"), nullable=False)         # affected object
	right = Column(Integer(1))
	inherit = Column(Boolean, nullable=True)
	discriminator = Column(TinyInteger, ForeignKey('discriminator.id',name="obj_discr"))

	def __init__(self, user, obj, discr, right, inherit=None):
		self.user = user
		self.object = object
		if isinstance(discr, basestring):
			self.discriminator = Discriminator.q.get_by(name=base).id
		else:
			self.discriminator = discr
		self.right = right
		self.inherit = inherit
	
	@staticmethod
	def can_do(user,obj,discr=None):
		"""Recursively get the permission of this user for that (type of) object."""
		done = {}
		if discr is None:
			discr = obj.discriminator

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
				raise ValueError("Object recursion on "+repr(obj))
			done[obj.id]=1

			for u in ul:
				try:
					p = Permission.q.filter(Permission.inherit != no_inh).filter_by(user=u,object=obj).one()
				except NoResult:
					pass
				else:
					return p.right

			no_inh = False
			obj = obj.parent

		return PERM_NONE

	@staticmethod
	def permit(user,obj, right, discr=None, inherit=None):
		if discr is None:
			discr = obj.discriminator
		p = Permission.q.filter_by(user=u,object=obj,discriminator=discr).all()
		
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

	@staticmethod
	def drop(user,obj, discr=None, inherit=None):
		if discr is None:
			discr = obj.discriminator
		p = Permission.q.filter_by(user=u,object=obj,discriminator=discr).all()
		
		if len(p) > 0:
			if inherit is None:
				while p:
					p.pop().delete()
				return
			elif len(p) > 1 and p[1].inherit == inherit:
				p = p[1]
			else:
				p = p[0]
			p.delete()


Permission.user = relation(Object, remote_side=Object.id, primaryjoin=(Permission.user_id==Object.id))
Permission.object = relation(Object, remote_side=Object.id, primaryjoin=(Permission.obj_id==Object.id))

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


class TemplateMatch(db.Base,DbRepr):
	"""Associate a template to an object."""
	__tablename__ = "template_match"
	__table_args__ = ({'useexisting': True})
	q = db.session.query_property(db.Query)

	id = Column(Integer(20), primary_key=True)
	obj_id = Column('obj_id', Integer, ForeignKey('obj.id',name="obj_templates_obj"), nullable=False)
	template_id = Column('template_id', Integer, ForeignKey('templates.id',name="obj_templates_template"), nullable=False)
	discriminator = Column(TinyInteger, ForeignKey('discriminator.id',name="templatematch_discr"))
	type = Column(TinyInteger(1), nullable=False)
	inherit = Column(Boolean, nullable=True)

	def __init__(self, obj,discriminator,type, data):
		t = Template(None,data)
		self.obj = obj
		self.template = t
		self.discriminator = discriminator
		self.type = type

TemplateMatch.obj = relation(Object, remote_side=Object.id, primaryjoin=(TemplateMatch.obj_id==Object.id))
TemplateMatch.template = relation(Template, remote_side=Template.id, foreign_keys=(TemplateMatch.template_id), primaryjoin=(TemplateMatch.template_id==Template.id))

TM_TYPE_PAGE=1
TM_TYPE_LIST=2
TM_TYPE_STRING=3

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
	"""A wiki (or similar) page."""
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

