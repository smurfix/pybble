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
from .types import MIMEtype
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

	def __init__(self, adapter, data, source, name=None, parent=None, **kw):
		super(Template,self).__init__(**kw)
		if name is None:
			name = source
		if parent is None:
			parent = request.site
		self.name = name
		self.source=source
		self.content = data
		self.adapter = adapter
		self.owner = request.user
		self.parent = parent

	@property
	def as_str(self):
		return self.name+": "+str(self.adapter.translator.mime) if self.adapter and self.adapter.translator else "‽"

	@property
	@maybe_stale
	def translator(self):
		res = self.adapter.translator
		return res.mod(self)

	@maybe_stale
	def render(self,c,**vars):
		return self.translator(c,**vars)

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
		check_unique(cls, "obj template inherit")
		no_update(cls.obj)
		no_update(cls.template)

	inherit = Column(Boolean, nullable=True)
	weight = Column(Integer, nullable=False, default=0, doc="preference when there are conflicts. Less is better.")

	from_mime = property(lambda s:s.template.from_mime)
	to_mime = property(lambda s:s.template.to_mime)

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
			self._rec_str += 1
			return u'%s of %s on %s %s shows %s' % (TM_DETAIL[self.detail],self.for_discr.name,p, "*" if self.inherit is None else "Y" if self.inherit else "N", s)
		finally:
			self._rec_str -= 1
 
 	@property
	def data(self):
		return self.template.data

def _ref_descr(mapper, connection, obj):
	if obj.inherit is False and obj.parent is not None:
		assert obj.for_discr == obj.parent.discr
event.listen(TemplateMatch, 'before_insert', _ref_descr)
event.listen(TemplateMatch, 'before_update', _ref_descr)

