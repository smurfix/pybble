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

from flask import current_app,g,request
from flask.ext.security import UserMixin, RoleMixin
from flask._compat import string_types

from werkzeug import security
from werkzeug.utils import cached_property

from datetime import datetime,timedelta

from sqlalchemy import Integer, Unicode, DateTime, Boolean, ForeignKey, and_,or_, event
from sqlalchemy.orm import relationship,backref
from sqlalchemy.orm.base import NO_VALUE,NEVER_SET
from sqlalchemy.types import TypeDecorator, VARCHAR

from ... import ANON_USER_NAME
from ...utils import random_string, AuthError
from ..db import db, NoData, check_unique,no_update
from ..utils import hybridmethod
from ...globals import current_site
from ._const import PERM,PERM_NONE,PERM_ADMIN,PERM_READ,PERM_ADD,PERM_name,PERM_LIST
from .user import User,Group
from .object import Object,ObjectRef
from .objtyp import ObjType
from .types import MIMEtype
from .tracking import Delete

import sys

import logging
logger = logging.getLogger('pybble.core.models.permit')

access_logger = logging.getLogger('pybble.access')
def log_access(*args):
	access_logger.debug(" ".join(str(x) for x in args))

## Permissions

class Permission(Object):
	"""
		Permission checks: This user can do that to objects of yonder type.

		Inherit=False: only this object
		inherit=True : only to child objects
		inherit=NULL : both.

		objtyp: The object type to be modified
		new_objtyp: The type of object that may be added
		"""
	__tablename__ = "permissions"
	_no_crumbs = True

	_admin_add_perm="*"

	@classmethod
	def __declare_last__(cls):
		check_unique(cls, 'user target right inherit for_objtyp new_objtyp new_mimetyp')
		no_update(cls.user)
		no_update(cls.target)
		super(Permission,cls).__declare_last__()

	@hybridmethod
	def form_mod(self,fs,parent=None):
		if parent is not None:
			if isinstance(parent,(User,Group)):
				f = 'user'
			else:
				f = 'target'
			fs.set(f,parent)
		super(Permission,self).form_mod(fs)

	user = ObjectRef(doc="The user or group who can do things")
	target = ObjectRef(doc="The target which can have things done to it")

	right = db.Column(Integer, nullable=False)
	inherit = db.Column(Boolean, nullable=True, doc="three-valued: False:this, True:descendants, None:Both")

	for_objtyp = ObjectRef(ObjType)
	new_objtyp = ObjectRef(ObjType, nullable=True)
	new_mimetyp = ObjectRef(MIMEtype, nullable=True)

	def setup(self, user, target, for_objtyp=None, right=None, inherit=None, new_objtyp=None,new_mimetyp=None):
		assert right is not None
		if right < 0:
			assert new_objtyp is not None
		else:
			assert new_objtyp is None
		for_objtyp = ObjType.get(target if for_objtyp is None else for_objtyp)
		self.for_objtyp = for_objtyp
		self.right = right
		self.inherit = inherit
		self.user = user
		self.target = target
		self.new_objtyp = new_objtyp
		self.new_mimetyp = new_mimetyp

		if right == PERM_ADD:
			try: del user._can_add
			except AttributeError: pass

		super(Permission,self).setup()
	
	@property
	def as_str(self):
		return u'%s can %s %s %s %s %s/%s' % (unicode(self.user),PERM[self.right],self.for_objtyp.name if self.for_objtyp else "‽",unicode(self.target), "*" if self.inherit is None else "Y" if self.inherit else "N", self.new_objtyp.name if self.new_objtyp is not None else "-", self.new_mimetyp.name if self.new_mimetyp is not None else "-")

for a,b in PERM.iteritems():
	def can_do_closure(a,b):
		def can_do(self, obj, objtyp=None, new_objtyp=None,new_mimetyp=None):
			if objtyp is None and obj is not None:
				objtyp = obj.type
			if current_app.config.DEBUG_ACCESS:
				log_access("can_"+b+":", self,obj,objtyp,new_objtyp,new_mimetyp)
			if a > PERM_NONE:
				return self.can_do(obj, objtyp=objtyp, new_objtyp=new_objtyp,new_mimetyp=new_mimetyp, want=a) >= a
			else:
				return self.can_do(obj, objtyp=objtyp, new_objtyp=new_objtyp,new_mimetyp=new_mimetyp, want=a) == a
		can_do.__doc__ = "Check if this user/group/whatever can %s an object" % \
			(b.lower() if a > PERM_NONE else "do nothing with",)

		def will_do(self, obj, objtyp=None, new_objtyp=None,new_mimetyp=None):
			if current_app.config.DEBUG_ACCESS:
				log_access("will_"+b+":", self,obj,objtyp,new_objtyp,new_mimetyp)
			if not can_do(self, obj, objtyp=objtyp, new_objtyp=new_objtyp,new_mimetyp=new_mimetyp):
				raise AuthError(obj,a)

		return can_do,will_do
	
	c,d = can_do_closure(a,b)
	setattr(Object,'can_'+b.lower(), c)
	setattr(Object,'will_'+b.lower(), d)


