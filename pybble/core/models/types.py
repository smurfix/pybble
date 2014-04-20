# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, division
##
## This is part of Pybble, a WMS (Whatever Management System) based on
## Jinja2/Haml, Werkzeug, Flask, and Optimism.
##
## Pybble is Copyright © 2014 by Matthias Urlichs <matthias@urlichs.de>,
## it is licensed under the GPLv3. See the file `README.md` for details
## as well as hopeful statements by the author.
##
## This paragraph is auto-generated and may self-destruct at any time.
## Please do not remove the next line, or insert any blank lines before it.
##BP

from datetime import datetime

from sqlalchemy import Integer, Unicode, ForeignKey, DateTime
from sqlalchemy.orm import relationship,backref
from sqlalchemy import event

from pybble.compat import py2_unicode

from ..db import Base, Column

from pybble.utils import random_string, current_request, AuthError

from werkzeug import import_string
from jinja2.utils import Markup
from pybble.core import config
import sys,os
from copy import copy

from . import DummyObject,ObjectRef, TM_DETAIL_PAGE
from ._descr import D

def add_mime(name,typ,subtyp,ext):
	ext = unicode(ext)

	try:
		t = db.get_by(MIMEtype,typ=typ,subtyp=subtyp)
	except NoResult:
		t=MIMEtype()
		t.name = unicode(name)
		t.typ = typ
		t.subtyp = subtyp
		t.ext = ext
		db.store.add(t)
		db.store.flush()
		return t
	else:
		assert name == t.name
		if ext != t.ext:
			try:
				tt = db.get_by(MIMEext,ext=ext)
			except NoResult:
				tt = MIMEext()
				tt.mime = t
				tt.ext = ext
				db.store.add(tt)
				db.store.flush()
		return t

def mime_ext(ext):
	try:
		return db.get_by(MIMEtype,ext=ext)
	except NoResult:
		return db.get_by(MIMEext,ext=ext).mime

@py2_unicode
class MIMEtype(Base):
	"""Known MIME Types"""
	__tablename__ = "mimetype"

	name = Column(Unicode(30), nullable=False)
	typ = Column(Unicode(30), nullable=False)
	subtyp = Column(Unicode(30), nullable=False)
	doc = Column(Unicode(1000), nullable=True)
	ext = Column(Unicode(10), nullable=False) # primary extension
	exts = ReferenceSet(id,"MIMEext.mime_id")
	
	@property
	def mimetype(self):
		return "%s/%s" % (self.typ,self.subtyp)

	def __str__(self):
		return u"‹%s %s: .%s %s›" % (self.__class__.__name__, self.id,self.ext,self.mimetype)
	__repr__ = __str__

def find_mimetype(typ,subtyp=None):
	if subtyp is None:
		typ,subtyp = typ.split("/")
	return db.get_by(MIMEtype,typ=typ, subtyp=subtyp)

@py2_unicode
class MIMEext(Base):
	"""Extensions for MIME types"""
	__tablename__ = "mimeext"

	mime_id = Column(Integer, ForeignKey(MIMEtype.id), nullable=False, index=True)
	mime = relationship(mime_id,primaryjoin=mime_id==MIMEtype.id)
	ext = Column(Unicode(10), nullable=False)

	def __str__(self):
		return u"‹%s %s: %s %s›" % (self.__class__.__name__, self.id,self.ext,unicode(self.mime))
	__repr__ = __str__
