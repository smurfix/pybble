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

"""
	Change tracking: updated and deleted objects
	"""

from datetime import datetime,timedelta

from sqlalchemy import Integer, Unicode, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship,backref

from pybble.compat import py2_unicode

from ..db import Base, Column

from pybble.utils import current_request

from pybble.core import config

from . import Object,ObjectRef
from ._descr import D

@py2_unicode
class Breadcrumb(ObjectRef):
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

	discr = Column(Integer, nullable=False)
	#seq = Column(Integer)
	visited = Column(DateTime,default=datetime.utcnow)
	last_visited = Column(DateTime,nullable=True)
	cur_visited = Column(DateTime,default=datetime.utcnow, nullable=True)

	def __init__(self, user, obj):
		super(Breadcrumb,self).__init__()
		self.discr = obj.discriminator
		self.owner = user
		self.parent = obj
		self.superparent = current_request.site
		#self.seq = 1+(db.store.execute(select(Max(Breadcrumb.seq), And((Breadcrumb.owner==user,Breadcrumb.discr==self.discr))).scalar() or 0)

	def __str__(self):
		p,s,o,d = self.pso
		if self._rec_str or not o or not p: return super(Breadcrumb,self).__str__()
		try:
			self._rec_str = True
			return u'‹%s%s %s: %s saw %s on %s›' % (d,self.__class__.__name__, self.id, unicode(o), unicode(p), unicode(self.visited))
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

@py2_unicode	
class Change(ObjectRef):
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
	comment = Column(Unicode(1000), nullable=True)

	def __init__(self, user, obj, data, comment = None):
		super(Change,self).__init__()
		self.owner = user
		self.parent = obj
		self.data = data
		self.comment = comment

		session.add(self)
		session.add(Tracker(user,self))

	def __str__(self):
		p,s,o,d = self.pso
		if self._rec_str or not o or not p: return super(Change,self).__str__()
		try:
			self._rec_str = True
			return u'‹%s %s: %s changed %s on %s›' % (self.__class__.__name__, self.id, unicode(o), unicode(p), unicode(self.timestamp))
		finally:
			self._rec_str = False
	def __repr__(self):
		return self.__str__()

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
                	.order_by(-Change.timestamp)\
                	.first()

@py2_unicode
class Delete(ObjectRef):
	"""\
		Track deleted content.
		Owner: the user who did it.
		Parent: The page thus deleted.
		Superparent: the object's original parent.
		"""
	__tablename__ = "deleted"
	_descr = D.Delete
	_no_crumbs = True

	comment = Column(Unicode(1000), nullable=True)

	## The old parent is in self.superparent
	old_owner_id = Column(Integer, ForeignKey(ObjectRef.id), nullable=True, index=True)
	old_superparent_id = Column(Integer, ForeignKey(ObjectRef.id), nullable=True, index=True)
	@property
	def old_parent_id(self): return self.superparent_id

	old_owner = relationship(Object, primaryjoin=old_owner_id==Object.id)
	old_parent = Object._alias('superparent')
	old_superparent = relationship(Object, primaryjoin=old_superparent_id==Object.id)

	timestamp = Column(DateTime,default=datetime.utcnow)

	def __init__(self, user, obj, comment):
		super(Delete,self).__init__()
		self.owner = user
		self.parent = obj
		self.old_owner = obj.owner
		self.superparent = obj.parent
		self.old_superparent = obj.superparent

		session.add(self)
		session.add(Tracker(user,self))

	def __str__(self):
		if self._rec_str or not self.owner or not self.parent: return super(Delete,self).__str__()
		try:
			self._rec_str = True
			return u'‹%s %s: %s deleted %s on %s›' % (self.__class__.__name__, self.id, unicode(self.owner), unicode(self.parent), unicode(self.timestamp))
		finally:
			self._rec_str = False
	def __repr__(self):
		return self.__str__()

	@property
	def change_obj(self):
		return self.parent

@py2_unicode
class Tracker(ObjectRef):
	"""\
		Track any kind of change, for purpose of RSSification, Emails, et al.
		Owner: the user who did it.
		Parent: The Change/Delete object, or the new object.
		Superparent: The site.
		"""
	__tablename__ = "tracking"
	_descr = D.Tracker
	_no_crumbs = True

	site = Object._alias('superparent')

	timestamp = Column(DateTime,default=datetime.utcnow)

	def __init__(self, user, obj, site = None):
		super(Tracker,self).__init__()
		self.owner = user
		self.parent = obj
		self.superparent = site or current_request.site
		session.add(self)

	def __str__(self):
		if self._rec_str or not self.owner or not self.superparent: return super(Tracker,self).__str__()
		try:
			self._rec_str = True
			if self.parent:
				return u'‹%s %s: %s changed %s›' % (self.__class__.__name__, self.id, unicode(self.owner), unicode(self.parent))
			else:
				return u'‹%s %s: %s changed %s on %s›' % (self.__class__.__name__, self.id, unicode(self.owner), unicode(self.superparent), unicode(self.timestamp))
		finally:
			self._rec_str = False
	__repr__ = __str__

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

@py2_unicode
class UserTracker(ObjectRef):
	"""\
		Record that a change be reported to a user. This will be auto-built from Tracker and WantTracking objects.
		"""
	__tablename__ = "usertracking"
	_descr = D.UserTracker
	_no_crumbs = True

	user = ObjectRef._alias('owner')
	tracker = ObjectRef._alias('parent')
	want_tracking = ObjectRef._alias('superparent')

	def __init__(self, user, tracker, want):
		super(UserTracker,self).__init__()
		self.owner = user
		self.superparent = want
		self.parent = tracker

	def __str__(self):
		if self._rec_str or not self.owner or not self.parent: return super(Tracker,self).__str__()
		try:
			self._rec_str = True
			return u'‹%s %s: %s for %s›' % (self.__class__.__name__, self.id, unicode(self.parent), unicode(self.owner))
		finally:
			self._rec_str = False
	__repr__ = __str__

	@property
	def change_obj(self):
		return self.parent.change_obj

@py2_unicode
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

	obj = ObjectRef._alias('parent')
	user = ObjectRef._alias('owner')

	discr = Column(Integer, nullable=True)
	email = Column(Boolean, nullable=False) # send mail, not just RSS/on-site?
	track_new = Column(Boolean, nullable=False) # alert for new data?
	track_mod = Column(Boolean, nullable=False) # alert for modifications?
	track_del = Column(Boolean, nullable=False) # alert for deletions?

	def __init__(self, user,obj, discr=None):
		super(WantTracking,self).__init__()
		self.parent = obj
		self.owner = user
		self.discr = Discriminator.get(discr,obj).id if discr else None
		self.email = False
		self.track_new = False
		self.track_mod = False
		self.track_del = False
	
	def __str__(self):
		p,s,o,d = self.pso
		if self._rec_str or not o or not p: return super(WantTracking,self).__str__()
		try:
			self._rec_str = True
			return u'‹%s%s %s: %s in %s for %s %s›' % (d,self.__class__.__name__, self.id, "-" if self.discr is None else db.get_by(Discriminator,id=self.discr).name, unicode(p),unicode(o), "-N"[self.track_new]+"-M"[self.track_mod]+"-D"[self.track_del])
		finally:
			self._rec_str = False
	__repr__ = __str__

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

