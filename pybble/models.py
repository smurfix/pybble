# -*- coding: utf-8 -*-

from datetime import datetime,timedelta
from storm.locals import RawStr,Unicode,Int,Bool, Reference,ReferenceSet,Proxy,Select,Storm,DateTime,Desc, And,Or, Count, AutoReload
from storm.properties import PropertyPublisherMeta
from storm.references import Relation
from pybble.utils import random_string, current_request, AuthError
from pybble.database import db, NoResult

from pybble.decorators import add_to
from werkzeug import import_string
from jinja2.utils import Markup
from pybble import _settings as settings
import sys,os
from copy import copy

DEBUG_ACCESS=settings.ACCESS_DEBUG

"""Max ID of built-in tables; the rest are extensions"""
MAX_BUILTIN = 42

try:
    from hashlib import md5
except ImportError:
	from md5 import md5


# Template detail levels
TM_DETAIL = {1:"Page", 2:"Subpage", 3:"String", 4:"Detail", 5:"Snippet",
	6:"Hierarchy", 7:"RSS", 8:"email", 9:"preview"}
for _x,_y in TM_DETAIL.items():
	globals()["TM_DETAIL_"+_y.upper()] = _x

def TM_DETAIL_name(id):
	return TM_DETAIL[int(id)]

class MissingDummy(Exception):
	pass

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


class Discriminator(Storm,DbRepr):
	"""Discriminator for Object"""
	__storm_table__ = "discriminator"
	__storm_primary__ = "id"

	id = Int(primary=True)
	name = RawStr(allow_none=False)
	display_name = Unicode(allow_none=True)
	infotext = Unicode(allow_none=True)

	def __init__(self, cls):
		self.id = cls._discriminator
		self.name = cls.__name__
	
	@staticmethod
	def get(discr, obj=None):
		if discr is None and obj is None:
			return None
		if isinstance(discr, basestring):
			try: discr = int(discr)
			except ValueError: pass
		if isinstance(discr, Discriminator):
			return discr
		elif isinstance(discr, basestring):
			return db.get_by(Discriminator, name=str(discr))
		elif discr is None and obj is not None:
			return db.get_by(Discriminator, id=obj.discriminator)
		elif isinstance(discr, (int,long)):
			return db.get_by(Discriminator, id=discr)
		else:
			return db.get_by(Discriminator, id=discr._discriminator)

	@staticmethod
	def num(discr):
		if discr is None:
			return None
		if isinstance(discr, basestring):
			try: discr = int(discr)
			except ValueError: pass
		if isinstance(discr, Discriminator):
			return discr.id
		elif isinstance(discr, basestring):
			return db.get_by(Discriminator, name=str(discr)).id
		elif isinstance(discr, (int,long)):
			return discr
		else:
			return discr._discriminator

class Renderer(Storm,DbRepr):
	"""Render method for object content"""
	__storm_table__ = "renderer"
	id = Int(primary=True)
	name = Unicode(allow_none=False)
	cls = Unicode(allow_none=False)
	_mod = None

	def __init__(self, name, cls):
		super(Renderer,self).__init__()
		self.name = name
		self.cls = cls

	@property
	def _module(self):
		if self._mod is None:
			self._mod = import_string(self.cls)
		return self._mod
	
class BaseObject(Storm):
	"""This table represents all pointed-to objects"""
	__storm_table__ = "obj"
	id = Int(primary=True) # my ID
	owner_id = Int()       # creating object/user
	parent_id = Int()      # direct ancestor (replied-to comment)
	superparent_id = Int() # indirect ancestor (replied-to wiki page)
	
	owner = Reference(owner_id,id)
	parent = Reference(parent_id,id)
	superparent = Reference(superparent_id,id)

	discriminator = Int()

	def __init__(self, discr):
		self.discriminator = discr

#	def __storm_loaded__(self):
#		d = obj_class(self.discriminator)
#		object.__setattr__(self,"_ref", db.get_by(d, id=self.id))

	def _get_ref(self):
		try:
			ref = object.__getattribute__(self,"_ref");
		except AttributeError:
			d = obj_class(object.__getattribute__(self,"discriminator"))
			try:
				ref = db.get_by(d, id=object.__getattribute__(self,"id"))
			except NoResult:
				ref = None
			else:
				object.__setattr__(self,"_ref",ref)
		return ref

	def __getattribute__(self,k):
		try:
			return object.__getattribute__(self,k)
		except AttributeError:
			if k.startswith("__"):
				raise
			ref = self._get_ref()
			if ref:
				return object.__getattribute__(ref,k)
			else:
				raise
	def __setattr__(self,k,v):
		try:
			object.__getattribute__(self,k)
		except AttributeError:
			if k.startswith("__"):
				raise
			ref = self._get_ref()
			if ref:
				object.__setattr__(ref,k,v)
			else:
				raise
		else:
			object.__setattr__(self,k,v)

	def __unicode__(self):
		ref = self._get_ref()
		if ref:
			return unicode(ref)
		return u'‹%s %s %s›' % (self.__class__.__name__, self.id, Discriminator.get(self.discriminator) .name)
	def __str__(self):
		ref = self._get_ref()
		if ref:
			return str(ref)
		return '<%s %s %s>' % (self.__class__.__name__, self.id, Discriminator.get(self.discriminator).name)
	__repr__ = __str__


_discr2cls = {}
class RegistryMeta(PropertyPublisherMeta):
	def __init__(self, name, bases, dict):
		if "_obj" in dict: return
		self.id = Int(primary=True)
		self._obj = Reference(self.id, BaseObject.id)

		self.owner_id = Proxy(self._obj, BaseObject.owner_id)
		self.parent_id = Proxy(self._obj, BaseObject.parent_id)
		self.superparent_id = Proxy(self._obj, BaseObject.superparent_id)

		for k,v in dict.get("_proxy",{}).iteritems():
			setattr(self,k+"_id", Proxy(self._obj, getattr(BaseObject,v+"_id")))
			setattr(self,k,property(_get_ref(v),_set_ref(v)))

		#self.owner = Reference(self.owner_id, BaseObject.id)
		#self.parent = Reference(self.parent_id, BaseObject.id)
		#self.superparent = Reference(self.superparent_id, BaseObject.id)

		super(RegistryMeta,self).__init__(name, bases, dict)

		id = getattr(self, "_discriminator", None)
		if id:
			_discr2cls[id] = self

		return

		print "*",name
		try:
			o = Object
		except NameError:
			pass
		else:
			relmap = {}
			for a,b in Object.__dict__.items():
				if isinstance(b,Proxy):
					b = copy(b)
					#b._cls = self
					setattr(self,a,b)
					print "Proxy",a
				elif isinstance(b,Reference):
					b = copy(b)
					#b._cls = self
					setattr(self,a,b)
					print "Ref",a
				elif b is Object.id:
					b = copy(b)
					setattr(self,a,b)
					print "Ref",a
					


def _get_ref(n):
	def _get_one(self):
		self._obj_init()
		id = getattr(self._obj,n+"_id")
		if id is None: return id
		return db.store.get(BaseObject,id)
	return _get_one
def _set_ref(n):
	def _set_one(self,val):
		self._obj_init()
		if val is not None:
			val = val.id
		setattr(self._obj,n+"_id",val)
	return _set_one

class DummyObject(object):
	id=0
	owner=None
	owner_id=None
	parent=None
	parent_id=None
	superparent=None
	superparent_id=None
	@property
	def anon_user(self):
		return DummyUser()
	def has_children(self, discr=None):
		return False
	pso = (None,None,None,None)

