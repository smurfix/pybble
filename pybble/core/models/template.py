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
from ...globals import current_site
from .object import Object,ObjectRef
from . import LEN_NAME,LEN_PATH
from ._const import TM_DETAIL
from .objtyp import ObjType
from .types import MIMEtype,MIMEadapter,MIMEtranslator
from ._content import Cached,_Content

## Template

_not_cached = "not compiled"

class Template(_Content, Cached, Object):
	"""
		A template for rendering.
		parent: Object the template applies to.
		owner: the user who created the template.
		superparent: an adapter which links MIME types.

		"""

	@classmethod
	def __declare_last__(cls):
		check_unique(cls, "target name")

		# Drop cached data when the content changes
		def _del_cache(target, value, oldvalue, initiator):
			target.del_cache()
		event.listen(cls.content, 'set', _del_cache)
		super(Template,cls).__declare_last__()

	@property
	def parent(self):
		return self.target

	target = ObjectRef()
	adapter = ObjectRef(MIMEadapter)

	name = Column(Unicode(LEN_NAME), nullable=False, index=True)
	modified = Column(DateTime,default=datetime.utcnow)
	weight = Column(Integer, nullable=False, default=0, doc="preference when there are conflicts. Less is better.")

	source = Column(Unicode(LEN_PATH), nullable=True, doc="original file this template was loaded from")
	## so we can dump it back to the file system after editing

	from_mime = property(lambda s: s.adapter.from_mime)
	to_mime = property(lambda s: s.adapter.to_mime)

	@cached_property
	def mime(self):
		return self.adapter.mime

	def setup(self, adapter, data, source, target=None, name=None, weight=None):
		if name is None:
			name = source
		if target is None:
			target = current_site

		self.name = name
		self.source = source
		self.content = data
		self.adapter = adapter
		self.target = target
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

class TemplateMatch(Object):
	"""
		Associate a template to an object.

		if Inherit==False, only for_mime==parent.mime makes sense.

		"""
	__tablename__ = "template_match"
	@classmethod
	def __declare_last__(cls):
		check_unique(cls, "target template inherit for_objtyp")
		no_update(cls.target)
		no_update(cls.template)
		super(TemplateMatch,cls).__declare_last__()

	def before_insert(self):
		self._check_ref_objtyp()
		super(TemplateMatch,self).before_insert()

	def before_update(self):
		self._check_ref_objtyp()
		super(TemplateMatch,self).before_update()

	def _check_ref_objtyp(self):
		if self.inherit is False and self.parent is not None:
			assert self.for_objtyp == self.parent.objtyp, (self.for_objtyp,self.parent.objtyp)

	@property
	def parent(self):
		return self.target

	target = ObjectRef()
	template = ObjectRef(Template)

	inherit = Column(Boolean, nullable=True)
	weight = Column(Integer, nullable=False, default=0, doc="preference when there are conflicts. Less is better.")

	from_mime = property(lambda s:s.template.from_mime)
	to_mime = property(lambda s:s.template.to_mime)

	for_objtyp = ObjectRef(ObjType,nullable=True)

	def setup(self, target, template, inherit=None,weight=None, for_objtyp=None):
		if for_objtyp is not None:
			for_objtyp = ObjType.get(for_objtyp)

		self.for_objtyp = for_objtyp
		self.template = template
		self.target = target
		self.inherit = inherit
		if weight is not None:
			self.weight = weight

		super(TemplateMatch,self).setup()
	
	@property
	def as_str(self):
		return u'%s on %s %s shows %s' % (self.for_objtyp.name if self.for_objtyp else "*",self.target, "*" if self.inherit is None else "Y" if self.inherit else "N", self.template)
 
 	@property
	def data(self):
		return self.template.data


