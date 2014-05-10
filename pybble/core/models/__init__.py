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

from sqlalchemy import Integer, Unicode, ForeignKey
from sqlalchemy import event, select, func, and_
from sqlalchemy.orm import relationship,backref
from sqlalchemy.orm.base import NO_VALUE,NEVER_SET
from sqlalchemy.inspection import inspect

from ...compat import py2_unicode
from ..json import register_object

from ..db import Base, Column, IDrenderer, db, NoData, maybe_stale
from ..signal import ObjSignal

from flask import request,current_app
from flask._compat import text_type, string_types
from werkzeug import import_string
from jinja2.utils import Markup
from copy import copy

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

class Loadable(object):
	path = Column(Unicode(100), nullable=False, unique=True, doc="Python object name")
	_module = None

	@property
	def mod(self):
		"""Load the module"""
		if self._module is None:
			self._module = import_string(self.path)
		return self._module

class Dumpable(object):
	"""\
		A mix-in which declares a dict-like property that contains the
		actual object data.
		"""
	def _dump(self, add_none=False, cols=None):
		"""\
			Override with read-only one-to-many links
			"""
		return self._as_dict(add_none,cols)

	def _dump_attrs(self):
		i = inspect(self)
		res = set()
		for k in i.dict.keys():
			if k.startswith('_'):
				continue
			if k.endswith('_id'):
				k = k[:-3]
			res.add(k)
		return res
		
	def _as_dict(self, add_none=False, cols=None):
		"""\
			Override with extra settable properties
			"""
		if cols is None:
			cols = self._dump_attrs()
		res = {}
		for k in cols:
			v = getattr(self,k)
			if add_none or v is not None:
				res[k] = v
		return res

	@property
	def as_dict(self):
		return self._as_dict()

@py2_unicode
class Discriminator(Loadable, Dumpable, Base):
	"""Discriminator for Object"""
	__tablename__ = "discriminator"

	name = Column(Unicode(30), nullable=False, unique=True)
	doc = Column(Unicode(250), nullable=True)

	def __str__(self):
		return u'‹D:%s %s›' % (self.id, self.name)
	def __repr__(self):
		return '<D:%s %s>' % (self.id, self.name)

	
	@staticmethod
	def get(discr, obj=None):
		if discr is None and obj is None:
			return None
		if discr is not None and obj is not None:
			discr = Discriminator.get(discr)
			assert obj.discr is discr, (obj.discr,discr)
			return discr
		if isinstance(discr, string_types):
			try: discr = int(discr)
			except ValueError: pass
		if isinstance(discr, Discriminator):
			return discr
		elif isinstance(discr, string_types):
			return Discriminator.q.get_by(name=text_type(discr))
		elif isinstance(discr, (int,long)):
			return Discriminator.q.get_by(id=discr)
		else:
			return Discriminator.q.get_by(id=discr._discriminator)

	@staticmethod
	def num(discr):
		if discr is None:
			return None
		if isinstance(discr, string_types):
			try: discr = int(discr)
			except ValueError: pass
		if isinstance(discr, Discriminator):
			return discr.id
		elif isinstance(discr, string_types):
			return Discriminator.q.get_by(name=text_type(discr)).id
		elif isinstance(discr, (int,long)):
			return discr
		else:
			return discr._discriminator

@register_object
class _discr(object):
	"""
	Encode+decode objects in JSON.

	TODO: For external consumption, mangle the OID one-way
	(i.e. just drop the hash part) if the current user cannot
	read the object.
	"""
	cls = Discriminator
	clsname = "discr"

	@staticmethod
	def encode(obj):
		return {"d":obj.id,"s":str(obj)}

	@staticmethod
	def decode(d,s=None,**_):
		return Discriminator.q.get_by(id=d)