class DummyUser(DummyObject):
	cur_login = datetime.utcnow()
	last_login = datetime.utcnow()
	first_login = datetime.utcnow()
	groups = []
	def all_visited(self, cls=None): return ()
	def can_do(user,obj, discr=None, new_discr=None, want=None):
		return False
	def oid(self): return "DummyUser"

class Object(Storm):
	"""The base type of all pointed-to objects. Don't use this in Reference() calls!"""
	__metaclass__ = RegistryMeta

	id = Int(primary=True)
	_obj = Reference(id, BaseObject.id)

	owner_id = Proxy(_obj, BaseObject.owner_id)
	parent_id = Proxy(_obj, BaseObject.parent_id)
	superparent_id = Proxy(_obj, BaseObject.superparent_id)

	#owner = Reference(owner_id,BaseObject.id)
	#parent = Reference(parent_id,BaseObject.id)
	#superparent = Reference(superparent_id,BaseObject.id)
	
	owner = property(_get_ref("owner"),_set_ref("owner"))
	parent = property(_get_ref("parent"),_set_ref("parent"))
	superparent = property(_get_ref("superparent"),_set_ref("superparent"))

	@property
	def discriminator(self): return self._discriminator
	@property
	def discr(self): return Discriminator.get(self._discriminator)

	def _obj_init(self):
		if self.id is not None:
			return
		obj = BaseObject(self._discriminator)
		db.store.add(obj)
		db.store.flush()
		self._obj = obj
		assert self.id is not None

	def __init__(self):
		self._obj_init()

	def __storm_pre_flush__(self):
		self._obj_init()

	_rec_str = False

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
	def changes(self):
		return db.store.find(Change, Change.parent_id == self.id)

	def has_children(self, discr=None):
		if discr:
			discr = Discriminator.num(discr)
			return db.store.execute(Select(Count(), where=And(BaseObject.parent_id == self.id, BaseObject.discriminator == discr))).get_one()[0]
		else:
			return db.store.execute(Select(Count(), where=BaseObject.parent_id == self.id)).get_one()[0]

	def has_superchildren(self, discr=None):
		if discr:
			discr = Discriminator.num(discr)
			return db.store.execute(Select(Count(), where=And(BaseObject.superparent_id == self.id, BaseObject.discriminator == discr))).get_one()[0]
		else:
			return db.store.execute(Select(Count(), where=BaseObject.superparent_id == self.id)).get_one()[0]

	def has_slaves(self, discr=None):
		if discr:
			discr = Discriminator.num(discr)
			return db.store.execute(Select(Count(), where=And(BaseObject.owner_id == self.id, BaseObject.discriminator == discr))).get_one()[0]
		else:
			return db.store.execute(Select(Count(), where=BaseObject.owner_id == self.id)).get_one()[0]

	def all_children(self, discr=None, want=PERM_LIST):
		q = [ BaseObject.parent_id == self.id ]
		if discr:
			discr = Discriminator.num(discr)
			q.append(BaseObject.discriminator == discr)
		for o in db.store.find(BaseObject, And(*q)):
			if current_request.user.can_do(o, discr=discr, want=want):
				yield o

	def all_superchildren(self, discr=None, want=PERM_LIST):
		q = [ BaseObject.superparent_id == self.id ]
		if discr:
			discr = Discriminator.num(discr)
			q.append(BaseObject.discriminator == discr)
		for o in db.store.find(BaseObject, And(*q)):
			if current_request.user.can_do(o, discr=discr, want=want):
				yield o

	def all_slaves(self, discr=None, want=PERM_LIST):
		q = [ BaseObject.owner_id == self.id ]
		if discr:
			discr = Discriminator.num(discr)
			q.append(BaseObject.discriminator == discr)
		for o in db.store.find(BaseObject, And(*q)):
			if current_request.user.can_do(o, discr=discr, want=want):
				yield o

	@property
	def children(self):
		return db.store.find(BaseObject, BaseObject.parent_id == self.id)

	@property
	def superchildren(self):
		return db.store.find(BaseObject, BaseObject.superparent_id == self.id)

	@property
	def slaves(self):
		return db.store.find(BaseObject, BaseObject.owner_id == self.id)

	@property
	def discr_children(self):
		s = Select((BaseObject.discriminator, Count()), where=BaseObject.parent_id==self.id, \
		    group_by=BaseObject.discriminator, order_by=BaseObject.discriminator)
		for discr,num in db.store.execute(s):
			c = obj_class(discr)
			yield c, db.filter_by(c,parent=self), num

	@property
	def discr_superchildren(self):
		s = Select((BaseObject.discriminator, Count()), where=BaseObject.superparent_id==self.id, \
		    group_by=BaseObject.discriminator, order_by=BaseObject.discriminator)
		for discr,num in db.store.execute(s):
			c = obj_class(discr)
			yield c, db.filter_by(c,superparent=self), num

	@property
	def discr_slaves(self):
		s = Select((BaseObject.discriminator, Count()), where=BaseObject.owner_id==self.id, \
		    group_by=BaseObject.discriminator, order_by=BaseObject.discriminator)
		for discr,num in db.store.execute(s):
			c = obj_class(discr)
			yield c, db.filter_by(c,owner=self), num

	@property
	def site(self):
		found = set()
		while self:
			if isinstance(self,Site):
				return self

			if self in found:
				return None
			found.add(self)

			if self.deleted:
				try:
					d = db.get_by(Delete, parent=self)
				except NoResult:
					return (None,None,None,None)
				else:
					self = d.superparent
			else:
				self = self.parent or self.superparent

	@property
	def templates(self):
		q = [ TemplateMatch.parent_id == self.id ]
		return db.store.find(TemplateMatch, TemplateMatch.parent_id == self.id).order_by(TemplateMatch.discr,TemplateMatch.detail,TemplateMatch.inherit)

	def all_memberships(self, discr=None):
		"""Return all objects (of some type?) I am a member of."""
		discr = Discriminator.num(discr)
		for t in self._member_rules:
			q = dict(t.args)
			q[t.src] = self
			for m in db.filter_by(t.table, **q):
				mm = getattr(m,t.dst)
				if discr is None or mm._discriminator == discr:
					yield m,mm

	@property
	def memberships(self):
		return self.all_memberships()

	def member_of(self,obj):
		"""Am I a member of this?"""
		for t in self._member_rules:
			q = dict(t.args)
			q[t.src] = self
			q[t.dst] = obj
			for m in db.filter_by(t.table, **q):
				return not getattr(m,"excluded",False)
		return False


	def all_members(self, discr=None):
		"""Return all objects (of some type) which are my members."""
		discr = Discriminator.num(discr)
		for t in self._member_rules:
			q = dict(t.args)
			q[t.dst] = self
			for m in db.filter_by(t.table, **q):
				mm = getattr(m,t.src)
				if discr is None or mm._discriminator == discr:
					yield m,mm
	@property
	def members(self):
		return self.all_members()

	@property
	def members_count(self):
		"""Count my members."""
		n = 0
		for t in self._member_rules:
			q = dict(t.args)
			q[t.dst] = self
			n += db.filter_by(t.table,**q).count()
		return n

	_member_rules = []
	class _rules(object):
		def __init__(self, table,src,dst, args):
			self.table = table
			self.src = src
			self.dst = dst
			self.args = args

	@classmethod
	def new_member_rule(cls, table,src,dst, **args):
		cls._member_rules.append(cls._rules(table,src,dst,args))

	@property
	def has_permissions(self):
		return self.permissions.count()

	@property
	def permissions(self):
		return db.filter_by(Permission, parent_id=self.id)

	@property
	def trackings(self):
		return db.filter_by(WantTracking,parent=self, user=current_request.user)

	@property
	def classname(self):
		return self.__class__.__name__

	@property
	def classdiscr(self):
		return self._discriminator

	@classmethod
	def cls_name(cls):
		"""Necessary because underscore names don't work in templates."""
		return cls.__name__

	@classmethod
	def cls_discr(cls):
		return cls._discriminator

	@property
	def change_obj(self):
		"""\
			For objects which return change records, return whatever was changed.
			Other objects return themselves.
			"""
		return self
	
	@property
	def last_change(self):
		return db.store.find(Change, Change.parent_id == self.id).order_by(Desc(Change.timestamp)).first()

	@property
	def pso(self): # parent/super/owner
		if self.deleted:
			try:
				d = db.get_by(Delete,parent=self)
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
		if self.id is None:
			db.store.flush()
		return "%d.%d.%s" % (self.discriminator, self.id, 
		                        md5(self.__class__.__name__ + str(self.id) + settings.SECRET_KEY)\
		                            .digest().encode('base64').strip('\n =')[:10].replace("+","/-").replace("/","_"))

	def get_template(self, detail=TM_DETAIL_PAGE):
		"""\
			Return this object's template at a given detail level.

			This code tries to do the right thing when confronted with
			deleted pages (get "before" data) or nested sites (use them
			if seen on standard parent/child path).
			"""
		discr = self.discriminator

		no_inherit = True
		obj = self
		seen = set()
		got_site = False
		try_super = True
		while obj:
			p,s,o,d = obj.pso
			seen.add(obj)
			t = db.store.find(TemplateMatch, And(Or(TemplateMatch.inherit != no_inherit, TemplateMatch.inherit == None), \
									TemplateMatch.obj_id == obj.id, TemplateMatch.discr == discr, TemplateMatch.detail == detail)).one()
			if t is not None:
				return t

			if isinstance(obj,Site):
				try_super = False
				if not p:
					got_site = True

			if p is not None and p not in seen:
				obj = p
			elif try_super and s is not None and s not in seen:
				obj = s
			elif got_site:
				break
			elif current_request.site not in seen:
				obj = current_request.site # last resort
			else:
				break

			no_inherit = False

		raise NoResult("Template %d for %s" % (detail,str(self)))

	@property
	def data(self):
		raise NotImplementedError("You need to override .data in «%s»" % (self.__class__.__name__,))

	def uptree(self):
		while self:
			yield self
			ru = getattr(current_request,"user",None)
			if isinstance(self,Site) and not (ru and ru.can_admin(self)):
				return
			self = self.parent

	def record_creation(self):
		"""Record the fact that a user created this object"""
		db.store.add(self)
		Tracker(current_request.user,self)

	def record_change(self,content=None,comment=None):
		"""Record the fact that a user changed this object, and why"""
		if content is None:
			content = self.data
		Change(current_request.user,self,content,comment)

	def record_deletion(self,comment=None):
		"""Record the fact that a user killed this object, and why"""
		Delete(current_request.user,self,comment)

		self.owner = None
		self.parent = None
		self.superparent = None

	@property
	def default_storage(self):
		"""Some objects may have a 'storage' attribute."""
		s = getattr(self,"storage",None)
		if s:
			return s
		if self.parent is None:
			return None
		return self.parent.default_storage

