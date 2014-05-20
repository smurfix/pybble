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

from . import Object,ObjectRef, Discriminator
from ._descr import D
from ..db import Base, Column, check_unique, db
from ...core import config
from ...core.signal import ObjDeleted

class TrackingObjectRef(ObjectRef):
	"""Objects of this subclass cannot get changes recorded"""
	pass

## Breadcrumb

class Breadcrumb(TrackingObjectRef):
	"""\
		Track page visits.
		Owner: the user who did it.
		Parent: The page thus visited.
		Superparent: The site.
		discr: mirrors parent.discr, for easier selectage
		"""
	__tablename__ = "breadcrumbs"
	_descr = D.Breadcrumb
	_no_crumbs = True

	# for_discr is saved here because of faster lookups
	for_discr_id = Column("discr", Integer, ForeignKey(Discriminator.id), nullable=False)
	for_discr = relationship(Discriminator, primaryjoin=for_discr_id==Discriminator.id)

	#seq = Column(Integer)
	visited = Column(DateTime,default=datetime.utcnow)
	last_visited = Column(DateTime,nullable=True)
	cur_visited = Column(DateTime,default=datetime.utcnow, nullable=True)

	def setup(self, user, obj):
		self.for_discr = obj.discr
		self.owner = user
		self.parent = obj

		super(Breadcrumb,self).setup()

	@property
	def as_str(self):
		p,s,o,d = self.pso
		if self._rec_str or not o or not p: return "‽"
		try:
			self._rec_str += 1
			return u'%s saw %s on %s' % (unicode(o), unicode(p), unicode(self.visited))
		finally:
			self._rec_str -= 1

	def visit(self):
		now = datetime.utcnow()
		if self.cur_visited is None or self.cur_visited < now-timedelta(0,600):
			self.last_visited = self.visited
			self.visited = now
		self.cur_visited = now

## Change

class Change(TrackingObjectRef):
	"""\
		Track content changes.
		Owner: the user who did it.
		Parent: The page thus changed.
		"""
	__tablename__ = "changes"
	_descr = D.Change
	_no_crumbs = True

	timestamp = Column(DateTime,default=datetime.utcnow)
	data = Column(Unicode(100000))

	def setup(self, obj, user=None, data=None, comment=None):
		self.owner = user or request.user
		self.parent = obj
		self.data = data
		self._comment = comment

		super(Change,self).setup()

	def after_insert(self):
		Tracker.new(self, user=self.owner, comment=self._comment)

	@property
	def as_str(self):
		p,s,o,d = self.pso
		if self._rec_str or not o or not p: return "‽"
		try:
			self._rec_str += 1
			return u'%s changed %s on %s' % (unicode(o), unicode(p), unicode(self.timestamp))
		finally:
			self._rec_str -= 1

	@property
	def change_obj(self):
		return self.parent

	@property
	def next_change(self):
		return Change.q.filter(Change.timestamp>self.timestamp)\
				.filter(Change.parent==self.parent)\
                	.order_by(Change.timestamp)\
                	.first()
	@property
	def prev_change(self):
		return Change.q.filter(Change.timestamp<self.timestamp)\
				.filter(Change.parent==self.parent)\
                	.order_by(Change.timestamp.desc())\
                	.first()

## Delete

class Delete(TrackingObjectRef):
	"""\
		Track deleted content.
		Owner: the user who did it.
		Parent: The page thus deleted.
		Superparent: the object's original parent.
		"""
	__tablename__ = "deleted"
	_descr = D.Delete
	_no_crumbs = True
	@classmethod
	def __declare_last__(cls):
		if not hasattr(cls,'old_parent'):
			cls.old_parent = cls.superparent
		if not hasattr(cls,'old_parent_id'):
			cls.old_parent_id = cls.superparent_id
		check_unique(cls,"parent")

	## The old parent is in self.superparent
	old_owner_id = Column(Integer, ForeignKey(ObjectRef.id), nullable=True, index=True)
	old_superparent_id = Column(Integer, ForeignKey(ObjectRef.id), nullable=True, index=True)

	old_owner = relationship(Object, primaryjoin=old_owner_id==Object.id)
	old_superparent = relationship(Object, primaryjoin=old_superparent_id==Object.id)

	timestamp = Column(DateTime,default=datetime.utcnow)

	def setup(self, obj, user=None, comment=None):
		assert obj and not isinstance(obj,TrackingObjectRef)
		obj._deleting = True
		self.owner = user or request.user
		self.parent = obj
		self.old_owner = obj.owner
		self.superparent = obj.parent
		self.old_superparent = obj.superparent
		self._comment = comment

		obj.owner = None
		obj.parent = None
		obj.superparent = None
		super(Delete,self).setup()
	
	def after_insert(self):
		Tracker.new(self, user=user, comment=self._comment)
		self.parent.signal.send(ObjDeleted)
		self.parent.signal.dispose()


	@property
	def as_str(self):
		if self._rec_str or not self.owner or not self.parent: return "‽"
		try:
			self._rec_str += 1
			return u'%s deleted %s on %s' % (unicode(self.owner), unicode(self.parent), unicode(self.timestamp))
		finally:
			self._rec_str -= 1

	@property
	def change_obj(self):
		return self.parent

