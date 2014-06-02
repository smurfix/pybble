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
from . import LEN_NAME,LEN_TYPE,LEN_EXT,LEN_DOC
from ._utils import Loadable
from .object import ObjectRef,Object
from .objtyp import ObjType

def add_mime(name,typ,subtyp,ext):
	ext = unicode(ext)

	try:
		t = MIMEtype.q.get_by(typ=typ,subtyp=subtyp)
	except NoData:
		t=MIMEtype.new()
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

class MIMEtype(Object):
	"""Known MIME Types"""
	__tablename__ = "mimetype"

	name = Column(Unicode(LEN_NAME), nullable=False)
	typ = Column(Unicode(LEN_TYPE), nullable=False)
	subtyp = Column(Unicode(LEN_TYPE), nullable=False)
	doc = Column(Unicode(LEN_DOC), nullable=True)
	ext = Column(Unicode(LEN_EXT), nullable=True) # primary extension
	
	to_objtyp = ObjectRef(ObjType, "mimetype", nullable=True,unique=True)
	__table_args__ = (UniqueConstraint(typ,subtyp),)

	def setup(self, typ,subtyp, name=None, ext=None,doc=None,add=None,**kw):
		if add and isinstance(add,ObjType):
			objtyp = add
		elif typ == "pybble" and subtyp not in ("_empty","*"):
			objtyp = ObjType.get(subtyp)
		else:
			objtyp = None
		self.typ = typ
		self.subtyp = subtyp
		self.name = name
		self.ext = ext
		self.doc = doc
		self.to_objtyp = objtyp
		super(MIMEtype,self).setup(**kw)

	@classmethod
	def get(cls, typ,subtyp=None, add=False):
		if subtyp is None:
			if isinstance(typ,MIMEtype):
				return typ
			if isinstance(typ,Object):
				return typ.mime
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
				import pdb;pdb.set_trace()
				raise KeyError("Could not find MIME type "+typ+'/'+subtyp)
			return cls.new(typ=typ,subtyp=subtyp, add=add)

	def before_insert(self):
		if self.name is None:
			self.name = self.typ+'/'+self.subtyp
		super(MIMEtype,self).before_insert()

	@property
	def as_str(self):
		return str(self)
	def __str__(self):
		return self.typ+'/'+self.subtyp
	def __repr__(self):
		return u"‹%s %s: .%s %s›" % (self.__class__.__name__, self.id,self.ext,str(self) if self.typ and self.subtyp else '‹no type›')

## additional MIME filename extensions

class MIMEext(Object):
	"""Extensions for MIME types"""
	__tablename__ = "mimeext"

	mime = ObjectRef(MIMEtype, "exts")
	ext = Column(Unicode(10), nullable=False)

	def setup(self,mime,ext):
		self.mime = mime
		self.ext = ext

	def __str__(self):
		return u"‹%s %s: %s %s›" % (self.__class__.__name__, self.id,self.ext,unicode(self.mime))
	__repr__ = __str__

## A translator is code which interprets a template.

class MIMEtranslator(Loadable, Object):
	"""\
		Describes a translator of one type to another.

		`mime` is the type for the template's content (need an editor for that …).
		"""
	__tablename__ = "mimetrans"
	@classmethod
	def __declare_last__(cls):
		check_unique(cls, "mime")
		super(MIMEtranslator,cls).__declare_last__()

	mime = ObjectRef(MIMEtype)
	name = Column(Unicode(LEN_NAME), unique=True, nullable=False)
	weight = Column(Integer, nullable=False,default=0, doc="Used when translating from A to B to C. Less is better.")

	def setup(self, mime, name,weight=None,**kw):
		self.mime = MIMEtype.get(mime)
		self.name = name
		if weight is not None: self.weight = weight
		super(MIMEtranslator,self).setup(**kw)

	@classmethod
	def get(cls, mime, from_mime,to_mime):
		try:
			return cls.q.get_by(mime=mime,from_mime=from_mime,to_mime=to_mime)
		except NoData:
			if from_mime.subtyp != '*':
				from_mime=MIMEtype.get(from_mime.typ,"*")
				return cls.q.get_by(mime=mime,from_mime=from_mime,to_mime=to_mime)
			raise

	@property
	def as_str(self):
		return u"%s: %s" % (self.name,self.mime)

## An adapter links a translator to a specific type combination.

class MIMEadapter(Object):
	"""\
		Describes an adapter of one type to another.

		`from_mime` and `to_mime` are the managed types.
		"""
	__tablename__ = "mimeadapt"
	@classmethod
	def __declare_last__(cls):
		check_unique(cls, "from_mime to_mime translator")
		super(MIMEadapter,cls).__declare_last__()

	from_mime = ObjectRef(MIMEtype)
	to_mime = ObjectRef(MIMEtype)
	translator = ObjectRef(MIMEtranslator)

	name = Column(Unicode(LEN_NAME), unique=True, nullable=False)
	doc = Column(Unicode(LEN_DOC), nullable=True)
	weight = Column(Integer, nullable=False,default=0, doc="Used when translating from A to B to C. Less is better.")

	def setup(self, translator,from_mime,to_mime, name=None,weight=None,doc=None):
		self.translator = translator
		self.from_mime = from_mime
		self.to_mime = to_mime

		if name is None:
			name = "{} to {} via {}".format(from_mime,to_mime,translator)
		if len(name)>LEN_NAME-10:
			name = name[:LEN_NAME-10]+'…'+str(from_mime.id+to_mime.id+translator.id)
			# This name is too short for auto-populating but too long for humans
		self.name = name
		if weight is not None: self.weight = weight
		super(MIMEadapter,self).setup()

	@classmethod
	def get(cls, mime, from_mime,to_mime):
		try:
			return cls.q.get_by(mime=mime,from_mime=from_mime,to_mime=to_mime)
		except NoData:
			if from_mime.subtyp != '*':
				from_mime=MIMEtype.get(from_mime.typ,"*")
				return cls.q.get_by(mime=mime,from_mime=from_mime,to_mime=to_mime)
			raise

	def __str__(self):
		return u"‹%s %s: %s ➙ %s›" % (self.__class__.__name__, self.id,unicode(self.from_mime),unicode(self.to_mime))
	__repr__ = __str__