@py2_unicode
class Object(Dumpable, Base):
	"""The base type of all pointed-to objects."""
	__tablename__ = "obj"
	__mapper_args__ = {'polymorphic_on': 'discr_id'}
	#__abstract__ = True

	id = Column(Integer, primary_key=True, label="ID", renderer=IDrenderer)

	owner_id = Column(Integer,ForeignKey(id), index=True)       # user who created this node
	parent_id = Column(Integer,ForeignKey(id), index=True)      # direct ancestor (replied-to comment)
	superparent_id = Column(Integer,ForeignKey(id), index=True) # indirect ancestor (replied-to wiki page)
	## XXX The individual tables should document the semantics of these pointers if they don't match
	
	children = relationship("Object", backref=backref('parent', remote_side=[id]), foreign_keys=(parent_id,))
	superchildren = relationship("Object", backref=backref('superparent', remote_side=[id]), foreign_keys=(superparent_id,))
	owned = relationship("Object", backref=backref('owner', remote_side=[id]), foreign_keys=(owner_id,))

	discr_id = Column("discriminator", Integer, ForeignKey(Discriminator.id), nullable=False)
	discr = relationship(Discriminator, primaryjoin=discr_id==Discriminator.id)

	_rec_str = False ## marker for possibly-recursive __str__ calls

## causes a sqlalchemy warning. TODO: create a testcase and submit a bug report
#	@classmethod
#	def __declare_last__(cls):
#		@event.listens_for(Object.superparent, 'set')
#		def block_super_updates(target, value, oldvalue, initiator):
#			if oldvalue not in (NO_VALUE,NEVER_SET):
#				raise RuntimeError("You cannot change an object's ID".format(target,oldvalue))

	@property
	def as_str(self):
		if hasattr(self,"name"):
			return self.name
		else:
			return None
		
	@maybe_stale
	def __str__(self):
		if self.deleted: d = "DEL "
		else: d = ""
		s = self.as_str
		if s is None:
			s = ""
		else:
			s = " "+s
		return u'‹%s%s:%s%s›' % (d,self.__class__.__name__, self.id, s)

	def __repr__(self):
		try:
			return str(self)
		except Exception as err:
			if self.deleted: d = "DEL "
			else: d = ""
			return '<%s%s: ?? %s>' % (self.__class__.__name__, self.id, str(err))
	
	@property
	def signal(self):
		"""\
			A unique and site-wide signaller for this object.
			See ``blinker.Signal`` for details.
			"""
		return ObjSignal(self)

	def _dump(self):
		"""\
			Fetch the referring objects. This can be a whole lot!
			TODO: limit by only fetching when requested
		"""
		res = super(Object,self)._dump()

		for d in ('children','superchildren','owned'):
			got = {}
			for discr,filter,num in getattr(self,'discr_'+d):
				got[discr.name] = filter.all()
			if got:
				res[d] = got
		return res

	@property
	@maybe_stale
	def deleted(self):
		if self.id is None:
			db.flush()
		return self.parent_id is None and self.superparent_id is None and self.owner_id is None
	
	#all_children = relation('Object', backref=backref("superparent", remote_side=Object.id)) 

	def _all_X(self,attr, discr=None, want=PERM_LIST):
		"""Return all sub-objects of a specific type and permission level"""
		res = Object.q.filter_by(**{attr:self})
		if discr:
			discr = Discriminator.num(discr)
			res = res.filter_by(discr_id=discr)
		for o in res:
			if want is None or not hasattr(request,'user') or request.user.can_do(o, discr=discr, want=want):
				yield o
	def all_children(self, discr=None, want=PERM_LIST):
		return self._all_X("parent",discr,want)
	def all_superchildren(self, discr=None, want=PERM_LIST):
		return self._all_X("superparent",discr,want)
	def all_owned(self, discr=None, want=PERM_LIST):
		return self._all_X("owner",discr,want)

	def has_children(self, discr=None, want=None):
		return len(self._all_x("parent",discr, want=want))
	def has_superchildren(self, discr=None, want=None):
		return len(self._all_x("superparent",discr, want=want))
	def has_owned(self, discr=None, want=None):
		return len(self._all_x("owner",discr, want=want))

	def _discr_X(self,attr):
		"""\
			Return a list of types which point to this object.
			Used for grouped listing in the admin:
			for d in X.discr_children:
				for o in X.all_children(d):
					yield d,o # or whatever

			"""
		s = select((Object.discr_id, func.count()),
			whereclause=getattr(Object,attr)==self, 
		    group_by=Object.discr_id, order_by=Object.discr_id)
		for discr,num in db.execute(s).fetchall():
			yield Discriminator.get(discr), Object.q.filter(and_(Object.discr_id==discr, getattr(Object,attr)==self)).order_by(Object.id), num
	@property
	def discr_children(self):
		return self._discr_X("parent")
	@property
	def discr_superchildren(self):
		return self._discr_X("superparent")
	@property
	def discr_owned(self):
		return self._discr_X("owner")