#Object.children = relation(Object, remote_side=Object.parent_id, primaryjoin=(Object.id==Object.parent_id)) 
#Object.superchildren = relation(Object, remote_side=Object.superparent_id, primaryjoin=(Object.id==Object.superparent_id)) 
#Object.slaves = relation(Object, remote_side=Object.owner_id, primaryjoin=(Object.id==Object.owner_id)) 

def obj_class(id):
	"""Given a discriminator ID, return the referred object's class."""
	try:
		return _discr2cls[int(id)]
	except ValueError:
		for f in _discr2cls.values():
			if f.__name__ == id:
				return f
		raise KeyError(id)

def obj_get(oid):
	"""Given an object ID, return the object"""
	cid,id,hash = oid.split(".")
	cls = obj_class(int(cid))
	obj = db.get_by(cls, id=int(id))
	if oid != obj.oid():
		raise ValueError("This object does not exist: " % (oid,))
	return obj

class renderObject(Object):
	"""\
		An object with render().
		You do need to add a renderer_id foreign key, and a data field.
		"""

	def __init__(self,renderer = None):
		if renderer is not None:
			if not isinstance(renderer,Renderer):
				renderer = db.get_by(Renderer,name=renderer)
			self.renderer_id = renderer.id
	
	@property
	def render(self):
		if self.renderer_id is None:
			return None
		def _wrap(r):
			def _call(*a,**k):
				r(self,*a,**k)
			return _call
		try:
			return _wrap(db.get_by(Renderer,id=self.renderer_id)._module)
		except NoResult:
			def _wr(*a,**k):
				return "<pre>"+Markup.escape(self.data)+"<pre>\n"
			return _wr

class User(Object):
	"""\
		Authorized users.
		Owner: Managing user; some sort of root for anon users.
		Parent: the site they first logged in on.
		SuperParent: for anon users, the site they're used with.
		"""
	__storm_table__ = "users"
	_discriminator = 2
	        
	username = Unicode(allow_none=False)
	first_name = Unicode()
	last_name = Unicode()
	email = Unicode()
	password = Unicode(allow_none=False)
	first_login = DateTime(allow_none=False)
	last_login = DateTime()
	cur_login = DateTime()

	feed_age = Int(allow_none=False, default=10)
	feed_pass = Unicode(allow_none=True)
	feed_read = DateTime(allow_none=True)

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
		if password is None:
			password = unicode(random_string(9))
		self.password=password
		self.first_login = datetime.utcnow()
		try:
			db.get_by(User, parent_id=current_request.site.id, username=username)
		except (AttributeError,NoResult):
			pass
		else:
			raise RuntimeError(u"User '%s' already exists in %s" %
			(username,current_request.site))
		db.store.add(self)

		if not self.anon:
			try:
				m = Member(self,current_request.site.anon_user)
			except (AttributeError,RuntimeError):
				pass
			else:
				db.store.add(m)
	
	@property
	def tracks(self):
		return db.store.find(Tracker, Tracker.owner_id==self.id).order_by(Desc(Tracker.timestamp))

	@property
	def trackers(self):
		return db.store.find(WantTracking, WantTracking.owner_id==self.id)

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

	def visits(self,obj):
		if getattr(obj,"_no_crumbs",False):
			return # no recursive or similar nonsense, please
		q = { "owner":self, "discr":obj.discriminator }
		try:
			s = db.get_by(Breadcrumb, parent=obj, **q)
		except NoResult:
