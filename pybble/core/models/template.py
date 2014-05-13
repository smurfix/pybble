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

from sqlalchemy import Integer, Unicode, DateTime, Boolean, ForeignKey
from sqlalchemy import event
from sqlalchemy.orm import relationship

from flask import request,current_app

from .. import config
from ..db import Base, Column, no_update,check_unique, db
from . import Object,ObjectRef, TM_DETAIL, Discriminator
from ._descr import D
from .types import MIMEtype, mime_ext

## Template

class Template(ObjectRef):
	"""
		A template for rendering.
		parent: Site the template applies to.
		owner: user who created the template.
		"""
	_descr = D.Template

	@classmethod
	def __declare_last__(cls):
		if not hasattr(cls,'site'):
			cls.site = cls.parent
		check_unique(cls, "parent name")

	name = Column(Unicode(30), nullable=False)
	data = Column(Unicode(100000))
	modified = Column(DateTime,default=datetime.utcnow)

	mime_id = Column(Integer, ForeignKey(MIMEtype.id), nullable=False, index=True)
	mime = relationship(MIMEtype, primaryjoin=mime_id==MIMEtype.id)

	def __init__(self, name, data, parent=None, **kw):
		super(Template,self).__init__(**kw)
		self.name = name
		self.data = data
		self.owner = request.user
		self.parent = parent or request.site
		self.superparent = getattr(parent,"site",None) or request.site

		dot = name.rindex(".")
		self.mime = mime_ext(name[dot+1:])


## TemplateMatch

class TemplateMatch(ObjectRef):
	"""
		Associate a template to an object.

		Parent: The object which the template is for.
		Superparent: The template
		for_discr: data types the template shall be applied to

		if Inherit==False, only for_discr==parent.discr makes sense.

		TODO: Check whether for_discr should be in the template instead
		(or in addition, to speed up searches?)
		"""
	__tablename__ = "template_match"
	_descr = D.TemplateMatch
	@classmethod
	def __declare_last__(cls):
		if not hasattr(cls,'obj'):
			cls.obj = cls.parent
		if not hasattr(cls,'template'):
			cls.template = cls.superparent
		check_unique(cls, "obj template detail for_discr inherit")
		no_update(cls.obj)
		no_update(cls.template)

	for_discr_id = Column('discr',Integer, ForeignKey(Discriminator.id), nullable=False)
	for_discr = relationship(Discriminator, primaryjoin=for_discr_id==Discriminator.id)

	detail = Column(Integer, nullable=False)
	inherit = Column(Boolean, nullable=True)

	def __init__(self, obj, detail, template, for_discr=None, **kw):
		assert "discr" not in kw
		if for_discr is None:
			for_discr = obj.discr
		else:
			for_discr = Discriminator.get(for_discr)
		super(TemplateMatch,self).__init__(**kw)
		self.for_discr = for_discr
		self.detail = detail
		self.template = template
		self.obj = obj
	
	@property
	def as_str(self):
		p,s,o,d = self.pso
		if self._rec_str or not p: return "‽"
		try:
			self._rec_str = True
			return u'%s of %s on %s %s shows %s' % (TM_DETAIL[self.detail],self.for_discr.name,p, "*" if self.inherit is None else "Y" if self.inherit else "N", s)
		finally:
			self._rec_str = False
 
 	@property
	def data(self):
		return self.template.data

def _ref_descr(mapper, connection, obj):
	if obj.inherit is False and obj.parent is not None:
		assert obj.for_discr == obj.parent.discr
event.listen(TemplateMatch, 'before_insert', _ref_descr)
event.listen(TemplateMatch, 'before_update', _ref_descr)