#	@property
#	def site(self):
#		raise RuntimeError("This code should no longer be necessary")
#
#		from .site import Site
#
#		found = set()
#		while self:
#			if isinstance(self,Site):
#				return self
#
#			if self in found:
#				return None
#			found.add(self)
#
#			if self.deleted:
#				from .tracking import Delete
#				try:
#					d = Delete.q.get_by(parent=self)
#				except NoData:
#					return None
#				else:
#					self = d.superparent
#			elif self.parent and self.parent not in found:
#				self = self.parent
#			elif self.superparent and self.superparent not in found:
#				self = self.superparent
#			else:
#				return None

	@property
	def templates(self):
		q = [ TemplateMatch.parent_id == self.id ]
		return TemplateMatch.q.filter_by(parent=self).order_by(TemplateMatch.discr,TemplateMatch.detail,TemplateMatch.inherit)

	def all_memberships(self, discr=None):
		"""Return all objects (of some type?) I am a member of."""
		discr = Discriminator.num(discr)
		for t in self._member_rules:
			q = dict(t.args)
			q[t.src] = self
			for m in t.table.q.filter_by(**q):
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
		return db.filter_by(WantTracking,parent=self, user=request.user)

	@property
	def classname(self):
		return self.__class__.__name__

	@property
	def classdiscr(self):
		return self.discr

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
		return Change.q.filter_by(parent == self).order_by(Change.timestamp.desc()).first()

	@property
	def pso(self): # parent/super/owner/deletedFlag
		if self.deleted:
			from .tracking import Delete
			try:
				d = Delete.q.get_by(parent=self)
			except NoData:
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
			db.flush()
		return "%d.%d.%s" % (self.discr_id, self.id, 
		                        md5(self.__class__.__name__ + str(self.id) + current_app.config.SECRET_KEY)\
		                            .digest().encode('base64').strip('\n =')[:10].replace("+","/-").replace("/","_"))

	def get_template(self, detail=TM_DETAIL_PAGE):
		"""\
			Return this object's template at a given detail level.

			This code tries to do the right thing when confronted with
			deleted pages (get "before" data) or nested sites (use them
			if seen on standard parent/child path).
			"""
		discr = self.discr

		no_inherit = True
		obj = self
		seen = set()
		got_site = False
		try_super = True
		while obj:
			p,s,o,d = obj.pso
			seen.add(obj)
			t = TemplateMatch.q.get(and_(or_(TemplateMatch.inherit != no_inherit, TemplateMatch.inherit == None),
									TemplateMatch.obj == obj, TemplateMatch.discr == discr, TemplateMatch.detail == detail))
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
			elif request.site not in seen:
				obj = request.site # last resort
			else:
				break

			no_inherit = False

		raise NoData("Template %d for %s" % (detail,str(self)))

	@property
	def data(self):
		raise NotImplementedError("You need to override .data in «%s»" % (self.__class__.__name__,))

	def uptree(self):
		while self:
			yield self
			ru = getattr(request,"user",None)
			if isinstance(self,Site) and not (ru and ru.can_admin(self)):
				return
			self = self.parent

	def record_creation(self):
		"""Record the fact that a user created this object"""
		Tracker(self)

	def record_change(self,content=None,comment=None):
		"""Record the fact that a user changed this object, and why"""
		from .tracking import Change

		if content is None:
			content = self.data
		Change(self,data=content,comment=comment)

	def record_deletion(self,comment=None):
		"""Record the fact that a user killed this object, and why"""
		from .tracking import Delete
		Delete(self,comment=comment)

	@property
	def default_storage(self):
		"""Some objects may have a 'storage' attribute."""
		s = getattr(self,"storage",None)
		if s:
			return s
		if self.parent is None:
			return None
		return self.parent.default_storage