#			for b in db.filter_by(Breadcrumb,**q).order_by(Breadcrumb.visited)[10:]:
#				db.store.remove(b)
			b = Breadcrumb(self,obj)
			db.store.add(b)
		else:
			s.visit()
			if not s.superparent: # bugfix
				s.superparent = current_request.site
	
	def last_visited(self,cls=None):
		q = { "owner":self, "superparent":current_request.site }
		if cls:
			q["discr"] = cls.cls_discr()
		try:
			r = db.filter_by(Breadcrumb, **q).order_by(Desc(Breadcrumb.visited)).first()
		except NoResult:
			return None
		if r:
			return r.parent
	
	def all_visited(self, cls=None):
		q = { "owner":self, "superparent":current_request.site }
		if cls:
			q["discr"] = cls.cls_discr()
		return db.filter_by(Breadcrumb, **q).order_by(Desc(Breadcrumb.visited))

	def is_verified(self, site=None):
		if site is None:
			site = current_request.site
		try:
			m = db.get_by(Member,user=self,group=site)
		except NoResult:
			return False
		else:
			return not m.excluded

	def add_verified(self,v,site=None):
		if site is None:
			site = current_request.site
		try:
			m = db.get_by(Member, user_id=self.id,group_id=site.id)
		except NoResult:
			if v:
				db.store.add(Member(user=self,group=site))
		else:
			if not v:
				db.store.remove(m)
	verified = property(is_verified,add_verified)
				
	def __unicode__(self):
		if self.username != "":
			return u"‹User %d:%s›" % (self.id,self.username)

		try:
			return u"‹User %d:anon @%s›" % (self.id, self.superparent.domain)
		except Exception:
			return u"‹User %d:anon @ ???›" % (self.id,)

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

		ru = getattr(current_request,"user",None)
		if obj is not current_request.site and \
		   ru and ru.can_admin(current_request.site, discr=current_request.site.classdiscr):
			if DEBUG_ACCESS:
				print >>sys.stderr,"ADMIN",obj
			return want if want and want < 0 else PERM_ADMIN

		if want>0 and want<=PERM_READ and obj.owner==user:
			if DEBUG_ACCESS:
				print >>sys.stderr,"OWN",obj
			return want

		if DEBUG_ACCESS:
			print >>sys.stderr,"PERM", Discriminator.get(discr).name if discr else "-", Discriminator.get(new_discr) if new_discr else "-", (PERM_name(want) if want else "-")+":",obj,"FOR",user,"AT",current_request.site, u"⇒"

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
			pq.append(Permission.discr == discr)

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
				print >>sys.stderr, "Checking",obj
			p = p.first()
			if p is not None:
				if DEBUG_ACCESS:
					print >>sys.stderr,p
				p = p.right
				return p

			no_inh = False
			obj = obj.parent

		if DEBUG_ACCESS:
			print >>sys.stderr,"NONE"
		return PERM_NONE

	def will_do(user,obj,discr=None, perm=PERM_NONE):
		if user.can_do(obj,discr) < perm:
			raise AuthError(obj,perm)

	def permit(user,obj, right, discr=None, inherit=None):
		discr = Discriminator.get(discr,obj).id
		p = list(db.store.find(Permission, And(Permission.owner==u, Permission.parent==obj, Permission.discr==discr)))
		
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
			db.store.add(p)

	def forbid(user,obj, discr=None, inherit=None):
		discr = Discriminator.get(discr,obj).id
		p = list(db.store_find(Permission, And(Permission.owner==u,Permission.parent==obj,Permission.discr==discr)))
		
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


class Group(Object):
	"""
		A group of users. (Usually.)
		superparent: the site this group belongs to.
		owner: the managing user; the site, for system groups.
		"""
	__storm_table__ = "groups"
	_discriminator = 4
	        
	name = Unicode()

	def __init__(self,name,owner,site=None):
		super(Group,self).__init__()
		self.superparent = site or owner
		self.owner = owner
		self.name = name
	
def named_group(owner, name):
	"""Return the site-specific group with that name."""
	return db.get_by(Group,name=name, owner=site)

class Member(Object):
	"""\
		Indicates membership of one object of another.
		owner: the individual who's the member.
		parent: the group
		"""
	__storm_table__ = "groupmembers"
	_discriminator = 13
	_no_crumbs = True
	_proxy = { "user":"owner", "group":"parent" };

	excluded = Bool(allow_none=False,default=False)

	def __init__(self,user,group):
		super(Member,self).__init__()
		self.owner = user
		self.parent = group
		self.excluded = False
		try: del self._memberships
		except AttributeError: pass
		db.store.add(self)

	@property
	def data(self):
		return """\
User: %s
Group: %s
Member: %s
""" % (self.owner, self.parent, "Yes" if not self.excluded else "No")

	def __unicode__(self):
		p,s,o,d = self.pso
		if self._rec_str or not o or not p: return super(Member,self).__str__()
		try:
			self._rec_str = True
			return u'‹%s%s %s: %s%s in %s›' % (d,self.__class__.__name__, self.id, unicode(o), " NOT" if self.excluded else "", unicode(p))
		finally:
			self._rec_str = False
	def __str__(self):
		p,s,o,d = self.pso
		if self._rec_str or not o or not p: return super(Member,self).__str__()
		try:
			self._rec_str = True
			return '<%s%s %s: %s%s in %s>' % (d,self.__class__.__name__, self.id, str(o), " NOT" if self.excluded else "", str(p))
		finally:
			self._rec_str = False
	def __repr__(self):
		if not self.owner or not self.parent: return super(Member,self).__repr__()
		return self.__str__()

Object.new_member_rule(Member, "owner","parent")

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
	__storm_table__ = "permissions"
	_discriminator = 10
	_no_crumbs = True

	right = Int(allow_none=False)
	inherit = Bool(allow_none=True)
	discr = Int(allow_none=False)
	new_discr = Int(allow_none=True)

	def __init__(self, user, obj, discr, right, inherit=None, new_discr=None):
		discr = Discriminator.get(discr,obj).id
		super(Permission,self).__init__()
		self.discr = discr
		self.right = right
		self.inherit = inherit
		self.owner = user
		self.parent = obj

		if right == PERM_ADD:
			try: del user._can_add
			except AttributeError: pass
	
	def __unicode__(self):
		p,s,o,d = self.pso
		if self._rec_str or not o or not p: return super(Permission,self).__unicode__()
		try:
			self._rec_str = False
			return u'‹%s%s %s: %s can %s %s %s %s %s›' % (d,self.__class__.__name__, self.id, unicode(o),PERM[self.right],db.get_by(Discriminator,id=self.discr).name,unicode(p), "*" if self.inherit is None else "Y" if self.inherit else "N", db.get_by(Discriminator,id=self.new_discr).name if self.new_discr is not None else "-")
		finally:
			self._rec_str = False
	def __str__(self):
		p,s,o,d = self.pso
		if self._rec_str or not o or not p: return super(Permission,self).__str__()
		try:
			self._rec_str = True
			return '<%s%s %s: %s can %s %s %s %s %s>' % (d,self.__class__.__name__, self.id, str(o),PERM[self.right],db.get_by(Discriminator,id=self.discr).name,str(p), "*" if self.inherit is None else "Y" if self.inherit else "N", db.get_by(Discriminator,id=self.new_discr).name if self.new_discr is not None else "-")
		finally:
			self._rec_str = False
	def __repr__(self):
		if not self.owner or not self.parent: return super(Permission,self).__repr__()
		return self.__str__()

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
		db.get_by(Discriminator,id=self.discr).name, \
		db.get_by(Discriminator,id=self.new_discr).name if self.new_discr is not None else "-", \
		self.right, \
		"*" if self.inherit is None else "Y" if self.inherit else "N")


for a,b in PERM.iteritems():
	def can_do_closure(a,b):
		def can_do(self, obj, discr=None, new_discr=None):
			if DEBUG_ACCESS:
				print >>sys.stderr, "can_"+b+":", self,obj,discr,new_discr
			if a > PERM_NONE:
				return self.can_do(obj, discr=discr, new_discr=new_discr, want=a) >= a
			else:
				return self.can_do(obj, discr=discr, new_discr=new_discr, want=a) == a
		can_do.__doc__ = "Check if this user/group/whatever can %s an object" % \
			(b.lower() if a > PERM_NONE else "do nothing with",)

		def will_do(self, obj, discr=None, new_discr=None):
			if DEBUG_ACCESS:
				print >>sys.stderr, "will_"+b+":", self,obj,discr,new_discr
			if not can_do(self, obj, discr=discr, new_discr=new_discr):
				raise AuthError(obj,a)
		def can_err(self, obj, discr=None, new_discr=None):
			if isinstance(obj,(DummyUser,DummySite)) and discr in (User._discriminator,Site._discriminator,None) and new_discr is None and a>0 and a<=PERM_READ:
				return True
			return False
		def will_err(self, obj, discr=None, new_discr=None):
			if not can_err(self, obj, discr=discr, new_discr=new_discr):
				raise AuthError(obj,a)


		return can_do,will_do,can_err,will_err
	
	c,d,e,f = can_do_closure(a,b)
	setattr(Object,'can_'+b.lower(), c)
	setattr(Object,'will_'+b.lower(), d)
	setattr(DummyUser,'can_'+b.lower(), e)
	setattr(DummyUser,'will_'+b.lower(), f)


