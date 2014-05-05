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

from flask import current_app,g

from werkzeug import import_string

from datetime import datetime,timedelta

from sqlalchemy import Integer, Unicode, DateTime, ForeignKey
from sqlalchemy.orm import relationship,backref

from ...utils import random_string
from .. import config
from ..db import Column, NoData
from . import Loadable, ObjectRef
from ._descr import D

VerifierBases = {}
class VerifierBase(Loadable, ObjectRef):
	"""
		Class for verification subsystems.
		"""

	__tablename__ = "verifierbase"
	_descr = D.VerifierBase
	name = Column(Unicode(30), nullable=False)
	doc = Column(Unicode(1000), nullable=True)

class Verifier(ObjectRef):
	"""
		Verification emails (or similar).
		Parent: the thing to be verified.
		Owner: the user who's asked.
		"""
	__tablename__ = "verifiers"
	_descr = D.Verifier
	@classmethod
	def __declare_last__(cls):
		cls.base = cls.superparent

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
			self._rec_str = True
			return u'%s for %s' % (self.base.name, unicode(p))
		finally:
			self._rec_str = False

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

