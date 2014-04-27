# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, division, unicode_literals
##
## This is part of Pybble, a WMS (Whatever Management System) based on
## Jinja2/Haml, Werkzeug, Flask, and Optimism.
##
## Pybble is Copyright © 2009-2014 by Matthias Urlichs <matthias@urlichs.de>,
## it is licensed under the GPLv3. See the file `README.md` for details
## as well as hopeful statements by the author.
##
## This paragraph is auto-generated and may self-destruct at any time.
## Please do not remove the next line, or insert any blank lines before it.
##BP

from flask import current_app,g

from datetime import datetime,timedelta

from sqlalchemy import Integer, Unicode, DateTime, ForeignKey
from sqlalchemy.orm import relationship,backref

from pybble.compat import py2_unicode

from ..db import Base, Column, NoData

from pybble.utils import random_string

from werkzeug import import_string
from pybble.core import config

from . import ObjectRef
from ._descr import D

VerifierBases = {}
class VerifierBase(Base):
	"""
		Class for verification subsystems.
		"""

	__tablename__ = "verifierbase"
	name = Column(Unicode(30), nullable=False)
	cls = Column(Unicode(100), nullable=False)
	doc = Column(Unicode(1000), nullable=True)
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
			v = VerifierBase.q.get_by(name=name)
		except NoData:
			v=VerifierBase(name=name, cls=cls)
			db.store.add(v)
		else:
			assert v.cls == cls

@py2_unicode
class Verifier(ObjectRef):
	"""
		Verification emails (or similar).
		Parent: the thing to be verified.
		Owner: the user who's asked.
		"""
	__tablename__ = "verifiers"
	_descr = D.Verifier

	base_id = Column(Integer, ForeignKey(VerifierBase.id), index=True)
	base = relationship(VerifierBase, primaryjoin=base_id==VerifierBase.id)

	code = Column(Unicode(30), nullable=False)

	added = Column(DateTime,default=datetime.utcnow, nullable=False)
	repeated = Column(DateTime,nullable=True)
	timeout = Column(DateTime,nullable=False)

	def __init__(self,base, obj, user=None, code=None, days=None):
		super(Verifier,self).__init__()
		if isinstance(base, basestring):
			base = VerifierBase.q.get_by(name=unicode(base))
		self.base = base
		self.parent = obj
		self.owner = user or obj
		self.code = code or random_string(20,dash="-",dash_step=5)
		self.timeout = datetime.utcnow() + timedelta((days or 10),0) ## ten days

	def __str__(self):
		p,s,o,d = self.pso
		if self._rec_str or not p: return super(Verifier,self).__str__()
		try:
			self._rec_str = True
			return u'‹%s%s %s: %s for %s›' % (d,self.__class__.__name__, self.id, self.base.name, unicode(p))
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