class Storage(Object):
	"""A box for binary data files"""
	__storm_table__ = "storage"
	_discriminator = 21
	_no_crumbs = True

	name = Unicode(allow_none=False)
	path = Unicode(allow_none=False)
	url = Unicode(allow_none=False)

	def __init__(self, name,path,url):
		super(Storage,self).__init__()
		self.name = unicode(name)
		self.path = unicode(path)
		self.url = unicode(url)
		self.superparent = current_request.site
		try: os.makedirs(path)
		except OSError: pass

	def __str__(self):
		return "<%s %s: %s %s>" % (self.__class__.__name__, self.id,self.name,str(self.path))
	def __unicode__(self):
		return u"‹%s %s: %s %s›" % (self.__class__.__name__, self.id,self.name,unicode(self.path))
	__repr__ = __str__


class DummySite(DummyObject):
	"""A site without content."""
	def __init__(self,domain,name=None):
		if name is None:
			name=u"Here be "+domain
		self.domain=unicode(domain)
		self.name=name
		try:
			self.parent = db.get_by(Site,domain=u"")
		except NoResult:
			pass
		else:
			self.parent_id = self.parent.id
	def oid(self): return "DummySite"
	def get_template(self, detail=TM_DETAIL_PAGE):
		if isinstance(self,DummySite) and detail == TM_DETAIL_SUBPAGE:
			raise MissingDummy
		if not self.parent:
			raise NoResult
		return self.parent.get_template(detail)

class Site(Object):
	"""A web domain. 'owner' is set to the domain's superuser."""
	__storm_table__ = "sites"
	_discriminator = 5

	domain = Unicode(allow_none=False)
	name = Unicode(allow_none=False)
	tracked = DateTime(allow_none=False, default_factory=datetime.utcnow)
	## Datestamp of newest fully-processed Tracker object

	storage_id = Int(allow_none=True)
	storage = Reference(storage_id,Storage.id)

	def __storm_pre_flush__(self):
		self.tracked = datetime.utcnow()
		super(Site,self).__storm_pre_flush__()

	def __init__(self,domain,name=None):
		super(Site,self).__init__()
		if name is None:
			name=u"Here be "+domain
		self.domain=unicode(domain)
		self.name=name

		try:
			s = db.get_by(Site,domain=u"")
		except NoResult:
			if domain == "":
				s = None
			else:
				s = Site(name=u"Main default site",domain=u"")
				db.store.add(s)
		self.parent = s

		try:
			self.owner = current_request.user
		except (AttributeError,RuntimeError):
			self.owner = None
		db.store.add(self)
		u = User(u"",u"")
		u.superparent = self
		db.store.add(u)

	@property
	def anon_user(self):
		while True:
			try:
				return db.get_by(User, superparent_id=self.id, username=u"", password=u"")
			except NoResult:
				if site.parent:
					site = site.parent
				else:
					raise

		
	def __unicode__(self):
		return u"‹Site ‚%s‘ @ %s›" % (self.name, self.domain)

	@property
	def data(self):
		return u"""\
name: %s
domain: %s
""" % (self.name,self.domain)


class Template(Object):
	"""
		A template for rendering.
		parent: Site the template applies to.
		owner: user who created the template.
		"""
	__storm_table__ = "templates"
	_discriminator = 6

	name = Unicode(allow_none=False)
	data = Unicode()
	modified = DateTime(default_factory=datetime.utcnow)

	def __storm_pre_flush__(self):
		self.modified = datetime.utcnow()
		super(Template,self).__storm_pre_flush__()

	def __init__(self, name, data, parent=None):
		super(Template,self).__init__()
		self.name = name
		self.data = data
		self.owner = current_request.user
		self.parent = parent or current_request.site
		self.superparent = getattr(parent,"site",None) or current_request.site

	def __repr__(self):
		return "'<%s:%d>'" % (self.__class__.__name__,self.id)


class TemplateMatch(Object):
	"""
		Associate a template to an object.
		Parent: The object which the template is for.
		"""
	__storm_table__ = "template_match"
	_discriminator = 12
	_proxy = { "obj":"parent" }

	data = Unicode()
	modified = DateTime(default_factory=datetime.utcnow)

	def __storm_pre_flush__(self):
		self.modified = datetime.utcnow()
		super(TemplateMatch,self).__storm_pre_flush__()

	discr = Int(allow_none=False)
	detail = Int(allow_none=False)
	inherit = Bool(allow_none=True)

	def __init__(self, obj,discr,detail, data):
		discr = Discriminator.get(discr,obj).id
		super(TemplateMatch,self).__init__()
		self.discr = discr
		self.detail = detail
		self.data = data
		db.store.add(self)
		self.parent = obj
		db.store.flush()
	
	def __unicode__(self):
		p,s,o,d = self.pso
		if self._rec_str or not p: return super(TemplateMatch,self).__unicode__()
		try:
			self._rec_str = True
		finally:
			return u'‹%s%s %s: %s %s %s %s›' % (d,self.__class__.__name__, self.id, TM_DETAIL[self.detail],db.get_by(Discriminator, id=self.discr).name,unicode(p), "*" if self.inherit is None else "Y" if self.inherit else "N")
			self._rec_str = False
	def __str__(self):
		p,s,o,d = self.pso
		if self._rec_str or not p: return super(TemplateMatch,self).__str__()
		try:
			self._rec_str = True
			return '<%s%s %s: %s %s %s %s>' % (d,self.__class__.__name__, self.id, TM_DETAIL[self.detail],db.get_by(Discriminator,id=self.discr).name,str(p), "*" if self.inherit is None else "Y" if self.inherit else "N")
		finally:
			self._rec_str = False
	def __repr__(self):
		if not self.parent: return "'"+super(TemplateMatch,self).__repr__()+"'"
		return "'"+self.__str__()+"'"


VerifierBases = {}
class VerifierBase(Storm,DbRepr):
	"""
		Class for verification subsystems.
		"""

	__storm_table__ = "verifierbase"
	id = Int(primary=True)
	name = Unicode(allow_none=False)
	cls = RawStr(allow_none=False)
	_mod = None

	def __init__(self, name, cls):
		super(VerifierBase,self).__init__()
		self.name = unicode(name)
		self.cls = cls

	@property
	def _module(self):
		if self._mod is None:
			self._mod = import_string(str(self.cls))
		return self._mod

	@staticmethod
	def register(name, cls):
		name = unicode(name)
		try:
			v = db.get_by(VerifierBase,name=name)
		except NoResult:
			v=VerifierBase(name=name, cls=cls)
			db.store.add(v)
		else:
			assert v.cls == cls