def permit(user,obj, right, objtyp=None, new_objtyp=None,new_mimetyp=None, inherit=None):
	if right >= PERM_NONE:
		pq = [Permission.right >= 0]
	else:
		pq = [Permission.right == right]

	objtyp = ObjType.get(obj if objtyp is None else objtyp)
	if inherit is not None:
		pq.append(or_(Permission.inherit == None, Permission.inherit == inherit))

	p = list(Permission.q.filter_by(user=user, target=obj, for_objtyp=objtyp, new_objtyp=new_objtyp,new_mimetyp=new_mimetyp).filter(*pq))
	
	if p:
		if p[0].inherit is None and inherit is not None:
			assert len(p) == 1
			p = p[0]
			if p.right >= right:
				return # nothing to do
			Change(p,{'inherit':(p.inherit,not inherit)})
			p.inherit = not inherit
		elif p[0].inherit is not None and inherit is None:
			permit(user,obj, right, objtyp, new_objtyp,new_mimetyp, inherit=False)
			permit(user,obj, right, objtyp, new_objtyp,new_mimetyp, inherit=True)
			return
		else:
			assert len(p) == 1
			p = p[0]
			if p.right >= right:
				return # nothing to do
			Change.new(p,{'right':(p.right,right)})
			p.right = right
			return
	p = Permission.new(user,obj,objtyp,right,inherit,new_objtyp=new_objtyp,new_mimetyp=new_mimetyp)
	logger.debug("New: {}".format(p))

def forbid(user,obj, objtyp=None, inherit=None,new_objtyp=None,new_mimetyp=None, right=PERM_LIST):
	if right >= PERM_NONE:
		pq = [Permission.right >= right]
	else:
		pq = [Permission.right == want]
	if inherit is not None:
		pq.append(or_(Permission.inherit == None, Permission.inherit == inherit))
	p = list(Permission.q.filter_by(user=u, target=obj, for_objtyp=objtyp,new_objtyp=new_objtyp,new_mimetyp=new_mimetyp).filter(*pq))
	
	assert len(p) <= 2
	if not p:
		return
	def fix(x):
		if right < PERM_LIST:
			logger.debug("Del: {}".format(x))
			Delete.new(x)
		else:
			Change.new(x,{'right':(x.right,right-1)})
			x.right = right-1
	if inherit is None:
		while p:
			fix(p.pop())
		return

	assert len(p) == 1
	p = p[0]

	if p.inherit is None: # and inherit is not None
		if right <= PERM_LIST:
			Change.new(p,{'inherit':(p.inherit,not inherit)})
			p.inherit = not inherit
		else:
			orig_right = p.right
			p.inherit = not inherit
			p.right = right-1
			Change.new(p,{'right':(p.right,right-1),'inherit':(p.inherit,not inherit)})
			Permission.new(p.user,p.obj,p.objtyp,orig_right,not p.inherit,new_objtyp=new_objtyp,new_mimetyp=new_mimetyp)
	else:
		fix(p)
	
def can_do(user,obj, objtyp=None, new_objtyp=None,new_mimetyp=None, want=None):
	"""Recursively get the permission of this user for that (type of) object."""

	ru = getattr(request,"user",None)
#	if obj != current_site and \
#		ru and ru.can_admin(current_site, objtyp=current_site.type):
#		if current_app.config.DEBUG_ACCESS:
#			log_access("ADMIN",obj)
#		return want if want and want < 0 else PERM_ADMIN
#
#		if want>0 and want<=PERM_READ and obj.owner==user:
#			if current_app.config.DEBUG_ACCESS:
#				log_access("OWN",obj)
#			return want

	if current_app.config.DEBUG_ACCESS:
		log_access("PERM", objtyp or "-", (str(new_objtyp) if new_objtyp else "-")+'/'+(str(new_mimetyp) if new_mimetyp else "-"), (PERM_name(want) if want else "-")+":",obj,"FOR",user,"AT",current_site, u"⇒")

	pq = []
	if want is not None:
		if want >= PERM_NONE:
			pq.append(Permission.right >= want)
		else:
			pq.append(Permission.right == want)
	else:
		pq.append(Permission.right >= 0)
	if objtyp is None and want < 0:
		objtyp = obj

	if objtyp is not None:
		objtyp = ObjType.get(objtyp)
		pq.append(Permission.for_objtyp == objtyp)

	if new_objtyp is not None:
		new_objtyp = ObjType.get(new_objtyp)
		pq.append(Permission.new_objtyp == new_objtyp)
	if new_mimetyp is not None:
		new_mimetyp = ObjType.get(new_mimetyp)
		pq.append(Permission.new_mimetyp == new_mimetyp)

	inherited = False
	done = set()
	while obj:
		if current_app.config.DEBUG_ACCESS:
			log_access("Checking",obj)
		if obj in done:
			raise ValueError("Parent recursion on "+repr(obj))
		done.add(obj)

		p = Permission.q.filter(and_(or_(Permission.for_objtyp == None, Permission.for_objtyp == objtyp) if objtyp is not None else (Permission.for_objtyp == None),
										or_(Permission.inherit == inherited, Permission.inherit == None),
										Permission.target == obj,
										or_(Permission.user == u for u in user.groups), ## includes the user itself!
										*pq)).order_by(Permission.right.desc())
		p = p.first()
		if p is not None:
			if current_app.config.DEBUG_ACCESS:
				log_access(p)
			p = p.right
			return p

		inherited = True
		obj = getattr(obj,'parent',None)

	if current_app.config.DEBUG_ACCESS:
		log_access("NONE")
	return PERM_NONE

