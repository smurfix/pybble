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

from flask import current_app,g, request

from werkzeug import import_string

from datetime import datetime,timedelta

from sqlalchemy import Integer, Unicode, DateTime, ForeignKey
from sqlalchemy.orm import relationship,backref

from ...utils import random_string
from .. import config
from ..db import Column, NoData, check_unique,no_update
from . import Loadable, ObjectRef
from ._descr import D

## VerifierBase

VerifierBases = {}
class VerifierBase(Loadable, ObjectRef):
	"""
		Class for verification subsystems.
		"""

	__tablename__ = "verifierbase"
	_descr = D.VerifierBase

	@classmethod
	def __declare_last__(cls):
		no_update(cls.path)

	name = Column(Unicode(30), unique=True, nullable=False)
	doc = Column(Unicode(1000), nullable=True)

	def new(self, obj, user=None,*a,**k):
		"""Return a new verifier for me and the current user."""
		if user is None:
			user = request.user
		obj = self.mod.new(obj=obj, user=user, *a,**k) or obj
		return Verifier(user=user or request.user, base=self, obj=obj)

## Verifier

class Verifier(ObjectRef):
	"""
		Verification emails (or similar).
		Parent: the thing to be verified.
		Owner: the user who asked.
		SuperParent: the VerifierBase object this refers to.
		"""
	__tablename__ = "verifiers"
	_descr = D.Verifier
	@classmethod
	def __declare_last__(cls):
		if not hasattr(cls,'obj'):
			cls.obj = cls.parent
		if not hasattr(cls,'base'):
			cls.base = cls.superparent
		if not hasattr(cls,'user'):
			cls.user = cls.owner
		check_unique(cls,"user obj base")

	code = Column(Unicode(30), nullable=False)

	added = Column(DateTime,default=datetime.utcnow, nullable=False)
	repeated = Column(DateTime,nullable=True)
	timeout = Column(DateTime,nullable=False)

	def __init__(self,base=None, obj=None, user=None, code=None, days=None, **kw):
		super(Verifier,self).__init__(**kw)

		if isinstance(base, basestring):
			base = VerifierBase.q.get_by(name=unicode(base))

		if self.superparent is None:
			self.superparent = base
		else:
			assert base is None

		if self.parent is None:
			self.parent = obj
		else:
			assert obj is None

		if self.owner is None:
			self.owner = user or obj
		else:
			assert user is None
		assert self.owner and self.parent and self.superparent
		self.code = code or random_string(20,dash="-",dash_step=5)
		self.timeout = datetime.utcnow() + timedelta((days or 10),0) ## ten days

	@property
	def as_str(self):
		p,s,o,d = self.pso
		if self._rec_str or not p: return "‽"
		try:
			self._rec_str += 1
			return u'%s for %s' % (self.base.name, unicode(p))
		finally:
			self._rec_str -= 1

	@property
	def expired(self):
		return self.timeout < datetime.utcnow()
	
	def send(self,*a,**k):
		"""Send the data to the user"""
		return self.base.mod.send(self,*a,**k)

	def entered(self,*a,**k):
		"""The user entered the code. Redirect to whatever."""
		return self.base.mod.entered(self,*a,**k)

	def confirmed(self,*a,**k):
		"""Confirmation page. Redirect to whatever."""
		return self.base.mod.confirmed(self,*a,**k)

	def retry(self,*a,**k):
		"""The user entered the code too late, or whaveter. Redirect to request page."""
		return self.base.mod.retry(self,*a,**k)

