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

from datetime import datetime,timedelta

from sqlalchemy.orm import relationship,backref

from ...utils import random_string
from .. import config
from ..db import db, NoData, check_unique,no_update
from . import LEN_NAME,LEN_DOC
from ._utils import Loadable
from .object import Object,ObjectRef
from .objtyp import ObjType
from .config import ConfigData
from .user import User

## VerifierBase

VerifierBases = {}
class VerifierBase(Loadable, Object):
	"""
		Class for verification subsystems.
		"""

	__tablename__ = "verifierbase"

	name = db.Column(db.Unicode(LEN_NAME), unique=True, nullable=False)
	doc = db.Column(db.Unicode(LEN_DOC), nullable=True)

	config = ObjectRef(ConfigData, lazy="joined")

	def setup(self,name,doc=None,**kw):
		self.name = name
		self.config = ConfigData.new("Verifier "+name)
		if doc is not None:
			self.doc = doc
		super(VerifierBase,self).setup(**kw)

	def create_for(self, obj, user=None,*a,**k):
		"""Create a verifier for this object"""
		if user is None:
			user = request.user
		obj = self.mod.create(obj=obj, user=user, *a,**k) or obj
		return Verifier.new(user=user or request.user, base=self, obj=obj)

## Verifier

class Verifier(Object):
	"""
		Verification emails (or similar).
		"""
	__tablename__ = "verifiers"
	@classmethod
	def __declare_last__(cls):
		check_unique(cls,"user obj base")
		super(Verifier,cls).__declare_last__()

	obj = ObjectRef(doc="The object (or access thereto) to be verified")
	user = ObjectRef(User, doc="The user who shall be granted access")
	base = ObjectRef(VerifierBase)

	code = db.Column(db.Unicode(30), nullable=False)

	added = db.Column(db.DateTime,default=datetime.utcnow, nullable=False)
	repeated = db.Column(db.DateTime,nullable=True)
	timeout = db.Column(db.DateTime,nullable=False)

	def setup(self,base, obj, user=None, code=None, days=None):

		if isinstance(base, basestring):
			base = VerifierBase.q.get_by(name=unicode(base))

		self.base = base
		self.obj = obj
		self.user = user or obj
		assert self.owner and self.parent and self.superparent

		self.code = code or random_string(20,dash="-",dash_step=5)
		self.timeout = datetime.utcnow() + timedelta((days or 10),0) ## ten days

		super(Verifier,self).setup()

	@property
	def as_str(self):
		return u'%s for %s' % (self.base.name, self.obj)

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