class Verifier(Object):
	"""
		Verification emails (or similar).
		Parent: the thing to be verified.
		Owner: the user who's asked.
		"""
	__storm_table__ = "verifiers"
	_discriminator = 8

	base_id = Int()
	base = Reference(base_id, VerifierBase.id)
	code = RawStr(allow_none=False)

	added = DateTime(default_factory=datetime.utcnow, allow_none=False)
	repeated = DateTime(allow_none=True)
	timeout = DateTime(allow_none=False)

	def __init__(self,base, obj, user=None, code=None, days=None):
		super(Verifier,self).__init__()
		if isinstance(base, basestring):
			base = db.get_by(VerifierBase,name=unicode(base))
		self.base = base
		self.parent = obj
		self.owner = user or obj
		self.code = code or random_string(20,dash="-",dash_step=5)
		self.timeout = datetime.utcnow() + timedelta((days or 10),0) ## ten days

	def __unicode__(self):
		p,s,o,d = self.pso
		if self._rec_str or not p: return super(Verifier,self).__unicode__()
		try:
			self._rec_str = True
			return u'‹%s%s %s: %s for %s›' % (d,self.__class__.__name__, self.id, self.base.name, unicode(p))
		finally:
			self._rec_str = False
	def __str__(self):
		p,s,o,d = self.pso
		if self._rec_str or not p: return super(Verifier,self).__str__()
		try:
			self._rec_str = True
			return '<%s%s %s: %s for %s>' % (d,self.__class__.__name__, self.id, self.base.name, str(p))
		finally:
			self._rec_str = False
	def __repr__(self):
		if not self.parent: return super(Verifier,self).__repr__()
		return self.__str__()

	@property
	def expired(self):
		return self.timeout < datetime.utcnow()
	
	def send(self,*a,**k):
		"""Send the data to the user"""
		return self.base._module.send(self,*a,**k)

	def entered(self,*a,**k):
		"""The user entered the code. Redirect to whatever."""
		return self.base._module.entered(self,*a,**k)

	def confirmed(self,*a,**k):
		"""Confirmation page. Redirect to whatever."""
		return self.base._module.confirmed(self,*a,**k)

	def retry(self,*a,**k):
		"""The user entered the code too late, or whaveter. Redirect to request page."""
		return self.base._module.retry(self,*a,**k)


class WikiPage(Object):
	"""\
		A wiki (or similar) page.
		Parent: The "main" wikipage we're a parent of, or whatever parent there is
		Superparent: Our site (main page) or empty (subpage)
		Owner: Whoever created the page

		Wiki pages are not (yet?) nested.
		"""
	__storm_table__ = "wikipage"
	_discriminator = 9

	name = Unicode(allow_none=False)
	data = Unicode()
	mainpage = Bool(default=True, allow_none=False) # main-linked page?
	modified = DateTime(default_factory=datetime.utcnow)

	def __storm_pre_flush__(self):
		self.modified = datetime.utcnow()
		super(WikiPage,self).__storm_pre_flush__()

	def __init__(self, name, data):
		super(WikiPage,self).__init__()
		self.name = name
		self.data = data
	
	def url_html_view(self):
		from pybble.render import url_for
		if self.mainpage:
			return url_for("pybble.part.wikipage.viewer", name=self.name)
		if isinstance(self.parent,WikiPage) and self.parent.mainpage:
			return url_for("pybble.part.wikipage.viewer", name=self.name, parent=self.parent.name)

class Breadcrumb(Object):
	"""\
		Track page visits.
		Owner: the user who did it.
		Parent: The page thus visited.
		Superparent: The site.
		discr: mirrors parent.discr, for easier selectage
		"""
	__storm_table__ = "breadcrumbs"
	_discriminator = 14
	_no_crumbs = True

	discr = Int(allow_none=False)
	#seq = Int()
	visited = DateTime(default_factory=datetime.utcnow)
	last_visited = DateTime(allow_none=True)
	cur_visited = DateTime(default_factory=datetime.utcnow, allow_none=True)

	def __init__(self, user, obj):
		super(Breadcrumb,self).__init__()
		self.discr = obj.discriminator
		self.owner = user
		self.parent = obj
		self.superparent = current_request.site
		#self.seq = 1+(db.store.execute(select(Max(Breadcrumb.seq), And((Breadcrumb.owner==user,Breadcrumb.discr==self.discr))).scalar() or 0)

	def __unicode__(self):
		p,s,o,d = self.pso
		if self._rec_str or not o or not p: return super(Breadcrumb,self).__unicode__()
		try:
			self._rec_str = True
			return u'‹%s%s %s: %s saw %s on %s›' % (d,self.__class__.__name__, self.id, unicode(o), unicode(p), unicode(self.visited))
		finally:
			self._rec_str = False
	def __str__(self):
		p,s,o,d = self.pso
		if self._rec_str or not o or not p: return super(Breadcrumb,self).__str__()
		try:
			self._rec_str = True
			return '<%s%s %s: %s saw %s on %s>' % (d,self.__class__.__name__, self.id, str(o), str(p), str(self.visited))
		finally:
			self._rec_str = False
	def __repr__(self):
		return self.__str__()

	def visit(self):
		now = datetime.utcnow()
		if self.cur_visited is None or self.cur_visited < now-timedelta(0,600):
			self.last_visited = self.visited
			self.visited = now
		self.cur_visited = now

	
class Change(Object):
	"""\
		Track content changes.
		Owner: the user who did it.
		Parent: The page thus changed.
		"""
	__storm_table__ = "changes"
	_discriminator = 15
	_no_crumbs = True

	timestamp = DateTime(default_factory=datetime.utcnow)
	data = Unicode()
	comment = Unicode(allow_none=True)

	def __init__(self, user, obj, data, comment = None):
		super(Change,self).__init__()
		self.owner = user
		self.parent = obj
		self.data = data
		self.comment = comment

		db.store.add(self)
		db.store.add(Tracker(user,self))

	def __unicode__(self):
		p,s,o,d = self.pso
		if self._rec_str or not o or not p: return super(Change,self).__unicode__()
		try:
			self._rec_str = True
			return u'‹%s %s: %s changed %s on %s›' % (self.__class__.__name__, self.id, unicode(o), unicode(p), unicode(self.timestamp))
		finally:
			self._rec_str = False
	def __str__(self):
		p,s,o,d = self.pso
		if self._rec_str or not o or not p: return super(Change,self).__str__()
		try:
			self._rec_str = True
			return '<%s %s: %s changed %s on %s>' % (self.__class__.__name__, self.id, str(o), str(p), str(self.timestamp))
		finally:
			self._rec_str = False
	def __repr__(self):
		return self.__str__()

	@property
	def change_obj(self):
		return self.parent

	@property
	def next_change(self):
		return db.filter(Change, And(Change.timestamp>self.timestamp,
		                             Change.parent_id==self.parent_id))\
                	.order_by(Change.timestamp)\
                	.first()
	@property
	def prev_change(self):
		return db.filter(Change, And(Change.timestamp<self.timestamp,
		                             Change.parent_id==self.parent_id))\
					.order_by(Desc(Change.timestamp))\
					.first()


class Delete(Object):
	"""\
		Track deleted content.
		Owner: the user who did it.
		Parent: The page thus changed.
		Superparent: the old parent.
		"""
	__storm_table__ = "deleted"
	_discriminator = 16
	_no_crumbs = True

	comment = Unicode(allow_none=True)

	## The old parent is in self.superparent
	old_superparent_id = Int(allow_none=True)
	old_owner_id = Int(allow_none=True)
	@property
	def old_parent_id(self): return self.superparent_id

	old_owner = Reference(old_owner_id, BaseObject.id)
	old_parent = property(_get_ref("superparent"),_set_ref("superparent"))
	old_superparent = Reference(old_superparent_id, BaseObject.id)

	timestamp = DateTime(default_factory=datetime.utcnow)

	def __init__(self, user, obj, comment):
		super(Delete,self).__init__()
		self.owner = user
		self.parent = obj
		self.old_owner = obj.owner
		self.superparent = obj.parent
		self.old_superparent = obj.superparent

		db.store.add(self)
		db.store.add(Tracker(user,self))

	def __unicode__(self):
		if self._rec_str or not self.owner or not self.parent: return super(Delete,self).__unicode__()
		try:
			self._rec_str = True
			return u'‹%s %s: %s deleted %s on %s›' % (self.__class__.__name__, self.id, unicode(self.owner), unicode(self.parent), unicode(self.timestamp))
		finally:
			self._rec_str = False
	def __str__(self):
		if self._rec_str or not self.owner or not self.parent: return super(Delete,self).__str__()
		try:
			self._rec_str = True
			return '<%s %s: %s deleted %s on %s>' % (self.__class__.__name__, self.id, str(self.owner), str(self.parent), str(self.timestamp))
		finally:
			self._rec_str = False
	def __repr__(self):
		return self.__str__()

	@property
	def change_obj(self):
		return self.parent



