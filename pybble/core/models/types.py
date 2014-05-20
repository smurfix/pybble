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

from flask._compat import text_type

from sqlalchemy import Integer, Unicode, ForeignKey, DateTime, or_, UniqueConstraint
from sqlalchemy.orm import relationship,backref
from sqlalchemy import event

from ...compat import py2_unicode
from .. import config
from ..db import Base, Column, db, NoData, refresh, check_unique
from ..json import register_object
from . import ObjectRef,Loadable, Discriminator
from ._descr import D,MIMEproperty

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
				db.flush((tt,))
		return t

## MIME type

class MIMEtype(Loadable, ObjectRef):
	"""Known MIME Types"""
	_descr = D.MIMEtype
	__tablename__ = "mimetype"

	name = Column(Unicode(30), nullable=False)
	typ = Column(Unicode(30), nullable=False)
	subtyp = Column(Unicode(30), nullable=False)
	doc = Column(Unicode(1000), nullable=True)
	ext = Column(Unicode(10), nullable=True) # primary extension
	
	to_discr_id = Column(Integer, ForeignKey(Discriminator.id), nullable=True, unique=True)
	to_discr = relationship(Discriminator, primaryjoin=to_discr_id==Discriminator.id)
	__table_args__ = (UniqueConstraint(typ,subtyp),)

	def setup(self, typ,subtyp, name=None, ext=None,doc=None):
		if typ == "pybble":
			discr = getattr(D,subtyp,None)
		else:
			discr = None
		if name is None:
			name = typ+'/'+subtyp
		self.typ = typ
		self.subtyp = subtyp
		self.name = name
		self.ext = ext
		self.doc = doc
		self.to_discr_id = discr
		super(MIMEtype,self).setup()

	@classmethod
	def get(cls, typ,subtyp=None, add=False):
		if subtyp is None:
			if isinstance(typ,MIMEtype):
				return typ
			typ = text_type(typ)
			try:
				typ,subtyp = typ.split('/')
			except ValueError:
				try:
					return cls.q.get(or_(cls.name==typ, cls.ext==typ))
				except NoData:
					try:
						return MIMEext.q.get_by(ext=typ).mime
					except NoData:
						raise KeyError("Could not find MIME type "+typ)
		else:
			subtyp = text_type(subtyp)
		try:
			return cls.q.get_by(typ=typ,subtyp=subtyp)
		except NoData:
			if not add:
				raise KeyError("Could not find MIME type "+typ+'/'+subtyp)
			return cls(typ=typ,subtyp=subtyp)

	@property
	def as_str(self):
		return str(self)
	def __str__(self):
		return self.typ+'/'+self.subtyp
	def __repr__(self):
		return u"‹%s %s: .%s %s›" % (self.__class__.__name__, self.id,self.ext,str(self))

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

## A translator is code which interprets a template.

class MIMEtranslator(Loadable, ObjectRef):
	"""\
		Describes a translator of one type to another.

		`mime` is the type for the template's content (need an editor for that …).
		"""
	__tablename__ = "mimetrans"
	_descr = D.MIMEtranslator
	@classmethod
	def __declare_last__(cls):
		if not hasattr(cls,'mime'):
			cls.mime = cls.owner
		check_unique(cls, "mime")

	name = Column(Unicode(30), unique=True, nullable=False)
	weight = Column(Integer, nullable=False,default=0, doc="Used when translating from A to B to C. Less is better.")

	@classmethod
	def get(cls, mime, from_mime,to_mime):
		try:
			return cls.q.get_by(mime=mime,from_mime=from_mime,to_mime=to_mime)
		except NoData:
			if from_mime.subtyp != '*':
				from_mime=MIMEtype.get(from_mime.typ,"*")
				return cls.q.get_by(mime=mime,from_mime=from_mime,to_mime=to_mime)
			raise

	def __call__(self,*a,**k):
		"""Call the underlying translator"""
		return self.mod().__call__(*a,**k)

	@property
	def as_str(self):
		return u"%s: %s" % (self.name,self.mime)

## An adapter links a translator to a specific type combination.

class MIMEadapter(ObjectRef):
	"""\
		Describes an adapter of one type to another.

		`from_mime` and `to_mime` are the managed types.
		"""
	__tablename__ = "mimeadapt"
	_descr = D.MIMEadapter
	@classmethod
	def __declare_last__(cls):
		if not hasattr(cls,'from_mime'):
			cls.from_mime = cls.parent
		if not hasattr(cls,'to_mime'):
			cls.to_mime = cls.superparent
		if not hasattr(cls,'translator'):
			cls.translator = cls.owner
		check_unique(cls, "from_mime to_mime translator")

	name = Column(Unicode(30), unique=True, nullable=False)
	doc = Column(Unicode(1000), nullable=True)
	weight = Column(Integer, nullable=False,default=0, doc="Used when translating from A to B to C. Less is better.")

	@classmethod
	def get(cls, mime, from_mime,to_mime):
		try:
			return cls.q.get_by(mime=mime,from_mime=from_mime,to_mime=to_mime)
		except NoData:
			if from_mime.subtyp != '*':
				from_mime=MIMEtype.get(from_mime.typ,"*")
				return cls.q.get_by(mime=mime,from_mime=from_mime,to_mime=to_mime)
			raise

	def __call__(self,*a,**k):
		"""Call the underlying translator"""
		return self.mod().__call__(*a,**k)

	def __str__(self):
		return u"‹%s %s: %s➙%s›" % (self.__class__.__name__, self.id,unicode(self.from_mime),unicode(self.to_mime))
	__repr__ = __str__

## Serializer for MIME type to JSON

@register_object
class _serialize_mimetype(object):
	cls = MIMEtype
	clsname = "mime"

	@staticmethod
	def encode(obj):
		res = {"t":(obj.typ,obj.subtyp), "s":str(obj)}
		if obj.ext is not None:
			res['x'] = obj.ext
		return res

	@staticmethod
	def decode(t=None,s=None,x=None,**_):
		return MIMEtype.q.get_by(typ=t[0],subtyp=t[1])

@register_object
class _serialize_mimetranslator(object):
	cls = MIMEtranslator
	clsname = "mimetrans"

	@staticmethod
	def encode(obj):
		res = {"i":(obj.id), "s":str(obj)}
		return res

	@staticmethod
	def decode(i,s=None,x=None,**_):
		return MIMEtranslator.q.get_by(id=i)

@register_object
class _serialize_mimeadapter(object):
	cls = MIMEadapter
	clsname = "mimeadapt"

	@staticmethod
	def encode(obj):
		res = {"i":(obj.id), "s":str(obj)}
		return res

	@staticmethod
	def decode(i,s=None,**_):
		return MIMEadapter.q.get_by(id=i)

