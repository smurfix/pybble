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

from sqlalchemy import Integer, Unicode, DateTime, Boolean
from sqlalchemy.orm import relationship,backref

from pybble.compat import py2_unicode

from ..db import Base, Column

from pybble.core import config

from . import Object,ObjectRef, TM_DETAIL
from ._descr import D

@py2_unicode
class Template(ObjectRef):
	"""
		A template for rendering.
		parent: Site the template applies to.
		owner: user who created the template.
		"""
	_descr = D.Template

	name = Column(Unicode(30), nullable=False)
	data = Column(Unicode(100000))
	modified = Column(DateTime,default=datetime.utcnow)

	site = Object._alias('parent')

	def __storm_pre_flush__(self):
		self.modified = datetime.utcnow()
		super(Template,self).__storm_pre_flush__()

	def __init__(self, name, data, parent=None):
		super(Template,self).__init__()
		self.name = name
		self.data = data
		self.owner = current_request.user
		self.parent = parent or current_request.site
		self.superparent = getattr(parent,"site",None) or current_request.site

	def __str__(self):
		return "‹%s:%d›" % (self.__class__.__name__,self.id)
	def __repr__(self):
		return "'<%s:%d>'" % (self.__class__.__name__,self.id)

@py2_unicode
class TemplateMatch(ObjectRef):
	"""
		Associate a template to an object.
		Parent: The object which the template is for.
		"""
	__tablename__ = "template_match"
	_descr = D.TemplateMatch

	obj = Object._alias('parent')

	data = Column(Unicode(100000))
	modified = Column(DateTime,default=datetime.utcnow)

	def __storm_pre_flush__(self):
		self.modified = datetime.utcnow()
		super(TemplateMatch,self).__storm_pre_flush__()

	discr = Column(Integer, nullable=False)
	detail = Column(Integer, nullable=False)
	inherit = Column(Boolean, nullable=True)

	def __init__(self, obj,discr,detail, data):
		discr = Discriminator.get(discr,obj).id
		super(TemplateMatch,self).__init__()
		self.discr = discr
		self.detail = detail
		self.data = data
		db.store.add(self)
		self.parent = obj
		db.store.flush()
	
	def __str__(self):
		p,s,o,d = self.pso
		if self._rec_str or not p: return super(TemplateMatch,self).__str__()
		try:
			self._rec_str = True
		finally:
			return u'‹%s%s %s: %s %s %s %s›' % (d,self.__class__.__name__, self.id, TM_DETAIL[self.detail],Discriminator.q.get_by(id=self.discr).name,unicode(p), "*" if self.inherit is None else "Y" if self.inherit else "N")
			self._rec_str = False
	def __repr__(self):
		if not self.parent: return "'"+super(TemplateMatch,self).__repr__()+"'"
		return "'"+self.__str__()+"'"