class Tracker(Object):
	"""\
		Track any kind of change, for purpose of RSSification, Emails, et al.
		Owner: the user who did it.
		Parent: The Change/Delete object, or the new object.
		Superparent: The site.
		"""
	__storm_table__ = "tracking"
	_discriminator = 17
	_no_crumbs = True
	_proxy = { "site":"superparent" }

	timestamp = DateTime(default_factory=datetime.utcnow)

	def __init__(self, user, obj, site = None):
		super(Tracker,self).__init__()
		self.owner = user
		self.parent = obj
		self.superparent = site or current_request.site
		db.store.add(self)

	def __unicode__(self):
		if self._rec_str or not self.owner or not self.superparent: return super(Tracker,self).__unicode__()
		try:
			self._rec_str = True
			if self.parent:
				return u'‹%s %s: %s changed %s›' % (self.__class__.__name__, self.id, unicode(self.owner), unicode(self.parent))
			else:
				return u'‹%s %s: %s changed %s on %s›' % (self.__class__.__name__, self.id, unicode(self.owner), unicode(self.superparent), unicode(self.timestamp))
		finally:
			self._rec_str = False
	def __str__(self):
		if self._rec_str or not self.owner or not self.superparent: return super(Tracker,self).__str__()
		try:
			self._rec_str = True
			if self.parent:
				return '<%s %s: %s changed %s>' % (self.__class__.__name__, self.id, str(self.owner), str(self.parent))
			else:
				return '<%s %s: %s changed %s on %s>' % (self.__class__.__name__, self.id, str(self.owner), str(self.superparent), str(self.timestamp))
		finally:
			self._rec_str = False
	def __repr__(self):
		return self.__str__()

	@property
	def change_obj(self):
		return self.parent.change_obj
	
	@property
	def is_new(self):
		return not isinstance(self.parent, (Change,Delete))

	@property
	def is_mod(self):
		return isinstance(self.parent, Change)

	@property
	def is_del(self):
		return isinstance(self.parent, Delete)


	
class UserTracker(Object):
	"""\
		Record that a change be reported to a user. This will be auto-built from Tracker and WantTracking objects.
		Owner: the user who owns the tracker.
		Parent: The tracker object this is reporting on.
		Superparent: the WantTracker that's responsible.
		"""
	__storm_table__ = "usertracking"
	_discriminator = 18
	_no_crumbs = True
	_proxy = { "user":"owner", "tracker":"parent" }

	def __init__(self, user, tracker, want):
		super(UserTracker,self).__init__()
		self.owner = user
		self.superparent = want
		self.parent = tracker

	def __unicode__(self):
		if self._rec_str or not self.owner or not self.parent: return super(Tracker,self).__unicode__()
		try:
			self._rec_str = True
			return u'‹%s %s: %s for %s›' % (self.__class__.__name__, self.id, unicode(self.parent), unicode(self.owner))
		finally:
			self._rec_str = False
	def __str__(self):
		if self._rec_str or not self.owner or not self.parent: return super(Tracker,self).__str__()
		try:
			self._rec_str = True
			return '<%s %s: %s for %s>' % (self.__class__.__name__, self.id, str(self.parent), str(self.owner))
		finally:
			self._rec_str = False
	def __repr__(self):
		return self.__str__()

	@property
	def change_obj(self):
		return self.parent.change_obj


class WantTracking(Object):
	"""
		Record that a user wants changes reported.
		Parent: The object which should be tracked.
		Owner: The user who wants the tracking.
		email: send email when this happens.
		track_new/_mod/_del: track new / modified / deleted content
		"""
	__storm_table__ = "wanttracking"
	_discriminator = 19
	_display_name = "Beobachtungs-Eintrag"
	_proxy = { "obj":"parent", "user":"owner" }

	discr = Int(allow_none=True)
	email = Bool(allow_none=False) # send mail, not just RSS/on-site?
	track_new = Bool(allow_none=False) # alert for new data?
	track_mod = Bool(allow_none=False) # alert for modifications?
	track_del = Bool(allow_none=False) # alert for deletions?

	def __init__(self, user,obj, discr=None):
		super(WantTracking,self).__init__()
		self.parent = obj
		self.owner = user
		self.discr = Discriminator.get(discr,obj).id if discr else None
		self.email = False
		self.track_new = False
		self.track_mod = False
		self.track_del = False
	
	def __unicode__(self):
		p,s,o,d = self.pso
		if self._rec_str or not o or not p: return super(WantTracking,self).__unicode__()
		try:
			self._rec_str = True
			return u'‹%s%s %s: %s in %s for %s %s›' % (d,self.__class__.__name__, self.id, "-" if self.discr is None else db.get_by(Discriminator,id=self.discr).name, unicode(p),unicode(o), "-N"[self.track_new]+"-M"[self.track_mod]+"-D"[self.track_del])
		finally:
			self._rec_str = False
	def __str__(self):
		p,s,o,d = self.pso
		if self._rec_str or not o or not p: return super(WantTracking,self).__str__()
		try:
			self._rec_str = True
			return '<%s%s %s: %s in %s for %s %s>' % (d,self.__class__.__name__, self.id, "-" if self.discr is None else db.get_by(Discriminator,id=self.discr).name, str(p),str(o), "-N"[self.track_new]+"-M"[self.track_mod]+"-D"[self.track_del])
		finally:
			self._rec_str = False
	def __repr__(self):
		return self.__str__()

	@property
	def data(self):
		wh = []
		if self.track_new: wh.append("New")
		if self.track_mod: wh.append("Mod")
		if self.track_del: wh.append("Del")
		return u"""\
Object: %s %s
User: %s %s
Type: %s
What: %s
Email: %s

""" % (unicode(self.parent),self.parent.oid(), \
       unicode(self.owner),self.owner.oid(), \
	   db.get_by(Discriminator,id=self.discr).name if self.discr is not None else "None",
	   " ".join(wh) if wh else "-", \
	   "yes" if self.email else "no")


def add_mime(name,typ,subtyp,ext):
	ext = unicode(ext)

	try:
		t = db.get_by(MIMEtype,typ=typ,subtyp=subtyp)
	except NoResult:
		t=MIMEtype()
		t.name = unicode(name)
		t.typ = typ
		t.subtyp = subtyp
		t.ext = ext
		db.store.add(t)
		db.store.flush()
		return t
	else:
		assert name == t.name
		if ext != t.ext:
			try:
				tt = db.get_by(MIMEext,ext=ext)
			except NoResult:
				tt = MIMEext()
				tt.mime = t
				tt.ext = ext
				db.store.add(tt)
				db.store.flush()
		return t

def mime_ext(ext):
	try:
		return db.get_by(MIMEtype,ext=ext)
	except NoResult:
		return db.get_by(MIMEext,ext=ext).mime


