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

import sys
import marshal
from datetime import datetime,timedelta

from sqlalchemy import Integer, Unicode, DateTime, Boolean, ForeignKey, PickleType
from sqlalchemy import event
from sqlalchemy.orm import relationship

from flask import request,current_app
from werkzeug.utils import cached_property

from .. import config
from ..db import Base, Column, no_update,check_unique, db, refresh, maybe_stale
from . import Object,ObjectRef, TM_DETAIL, Discriminator
from ._descr import D
from .types import MIMEtype,MIMEadapter,MIMEtranslator
from ._content import Cached,_Content

## Template

_not_cached = "not compiled"

class Template(_Content, Cached, ObjectRef):
	"""
		A template for rendering.
		parent: Object the template applies to.
		owner: the user who created the template.
		superparent: an adapter which links MIME types.

		"""
	_descr = D.Template

	@classmethod
	def __declare_last__(cls):
		if not hasattr(cls,'site'):
			cls.site = cls.parent
		if not hasattr(cls,'adapter'):
			cls.adapter = cls.superparent
		check_unique(cls, "parent name")

		# Drop cached data when the content changes
		def _del_cache(target, value, oldvalue, initiator):
			target.del_cache()
		event.listen(cls.content, 'set', _del_cache)

	name = Column(Unicode(30), nullable=False, index=True)
	modified = Column(DateTime,default=datetime.utcnow)
	weight = Column(Integer, nullable=False, default=0, doc="preference when there are conflicts. Less is better.")

	source = Column(Unicode(1000), nullable=True, doc="original file this template was loaded from")
	## so we can dump it back to the file system after editing

	from_mime = property(lambda s: s.adapter.from_mime)
	to_mime = property(lambda s: s.adapter.to_mime)

	@cached_property
	def mime(self):
		return self.translator.mime

	def setup(self, adapter, data, source, parent, name=None, weight=None):
		if name is None:
			name = source
		if parent is None:
			parent = request.site

		self.name = name
		self.source = source
		self.content = data
		self.adapter = adapter
		self.owner = request.user
		self.parent = parent
		if weight is not None:
			self.weight = weight

		super(Template,self).setup()

	@property
	def as_str(self):
		return self.name+": "+(str(self.adapter.translator.mime) if isinstance(self.adapter,MIMEadapter) and isinstance(self.adapter.translator,MIMEtranslator) else "‽")

	@property
	@maybe_stale
	def translator(self):
		res = self.adapter.translator
		return res.mod(self)

	@maybe_stale
	def render(self,c,params):
		return self.translator(c,params)

## TemplateMatch

class TemplateMatch(ObjectRef):
	"""
		Associate a template to an object.

		if Inherit==False, only for_mime==parent.mime makes sense.

		"""
	__tablename__ = "template_match"
	_descr = D.TemplateMatch
	@classmethod
	def __declare_last__(cls):
		if not hasattr(cls,'obj'):
			cls.obj = cls.parent
		if not hasattr(cls,'template'):
			cls.template = cls.superparent
		check_unique(cls, "obj template inherit for_discr")
		no_update(cls.obj)
		no_update(cls.template)

		def _ref_descr(mapper, connection, obj):
			if obj.inherit is False and obj.parent is not None:
				assert obj.for_discr == obj.parent.discr, (obj.for_discr,obj.parent.discr)
		event.listen(cls, 'before_insert', _ref_descr)
		event.listen(cls, 'before_update', _ref_descr)

	inherit = Column(Boolean, nullable=True)
	weight = Column(Integer, nullable=False, default=0, doc="preference when there are conflicts. Less is better.")

	from_mime = property(lambda s:s.template.from_mime)
	to_mime = property(lambda s:s.template.to_mime)

	for_discr_id = Column('discr',Integer, ForeignKey(Discriminator.id), nullable=True)
	for_discr = relationship(Discriminator, primaryjoin=for_discr_id==Discriminator.id)

	def setup(self, obj, template, inherit=None,weight=None, for_discr=None):
		if for_discr is not None:
			for_discr = Discriminator.get(for_discr)

		self.for_discr = for_discr
		self.template = template
		self.obj = obj
		self.inherit = inherit
		if weight is not None:
			self.weight = weight

		super(TemplateMatch,self).setup()
	
	@property
	def as_str(self):
		p,s,o,d = self.pso
		if self._rec_str or not p: return "‽"
		try:
			self._rec_str += 1
			return u'%s on %s %s shows %s' % (self.for_discr.name if self.for_discr else "*",p, "*" if self.inherit is None else "Y" if self.inherit else "N", s)
		finally:
			self._rec_str -= 1
 
 	@property
	def data(self):
		return self.template.data


