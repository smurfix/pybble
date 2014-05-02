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

from datetime import datetime,timedelta

from sqlalchemy import Integer, Unicode, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from flask import request,current_app

from .. import config
from ..db import Base, Column, no_autoflush
from . import Object,ObjectRef, TM_DETAIL, Discriminator
from ._descr import D
from .types import MIMEtype, mime_ext

class Template(ObjectRef):
	"""
		A template for rendering.
		parent: Site the template applies to.
		owner: user who created the template.
		"""
	_descr = D.Template

	@classmethod
	def __declare_last__(cls):
		cls.site = cls.parent

	name = Column(Unicode(30), nullable=False)
	data = Column(Unicode(100000))
	modified = Column(DateTime,default=datetime.utcnow)

	mime_id = Column(Integer, ForeignKey(MIMEtype.id), nullable=False, index=True)
	mime = relationship(MIMEtype, primaryjoin=mime_id==MIMEtype.id)

	@no_autoflush
	def __init__(self, name, data, parent=None, **kw):
		super(Template,self).__init__(**kw)
		self.name = name
		self.data = data
		self.owner = request.user
		self.parent = parent or current_app.site
		self.superparent = getattr(parent,"site",None) or current_app.site

		dot = name.rindex(".")
		self.mime = mime_ext(name[dot+1:])

class TemplateMatch(ObjectRef):
	"""
		Associate a template to an object.
		Parent: The object which the template is for.
		"""
	__tablename__ = "template_match"
	_descr = D.TemplateMatch
	@classmethod
	def __declare_last__(cls):
		cls.obj = cls.parent

	data = Column(Unicode(100000))
	modified = Column(DateTime,default=datetime.utcnow)

	for_discr_id = Column('discr',Integer, ForeignKey(Discriminator.id), nullable=False)
	for_discr = relationship(Discriminator, primaryjoin=for_discr_id==Discriminator.id)

	detail = Column(Integer, nullable=False)
	inherit = Column(Boolean, nullable=True)

	def __init__(self, obj,discr,detail, data, **kw):
		discr = Discriminator.get(discr,obj)
		super(TemplateMatch,self).__init__(**kw)
		self.for_discr = discr
		self.detail = detail
		self.data = data
		db.store.add(self)
		self.parent = obj
		db.store.flush()
	
	@property
	def as_str(self):
		p,s,o,d = self.pso
		if self._rec_str or not p: return "‽"
		try:
			self._rec_str = True
		finally:
			return u'%s %s %s %s' % (TM_DETAIL[self.detail],self.for_discr.name,unicode(p), "*" if self.inherit is None else "Y" if self.inherit else "N")
			self._rec_str = False

