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

"""
	Change tracking: updated and deleted objects
	"""

from datetime import datetime,timedelta

from sqlalchemy import Integer, Unicode, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship,backref

from flask import request, current_app

from . import LEN_DOC
from .object import Object,ObjectRef
from .objtyp import ObjType
from .user import User,Group
from .site import Site
from ..db import Base, Column, check_unique, db, JSON
from ..utils import hybridmethod
from ...globals import current_site
from ...core import config
from ...core.signal import ObjDeleted

class TrackingObject(Object):
	__abstract__ = True
	"""Objects of this subclass cannot get changes recorded"""
	pass

## Breadcrumb

class Breadcrumb(TrackingObject):
	"""\
		Track page visits.
		Superparent: The site.
		objtyp: mirrors parent.objtyp, for easier selectage
		"""
	__tablename__ = "breadcrumbs"
	_no_crumbs = True

	user = ObjectRef(User, doc="The user whodunit")
	obj = ObjectRef(doc="accessed page")
	site = ObjectRef(Site)

	#seq = Column(Integer)
	visited = Column(DateTime,default=datetime.utcnow)
	last_visited = Column(DateTime,nullable=True)
	cur_visited = Column(DateTime,default=datetime.utcnow, nullable=True)
	counter = Column(Integer, default=0)

	@property
	def parent(self):
		return self.user

	def setup(self, user, obj):
		self.user = user
		self.obj = obj
		self.site = current_site

		super(Breadcrumb,self).setup()

	@property
	def as_str(self):
		return u'%s saw %s on %s' % (self.user, self.obj, self.visited)

	def visit(self):
		now = datetime.utcnow()
		if self.cur_visited is None or self.cur_visited < now-timedelta(0,60):
			self.last_visited = self.visited
			self.visited = now
			self.counter += 1
		self.cur_visited = now

## Change

class Change(TrackingObject):
	"""\
		Track content changes.
		"""
	__tablename__ = "changes"
	_no_crumbs = True

	obj = ObjectRef()
	data = Column(JSON)

	@property
	def parent(self):
		return self.obj

	@property
	def tracker(self):
		return Tracker.q.get_by(obj=self)

	def setup(self, obj, user=None, data=None, comment=None):
		self.obj = obj
		self.data = data
		self._owner = user or request.user
		self._comment = comment

		super(Change,self).setup()

	def after_insert(self):
		Tracker.new(self, user=self._owner, comment=self._comment)

	@property
	def as_str(self):
		return u'changed %s' % (self.obj)

## Delete

class Delete(TrackingObject):
	"""\
		Track deleted content.
		"""
	__tablename__ = "deleted"
	_no_crumbs = True

	@classmethod
	def __declare_last__(cls):
		check_unique(cls,"obj")
		super(Delete,cls).__declare_last__()

	obj = ObjectRef(doc="the deleted object")

	@property
	def parent(self):
		return self.obj

	@property
	def tracker(self):
		return Tracker.q.get_by(obj=self)

	timestamp = Column(DateTime,default=datetime.utcnow)

	def setup(self, obj, user=None, comment=None):
		assert obj and not isinstance(obj,TrackingObject)
		obj._deleting = True
		self._user = user or request.user
		self.obj = obj
		self._comment = comment

		obj.deleted = True
		super(Delete,self).setup()
	
	def after_insert(self):
		Tracker.new(self, user=self._user, comment=self._comment)
		self.obj.signal.send(ObjDeleted)
		self.obj.signal.dispose()

	@property
	def as_str(self):
		return u'deleted %s' % (self.obj,)

## Tracker

class Tracker(TrackingObject):
	"""\
		Track any kind of change, for purpose of RSSification, Emails, et al.
		Owner: the user who did it.
		Parent: The Change/Delete object, or the new object.
		Superparent: The site. TODO: or the high-level action which triggered this one.
		"""
	__tablename__ = "tracking"
	_no_crumbs = True

	user = ObjectRef(User)
	site = ObjectRef(Site)
	obj = ObjectRef(doc="The new object, or a change/delete record")
	comment = Column(Unicode(LEN_DOC), nullable=True)
	timestamp = Column(DateTime,default=datetime.utcnow)

	@property
	def parent(self):
		return self.obj

	def setup(self, obj, user=None,site=None, comment=None):
		# You can track Change and Delete objects, but not e.g. a Tracker or a Breadcrumb
		assert obj and (isinstance(obj,(Change,Delete)) or not isinstance(obj,TrackingObject))

		self.user = user or request.user
		self.comment = comment
		self.obj = obj
		self.site = site or current_site
		super(Tracker,self).setup()

#	def after_insert(self):
#		db.flush((self.owner,)) # required to guard against cycles
#		self.parent = self._obj
#		self.superparent = self._site or current_site

	@property
	def as_str(self):
		return u'%s changed %s' % (self.user, self.obj)

	@property
	def is_new(self):
		return not isinstance(self.obj, (Change,Delete))

	@property
	def is_mod(self):
		return isinstance(self.obj, Change)

	@property
	def is_del(self):
		return isinstance(self.obj, Delete)

## WantTracking

class WantTracking(Object):
	"""
		Record that a user wants changes reported.
		(The "user" can in fact be a web site, if you want to create generic RSS.)
		email: send email when this happens.
		track_new/_mod/_del: track new / modified / deleted content
		"""
	_display_name = "Monitor entry"

	target = ObjectRef(doc="the hierarchy you want to watch")
	user = ObjectRef(doc="the user/?? you want to attach the RSS to")
	for_objtyp = ObjectRef(ObjType, nullable=True)

	@property
	def parent(self):
		return self.user
	
	@hybridmethod
	def form_mod(self,fs,parent):
		if parent is not None:
			if isinstance(parent,(User,Group)):
				fs.set('user',parent)
			else:
				fs.set('target',parent)
		super(WantTracking,self).form_mod(fs)

	email = Column(Boolean, nullable=False) # send mail, not just RSS/on-site?
	track_new = Column(Boolean, nullable=False) # alert for new data?
	track_mod = Column(Boolean, nullable=False) # alert for modifications?
	track_del = Column(Boolean, nullable=False) # alert for deletions?

	def setup(self, user,target, for_objtyp=None):
		self.user = user
		self.target = target
		self.for_objtyp = for_objtyp
		self.email = False
		self.track_new = False
		self.track_mod = False
		self.track_del = False
		super(WantTracking,self).setup()
	
	@property
	def as_str(self):
		return u'%s in %s for %s %s' % ("-" if self.for_objtyp is None else self.for_objtyp.name, self.user,self.target, "-N"[self.track_new]+"-M"[self.track_mod]+"-D"[self.track_del])

## UserTracker

class UserTracker(TrackingObject):
	"""\
		Record that a change be reported to a user. This will be auto-built from Tracker and WantTracking objects.
		"""
	__tablename__ = "usertracking"
	_no_crumbs = True

	user = ObjectRef(User)
	tracker = ObjectRef(WantTracking)
	obj = ObjectRef(doc="The new object / change / delete record")

	@property
	def parent(self):
		return self.user

	def setup(self, tracker, obj):
		self.user = tracker.user
		self.obj = obj
		self.tracker = tracker
		super(UserTracker,self).setup()

	@property
	def as_str(self):
		return '%s for %s' % (self.tracker, self.obj)

	@property
	def change_obj(self):
		return self.parent.change_obj

check_unique(UserTracker,"user tracker")

