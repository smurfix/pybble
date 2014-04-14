# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, division
##
## This is part of Pybble, a WMS (Whatever Management System) based on
## Jinja2/Haml, Werkzeug, Flask, and Optimism.
##
## Pybble is Copyright © 2014 by Matthias Urlichs <matthias@urlichs.de>,
## it is licensed under the GPLv3. See the file `README.md` for details
## as well as hopeful statements by the author.
##
## This paragraph is auto-generated and may self-destruct at any time.
## Please do not remove the next line, or insert any blank lines before it.
##BP

from datetime import datetime,timedelta

from sqlalchemy import Integer, Unicode, ForeignKey
from sqlalchemy.orm import relationship

from pybble.compat import py2_unicode

from . import Base, Column

from pybble.utils import random_string, current_request, AuthError

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

@py2_unicode
class Discriminator(Base):
	"""Discriminator for Object"""
	__tablename__ = "discriminator"

	name = Column(Unicode, nullable=False)
	display_name = Column(Unicode, nullable=True)
	infotext = Column(Unicode, nullable=True)

	def __init__(self, cls):
		self.id = cls._discriminator
		self.name = cls.__name__

	def __str__(self):
		return u'‹D:%s=%s›' % (d,self.__class__.__name__, self.id, self.name)
	__repr__ = __str__

	
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

#_discr2cls = {}
#class RegistryMeta(PropertyPublisherMeta):
#	def __init__(self, name, bases, dict):
#		if "_obj" in dict: return
#		self.id = Column(Integer)primary_key=True)
#		self._obj = Reference(self.id, BaseObject.id)
#
#		self.owner_id = Proxy(self._obj, BaseObject.owner_id)
#		self.parent_id = Proxy(self._obj, BaseObject.parent_id)
#		self.superparent_id = Proxy(self._obj, BaseObject.superparent_id)
#
#		for k,v in dict.get("_proxy",{}).iteritems():
#			setattr(self,k+"_id", Proxy(self._obj, getattr(BaseObject,v+"_id")))
#			setattr(self,k,property(_get_ref(v),_set_ref(v)))
#
#		#self.owner = Reference(self.owner_id, BaseObject.id)
#		#self.parent = Reference(self.parent_id, BaseObject.id)
#		#self.superparent = Reference(self.superparent_id, BaseObject.id)
#
#		super(RegistryMeta,self).__init__(name, bases, dict)
#
#		id = getattr(self, "_discriminator", None)
#		if id:
#			_discr2cls[id] = self
#
#		return
#
#		print "*",name
#		try:
#			o = Object
#		except NameError:
#			pass
#		else:
#			relmap = {}
#			for a,b in Object.__dict__.items():
#				if isinstance(b,Proxy):
#					b = copy(b)
#					#b._cls = self
#					setattr(self,a,b)
#					print "Proxy",a
#				elif isinstance(b,Reference):
#					b = copy(b)
#					#b._cls = self
#					setattr(self,a,b)
#					print "Ref",a
#				elif b is Object.id:
#					b = copy(b)
#					setattr(self,a,b)
#					print "Ref",a
#					

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

@py2_unicode
class Object(Base):
	"""The base type of all pointed-to objects."""
	__tablename__ = "obj"
	__mapper_args__ = {'polymorphic_on': discriminator}
	#__abstract__ = True

	owner_id = Column(Integer)       # user who created this node
	parent_id = Column(Integer)      # direct ancestor (replied-to comment)
	superparent_id = Column(Integer) # indirect ancestor (replied-to wiki page)
	## XXX The individual tables should document the semantics of these pointers if they don't match
	
	owned = relationship("Object", backref=backref('owner', remote_side=['id'])
	children = relationship("Object", backref=backref('parent', remote_side=['id'])
	superchildren = relationship("Object", backref=backref('superparent', remote_side=['id'])

	discriminator = Column(Integer, nullable=False)

	@property
	def discr(self): return Discriminator.get(self.discriminator)

	_rec_str = False

	def __str__(self):
		if self.deleted: d = "DEL "
		else: d = ""
		if getattr(self,"name",None):
			return u'‹%s%s %s:%s›' % (d,self.__class__.__name__, self.id, self.name)
		else:
			return u'‹%s%s %s›' % (d,self.__class__.__name__, self.id)
	__repr__ = __str__

	@property
	def deleted(self):
		return self.parent is None and self.superparent is None and self.owner is None
	
	#all_children = relation('Object', backref=backref("superparent", remote_side=Object.id)) 

	def _all_X(self,attr, discr=None, want=PERM_LIST):
		"""Return all sub-objects of a specific type and permission level"""
		res = Object.q.filter(**{attr:self})
		if discr:
			discr = Discriminator.num(discr)
			res = res.filter(discriminator=discr)
		for o in db.store.find(BaseObject, And(*q)):
			if want is None or current_request.user.can_do(o, discr=discr, want=want):
				yield o
	def all_children(self, discr=None, want=PERM_LIST):
		return self._all_X("parent",discr,want)
	def all_superchildren(self, discr=None, want=PERM_LIST):
		return self._all_X("superparent",discr,want)
	def all_owned(self, discr=None, want=PERM_LIST):
		return self._all_X("owner",discr,want)

	def has_children(self, discr=None, want=None):
		return self._all_x("parent",discr, want=want).count()
	def has_superchildren(self, discr=None, want=None):
		return self._all_x("superparent",discr, want=want).count()
	def has_owned(self, discr=None, want=None):
		return self._all_x("owner",discr, want=want).count()

	def _discr_X(self,attr):
		"""\
			Return a list of types which point to this object.
			Used for grouped listing in the admin:
			for d in X.discr_children:
				for o in X.all_children(d):
					yield d,o # or whatever

			"""
		raise NotImplementedError
		s = Select((BaseObject.discriminator, Count()), where=BaseObject.parent_id==self.id, \
		    group_by=BaseObject.discriminator, order_by=BaseObject.discriminator)
		for discr,num in db.store.execute(s):
			c = obj_class(discr)
			yield c, db.filter_by(c,parent=self), num
	@property
	def discr_children(self):
		return self._discr_X("parent")
	@property
	def discr_superchildren(self):
		return self._discr_X("superparent")
	@property
	def discr_owned(self):
		return self._discr_X("owner")

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
					return None
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
		return self.discriminator

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
	def pso(self): # parent/super/owner/deletedFlag
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
	try:
		cid,id,hash = oid.split(".")
	except ValueError:
		raise ValueError("bad OID: '%s'" % (oid,))
	cls = obj_class(int(cid))
	obj = db.get_by(cls, id=int(id))
	if oid != obj.oid():
		raise ValueError("This object does not exist: " % (oid,))
	return obj

class Renderer(Base):
	"""Render method for object content"""
	__tablename__ = "renderer"
	name = Column(Unicode, nullable=False)
	cls = Column(Unicode, nullable=False)
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
	

class renderObject(Object):
	"""\
		An object with render().
		You do need to add a renderer_id foreign key, and a data field.
		"""

	__abstract__ = True
	renderer_id = Column(Integer, nullable=True)
	renderer = Reference(renderer_id,Renderer.id)

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