## Tracker

class Tracker(TrackingObjectRef):
	"""\
		Track any kind of change, for purpose of RSSification, Emails, et al.
		Owner: the user who did it.
		Parent: The Change/Delete object, or the new object.
		Superparent: The site. TODO: or the high-level action which triggered this one.
		"""
	__tablename__ = "tracking"
	_descr = D.Tracker
	_no_crumbs = True
	@classmethod
	def __declare_last__(cls):
		if not hasattr(cls,'site'):
			cls.site = cls.superparent

	comment = Column(Unicode(1000), nullable=True)
	timestamp = Column(DateTime,default=datetime.utcnow)

	def setup(self, obj, user=None,site=None, comment=None):
		# You can track Change and Delete objects, but not e.g. a Tracker or a Breadcrumb
		assert obj and (isinstance(obj,(Change,Delete)) or not isinstance(obj,TrackingObjectRef))

		self.owner = user or request.user
		self.comment = comment
		self._obj = obj
		self._site = site
		super(Tracker,self).setup()

	def after_insert(self):
		db.flush((self.owner,)) # required to guard against cycles
		self.parent = self._obj
		self.superparent = self._site or request.site

	@property
	def as_str(self):
		if self._rec_str or not self.owner or not self.superparent: return "‽"
		try:
			self._rec_str += 1
			if self.parent:
				return u'%s changed %s' % (unicode(self.owner), unicode(self.parent))
			else:
				return u'%s changed %s on %s' % (unicode(self.owner), unicode(self.superparent), unicode(self.timestamp))
		finally:
			self._rec_str -= 1

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

## UserTracker

class UserTracker(TrackingObjectRef):
	"""\
		Record that a change be reported to a user. This will be auto-built from Tracker and WantTracking objects.
		"""
	__tablename__ = "usertracking"
	_descr = D.UserTracker
	_no_crumbs = True
	@classmethod
	def __declare_last__(cls):
		if not hasattr(cls,'user'):
			cls.user = cls.owner
		if not hasattr(cls,'tracker'):
			cls.tracker = cls.parent
		if not hasattr(cls,'want_tracking'):
			cls.want_tracking = cls.superparent

	def setup(self, user, tracker, want):
		self.user = user
		self.want_tracking = want
		self.tracker = tracker
		super(UserTracker,self).setup()

	@property
	def as_str(self):
		if self._rec_str or not self.owner or not self.parent: return "‽"
		try:
			self._rec_str += 1
			return '%s for %s' % (unicode(self.parent), unicode(self.owner))
		finally:
			self._rec_str -= 1

	@property
	def change_obj(self):
		return self.parent.change_obj

check_unique(UserTracker,"user tracker")

## WantTracking

class WantTracking(ObjectRef):
	"""
		Record that a user wants changes reported.
		Parent: The object which should be tracked.
		Owner: The user who wants the tracking.
		email: send email when this happens.
		track_new/_mod/_del: track new / modified / deleted content
		"""
	_descr = D.WantTracking
	_display_name = "Beobachtungs-Eintrag"
	@classmethod
	def __declare_last__(cls):
		if not hasattr(cls,'obj'):
			cls.obj = cls.parent
		if not hasattr(cls,'user'):
			cls.user = cls.owner

	for_discr_id = Column("discr", Integer, ForeignKey(Discriminator.id), nullable=True)
	for_discr = relationship(Discriminator, primaryjoin=for_discr_id==Discriminator.id)

	email = Column(Boolean, nullable=False) # send mail, not just RSS/on-site?
	track_new = Column(Boolean, nullable=False) # alert for new data?
	track_mod = Column(Boolean, nullable=False) # alert for modifications?
	track_del = Column(Boolean, nullable=False) # alert for deletions?

	def setup(self, user,obj, for_discr=None):
		self.parent = obj
		self.owner = user
		self.for_discr = for_discr
		self.email = False
		self.track_new = False
		self.track_mod = False
		self.track_del = False
		super(WantTracking,self).setup()
	
	@property
	def as_str(self):
		p,s,o,d = self.pso
		if self._rec_str or not o or not p: return "‽"
		try:
			self._rec_str += 1
			return u'%s in %s for %s %s' % ("-" if self.for_discr is None else self.for_discr.name, unicode(p),unicode(o), "-N"[self.track_new]+"-M"[self.track_mod]+"-D"[self.track_del])
		finally:
			self._rec_str -= 1

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
	   self.for_discr.name if self.for_discr is not None else "None",
	   " ".join(wh) if wh else "-", \
	   "yes" if self.email else "no")