class MIMEtype(Storm,DbRepr):
	"""Known MIME Types"""
	__storm_table__ = "mimetype"
	id = Int(primary=True)
	name = Unicode(allow_none=False)
	typ = RawStr(allow_none=False)
	subtyp = RawStr(allow_none=False)
	ext = Unicode(allow_none=False) # primary extension
	exts = ReferenceSet(id,"MIMEext.mime_id")
	
	@property
	def mimetype(self):
		return "%s/%s" % (self.typ,self.subtyp)

	def __str__(self):
		return "<%s %s: .%s %s>" % (self.__class__.__name__, self.id,self.ext,self.mimetype)
	def __unicode__(self):
		return u"‹%s %s: .%s %s›" % (self.__class__.__name__, self.id,self.ext,self.mimetype)
	__repr__ = __str__

def find_mimetype(typ,subtyp=None):
	if subtyp is None:
		typ,subtyp = typ.split("/")
	return db.get_by(MIMEtype,typ=typ, subtyp=subtyp)

class MIMEext(Storm):
	"""Extensions for MIME types"""
	__storm_table__ = "mimeext"
	id = Int(primary=True)
	mime_id = Int()
	mime = Reference(mime_id,MIMEtype.id)
	ext = Unicode(allow_none=False)

	def __str__(self):
		return "<%s %s: %s %s>" % (self.__class__.__name__, self.id,self.ext,str(self.mime))
	def __unicode__(self):
		return u"‹%s %s: %s %s›" % (self.__class__.__name__, self.id,self.ext,unicode(self.mime))
	__repr__ = __str__


def hash_data(content):
	from base64 import b64encode
	try:
		from hashlib import sha1
	except ImportError:
		from sha import sha as sha1
	return b64encode(sha1(content).digest(),altchars="-_").rstrip("=")

class BinData(Object):
	"""
		Stores one data file
		owner: whoever uploaded the thing
		parent: some object this is attached to
		superparent: the storage
		"""
	__storm_table__ = "bindata"
	_discriminator = 22
	_no_crumbs = True
	_proxy = { "storage":"superparent" }

	storage_seq = Int()
	mime_id = Int(allow_none=False)
	mime = Reference(mime_id,MIMEtype.id)
	name = Unicode(allow_none=False)
	hash = RawStr(allow_none=False)
	timestamp = DateTime(default_factory=datetime.utcnow)
	size = Int()

	static_files = ReferenceSet(id, BaseObject.parent_id)

	@staticmethod
	def lookup(content):
		res = db.store.find(BinData, And(BinData.hash == hash_data(content)), BinData.superparent_id != None).one()
		if not res:
			raise NoResult
		return res
			
	def __init__(self,name, ext=None,mimetype=None, content=None, parent=None, storage=None):
		super(BinData,self).__init__()
		if not parent: parent = current_request.site
		if not storage: storage = parent.default_storage
		if mimetype:
			self.mime = mimetype
			if ext:
				assert mimetype == mime_ext(ext),"Extension doesn't match MIME type"
		elif ext:
			self.mime = mime_ext(ext)
		else:
			raise RuntimeError("You need to specify MIME type or extension")
		self.name = name
		self._content = content
		self.hash = hash_data(content)
		self.size = len(content)
		self.owner = current_request.user
		self.parent = parent
		self.superparent = storage
		self._save_content()

	def __str__(self):
		return "<%s %s: %s %s>" % (self.__class__.__name__, self.id,self.name+"."+self.ext,self.mimetype)
	def __unicode__(self):
		return u"‹%s %s: %s %s›" % (self.__class__.__name__, self.id,self.name+"."+self.ext,self.mimetype)
	__repr__ = __str__

	@property
	def content(self):
		if not hasattr(self,"_content"):
			try:
				self._content = open(self.path).read()
			except IOError:
				self._content = open(self.old_path).read()
		return self._content

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

	def _old_get_chars(self):
		if self.id is None:
			db.store.flush()
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

	def _get_chars(self):
		if self.storage_seq is None:
			db.store.flush()
			self.storage_seq = AutoReload
			if self.storage_seq is None:
				return "???"
		id = self.storage_seq-1
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

	def _move_old(self):
		op = self.old_path
		np = self.path
		if op != np:
			try:
				os.rename(op,np)
			except OSError:
				pass

	@property
	def path(self):
		fn = self.superparent.path
		fc = self._get_chars()
		dir = os.path.join(fn,*fc[:-1])
		if not os.path.isdir(dir):
			os.makedirs(dir)
		fn = os.path.join(dir,fc[-1])
		return fn

	@property
	def old_path(self):
		fn = self.superparent.path
		fc = self._old_get_chars()
		return os.path.join(fn,*fc)

	def get_absolute_url(self):
		fc = self._get_chars()
		fn = self.superparent.url + "/".join(fc)
		return fn
	
	def delete(self):
		p = self.path
		if os.path.exists(p):
			os.remove(p)
		super(BinData,self).delete()

#	def __storm_pre_flush__(self):
#		super(BinData,self).__storm_pre_flush__()
#		if self._content is None:
#			raise RuntimeError("Need to set content before saving")
#		self._save_content()

	def _save_content(self):
		p = self.path
		if os.path.exists(p):
			raise RuntimeError("File exists")
		try:
			open(p,"w").write(self.content)
		except BaseException:
			if os.path.exists(p):
				os.remove(p)
			raise



class StaticFile(Object):
	"""\
		Record that a static file belongs to a specific site.
		Superparent: The site.
		Parent: The storage.
		"""
	__storm_table__ = "staticfile"
	_discriminator = 20
	_no_crumbs = True
	_proxy = { "bindata":"parent" }

	path = Unicode(allow_none=False)
	modified = DateTime(default_factory=datetime.utcnow)

	def __storm_pre_flush__(self):
		self.modified = datetime.utcnow()
		super(StaticFile,self).__storm_pre_flush__()

	def __init__(self, path, bin):
		super(StaticFile,self).__init__()
		self.path = path
		self.superparent = current_request.site
		self.parent = bin
		
	def __unicode__(self):
		if self._rec_str or not self.superparent or not self.parent: return super(StaticFile,self).__unicode__()
		try:
			self._rec_str = True
			return u'‹%s %s: %s in %s›' % (self.__class__.__name__, self.id, self.path, unicode(self.superparent))
		finally:
			self._rec_str = False
	def __str__(self):
		if self._rec_str or not self.superparent or not self.parent: return super(StaticFile,self).__str__()
		try:
			self._rec_str = True
			return '<%s %s: %s in %s>' % (self.__class__.__name__, self.id, self.path, str(self.superparent))
		finally:
			self._rec_str = False
	def __repr__(self):
		return self.__str__()
	@property
	def hash(self):
		return self.bindata.hash
	@property
	def content(self):
		return self.bindata.content
	@property
	def mimetype(self):
		return self.bindata.mimetype



class Comment(renderObject):
	"""\
		A comment (or similar) page.
		Parent: The comment or page we're referring to.
		Superparent: The main page thus commented.
		Owner: Whoever created the comment
		"""
	__storm_table__ = "comment"
	_discriminator = 23
	
	name = Unicode()
	data = Unicode()
	added = DateTime(default_factory=datetime.utcnow)
	renderer_id = Int(allow_none=True)
	renderer = Reference(renderer_id,Renderer)

	def __init__(self, obj, name, data, renderer = None):
		super(Comment,self).__init__()
		self.name = name
		self.data = data
		self.owner = current_request.user
		self.parent = obj
		if isinstance(obj,Comment):
			self.superparent = obj.superparent
		else:
			self.superparent = obj

		super(Comment,self).__init__(renderer)