## TODO: does not work yet
@event.listens_for(Object.id, 'set')
def block_id_updates(target, value, oldvalue, initiator):
	if oldvalue not in (NO_VALUE,NEVER_SET):
		raise RuntimeError("You cannot change an object's ID".format(target,oldvalue))

@event.listens_for(Object.superparent_id, 'set')
def block_super_updates(target, value, oldvalue, initiator):
	if oldvalue not in (NO_VALUE,NEVER_SET):
		raise RuntimeError("You cannot change an object's ID".format(target,oldvalue))

#@event.listens_for(Object.superparent, 'set')
#def block_super_updates(target, value, oldvalue, initiator):
#	if oldvalue not in (NO_VALUE,NEVER_SET):
#		raise RuntimeError("You cannot change an object's ID".format(target,oldvalue))

class ObjectMeta(type(Object)):
	def __init__(cls, name, bases, dct):
		if '_descr' in dct:
			xid = dct.get('id',None)
			if xid is None:
				xid = Column(None, ForeignKey(Object.id, ondelete='CASCADE', onupdate='RESTRICT'), primary_key=True)
				setattr(cls,'id',xid)
			xmp = dct.get('__mapper_args__',None)
			if xmp is None:
				xmp = {}
				setattr(cls,'__mapper_args__',xmp)
			xmp.setdefault('polymorphic_identity',dct['_descr'])
			xmp.setdefault('inherit_condition', xid == Object.id)
			# xmp.setdefault('primary_key',(xid,))
			## DO NOT enable this line. It is wrong.
			if '__tablename__' not in dct:
				setattr(cls,'__tablename__',name.lower())
			if "modified" in dct:
				event.listen(cls,'before_update',update_modified)

		super(ObjectMeta, cls).__init__(name, bases, dct)

def update_modified(mapper, connection, target):
	"""Utility helper for event.listen('before_update')"""
	target.modified = datetime.utcnow()

class ObjectRef(Object):
	__metaclass__ = ObjectMeta
	def __init__(self,*a,**k):
		super(ObjectRef,self).__init__(*a,**k)
		db.add(self)

	#__abstract__ = True
	## this would prevent inheritance from working
	## but fortunately, as the class is otherwise empty, it doesn't matter

@register_object
class _obj(object):
	"""
	Encode+decode objects in JSON.

	TODO: For external consumption, mangle the OID one-way
	(i.e. just drop the hash part) if the current user cannot
	read the object.
	"""
	cls = Object
	clsname = "obj"

	@staticmethod
	def encode(obj):
		return {"i":obj.oid(),"s":str(obj)}

	@staticmethod
	def decode(i,s=None,**_):
		return obj_get(id=i)

def obj_class(id):
	"""Given a discriminator ID, return the referred object's class."""
	return Discriminator.get(id).mod

def obj_get(oid):
	"""Given an object ID, return the object"""
	try:
		cid,id,hash = oid.split(".")
	except ValueError:
		raise ValueError("bad OID: '%s'" % (oid,))
	cls = Discriminator.get(cid).mod
	obj = cls.q.get_by(id=int(id))
	if oid != obj.oid():
		raise ValueError("This object does not exist: " % (oid,))
	return obj

class Renderer(Loadable,Base):
	"""Render method for object content"""
	name = Column(Unicode(30), nullable=False)
	doc = Column(Unicode(250), nullable=True)

class renderObject(Object):
	"""\
		An object with render().
		You do need to add a renderer_id foreign key, and a data field.
		"""

	__abstract__ = True
	renderer_id = Column(Integer, nullable=True)
	renderer = relationship(Renderer, primaryjoin=renderer_id==Renderer.id)

	def __init__(self,renderer = None):
		if renderer is not None:
			if not isinstance(renderer,Renderer):
				renderer = Renderer.q.get_by(name=renderer)
			self.renderer = renderer
	
	@property
	def render(self):
		if self.renderer_id is None:
			return None
		def _wrap(r):
			def _call(*a,**k):
				r(self,*a,**k)
			return _call
		try:
			return _wrap(Renderer.q.get_by(id=self.renderer_id)._module)
		except NoData:
			def _wr(*a,**k):
				return "<pre>"+Markup.escape(self.data)+"<pre>\n"
			return _wr

