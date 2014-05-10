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

from datetime import datetime

from sqlalchemy import Integer, Unicode, ForeignKey, DateTime
from sqlalchemy.orm import relationship,backref
from sqlalchemy import event

from ...compat import py2_unicode
from .. import config
from ..db import Base, Column, db, NoData
from ..json import register_object
from . import ObjectRef
from ._descr import D

def add_mime(name,typ,subtyp,ext):
	ext = unicode(ext)

	try:
		t = MIMEtype.q.get_by(typ=typ,subtyp=subtyp)
	except NoData:
		t=MIMEtype()
		t.name = unicode(name)
		t.typ = typ
		t.subtyp = subtyp
		t.ext = ext
		db.add(t)
		db.flush()
		return t
	else:
		assert name == t.name
		if ext != t.ext:
			try:
				tt = MIMEext.q.get_by(ext=ext)
			except NoData:
				tt = MIMEext()
				tt.mime = t
				tt.ext = ext
				db.add(tt)
				db.flush()
		return t

def mime_ext(ext):
	try:
		return MIMEtype.q.get_by(ext=ext)
	except NoData:
		return MIMEext.q.get_by(ext=ext).mime

## MIME type

@py2_unicode
class MIMEtype(Base):
	"""Known MIME Types"""
	__tablename__ = "mimetype"

	name = Column(Unicode(30), nullable=False)
	typ = Column(Unicode(30), nullable=False)
	subtyp = Column(Unicode(30), nullable=False)
	doc = Column(Unicode(1000), nullable=True)
	ext = Column(Unicode(10), nullable=True) # primary extension
	
	@property
	def mimetype(self):
		return "%s/%s" % (self.typ,self.subtyp)

	def __str__(self):
		return u"‹%s %s: .%s %s›" % (self.__class__.__name__, self.id,self.ext,self.mimetype)
	__repr__ = __str__

def find_mimetype(typ,subtyp=None):
	if subtyp is None:
		typ,subtyp = typ.split("/")
	return MIMEtype.q.get_by(typ=typ, subtyp=subtyp)

## additional MIME filename extensions

@py2_unicode
class MIMEext(Base):
	"""Extensions for MIME types"""
	__tablename__ = "mimeext"

	mime_id = Column(Integer, ForeignKey(MIMEtype.id), nullable=False, index=True)
	mime = relationship(MIMEtype, primaryjoin=mime_id==MIMEtype.id, backref=backref('exts'))
	ext = Column(Unicode(10), nullable=False)

	def __str__(self):
		return u"‹%s %s: %s %s›" % (self.__class__.__name__, self.id,self.ext,unicode(self.mime))
	__repr__ = __str__

@register_object
class _MIMEtype(object):
	cls = MIMEtype
	clsname = "mime"

	@staticmethod
	def encode(obj):
		## the string is purely for human consumption and therefore does not have a time zone
		res = {"t":(obj.typ,obj.subtyp), "s":str(obj)}
		if obj.ext is not None:
			res['x'] = obj.ext
		return res

	@staticmethod
	def decode(t=None,s=None,x=None,**_):
		return MIMEtype.q.get_by(typ=t[0],subtyp=t[1])

