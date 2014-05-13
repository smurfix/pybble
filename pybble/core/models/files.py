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
import logging

from flask import request,current_app

from sqlalchemy import Integer, Unicode, ForeignKey, DateTime
from sqlalchemy.orm import relationship,backref
from sqlalchemy import event

from ...core import config
from ...utils import hash_data
from ..db import Base, Column, db, check_unique,no_update
from . import Object,ObjectRef, update_modified
from ._descr import D
from .types import MIMEtype, mime_ext

import os

logger = logging.getLogger('pybble.core.models.files')

## BinData

class BinData(ObjectRef):
	"""
		Stores (a reference to) one data file
		owner: whoever uploaded the thing
		parent: the object this is attached to
		superparent: the storage

		This object implements a content-based file system: the hash of the
		file contents is an index.
		"""
	_descr = D.BinData
	_no_crumbs = True
	@classmethod
	def __declare_last__(cls):
		if not hasattr(cls,'storage'):
			cls.storage = cls.superparent
		no_update(cls.hash)

	storage_seq = Column(Integer, autoincrement=True, unique=True)
	## The mysql driver ignores autoincrement on non-primary-key columns.
	## Workaround: see end of file.

	mime_id = Column(Integer, ForeignKey(MIMEtype.id), nullable=False, index=True)
	mime = relationship(MIMEtype, primaryjoin=mime_id==MIMEtype.id)
	name = Column(Unicode(30), nullable=False)
	hash = Column(Unicode(33), nullable=True, unique=True) ## NULL if deleted
	timestamp = Column(DateTime,default=datetime.utcnow)
	size = Column(Integer)

	@staticmethod
	def lookup(content):
		return BinData.q.filter(BinData.hash == hash_data(content), BinData.superparent != None).one()
			
	def __init__(self,name, ext=None,mimetype=None, content=None, parent=None, storage=None, **kw):
		super(BinData,self).__init__(**kw)
		if not parent: parent = request.site
		if not storage: storage = parent.default_storage
		if mimetype:
			self.mime = mimetype
			if ext:
				assert mimetype == mime_ext(ext),"Extension doesn't match MIME type"
		elif ext:
			self.mime = mime_ext(ext)
		else:
			raise RuntimeError("You need to specify MIME type or extension")
		self.name = name
		self._content = content
		self.hash = hash_data(content)
		self.size = len(content)
		self.owner = request.user
		self.parent = parent
		self.superparent = storage
		self._save_content()

	@property
	def as_str(self):
		n = self.name
		if self.ext:
			n += "."+self.ext
		return u"%s %s" % (n,self.mimetype)

	@property
	def content(self):
		if not hasattr(self,"_content"):
			try:
				self._content = open(self.path).read()
			except IOError:
				try:
					self._content = open(self.old_path_1).read()
				except IOError:
					self._content = open(self.old_path_2).read()
					self._move_old_2()
				else:
					self._move_old_1()
		return self._content

	@property
	def mimetype(self):
		try:
			return self.mime.mimetype
		except Exception:
			return "???/???"

	@property
	def ext(self):
		try:
			return self.mime.ext
		except Exception:
			return "???"

	def _old1_get_chars(self):
		"""
		Broken: like _old2_get_chars(), and
		* id-based, thus was very sparse
		"""
		if self.id is None:
			db.flush()
			if self.id is None:
				return "???"
		id = self.id-1
		chars = "23456789abcdefghjkmnopqrstuvwxyz"
		midchars = "abcdefghjkmnopq"
		fc = []
		flast = chars[id % len(chars)]
		id = id // len(chars)
		while id:
			c = chars[id % len(midchars)]
			id = id // len(midchars)
			c = chars[id % len(midchars)] + c
			id = id // len(midchars)
			fc.insert(0,c)
		fc.append("_")
		fc.append(self.name+"_"+self.hash[0:10]+flast)
		if self.mime.ext:
			fc[-1] += "."+self.mime.ext
		return fc

	def _old2_get_chars(self):
		"""
		Broken:
		* chars[id % len(midchars)] instead of midchars[id % len(midchars)]
		* missing "id -= 1" after "while id", so there was never an ‘aa’
		  (or ‘22’ …) subdirectory
		"""
		assert self.storage_seq is not None, repr(self)
		id = self.storage_seq-1
		chars = "23456789abcdefghjkmnopqrstuvwxyz"
		midchars = "abcdefghjkmnopq"
		fc = []
		flast = chars[id % len(chars)]
		id = id // len(chars)
		while id:
			c = chars[id % len(midchars)]
			id = id // len(midchars)
			c = chars[id % len(midchars)] + c
			id = id // len(midchars)
			fc.insert(0,c)
		fc.append("_")
		fc.append(self.name+"_"+self.hash[0:10]+flast)
		if self.mime.ext:
			fc[-1] += "."+self.mime.ext
		return fc

	def _get_chars(self):
		if self.storage_seq is None:
			db.flush()
			db.refresh(self,('storage_seq',))
			if self.storage_seq is None: ## sqlite, probably
				from sqlalchemy import func
				self.storage_seq = (db.query(func.max(BinData.storage_seq)).scalar() or 0) +1
				db.flush()
		assert self.storage_seq, repr(self)
		id = self.storage_seq-1
		chars = "abcdefghjk" ## 100 files per end directory (long names)
		midchars = "abcdefghjkmnopqr" ## 256 subdirectories (short names)
		fc = []
		flast = chars[id % len(chars)]
		id = id // len(chars)
		flast += chars[id % len(chars)]
		id = id // len(chars)
		while id:
			id -= 1
			c = midchars[id % len(midchars)]
			id = id // len(midchars)
			c = midchars[id % len(midchars)] + c
			id = id // len(midchars)
			fc.insert(0,c)
		fc.append("_")
		fc.append(self.name+"_"+self.hash[0:10]+flast)
		if self.mime.ext:
			fc[-1] += "."+self.mime.ext
		return fc

	def _move_old_1(self):
		op = self.old_path_1
		np = self.path
		if op != np:
			try:
				os.rename(op,np)
			except OSError:
				logger.warn(u"Could not rename ‘{}’ to ‘{}’".format(op,np))

	def _move_old_2(self):
		op = self.old_path_2
		np = self.path
		if op != np:
			try:
				os.rename(op,np)
			except OSError:
				logger.warn(u"Could not rename ‘{}’ to ‘{}’".format(op,np))

	@property
	def path(self):
		fn = self.superparent.path
		fc = self._get_chars()
		dir = os.path.join(fn,*fc[:-1])
		if not os.path.isdir(dir):
			os.makedirs(dir)
		fn = os.path.join(dir,fc[-1])
		return fn

	@property
	def old_path_1(self):
		fn = self.superparent.path
		fc = self._old1_get_chars()
		return os.path.join(fn,*fc)

	@property
	def old_path_2(self):
		fn = self.superparent.path
		fc = self._old2_get_chars()
		return os.path.join(fn,*fc)

	def get_absolute_url(self):
		fc = self._get_chars()
		fn = self.superparent.url + "/".join(fc)
		return fn
	
	def delete(self):
		p = self.path
		if os.path.exists(p):
			os.remove(p)
		super(BinData,self).delete()

#	def __storm_pre_flush__(self):
#		super(BinData,self).__storm_pre_flush__()
#		if self._content is None:
#			raise RuntimeError("Need to set content before saving")
#		self._save_content()

	def _save_content(self):
		p = self.path
		if os.path.exists(p):
			raise RuntimeError("File exists",p)
		try:
			open(p,"w").write(self.content)
		except BaseException:
			if os.path.exists(p):
				os.remove(p)
			raise


## StaticFile

class StaticFile(ObjectRef):
	"""\
		Record that a static file belongs to a specific site.
		Superparent: The site.
		Parent: The file.
		"""
	__tablename__ = "staticfile"
	_descr = D.StaticFile
	_no_crumbs = True
	@classmethod
	def __declare_last__(cls):
		if not hasattr(cls,'bindata'):
			cls.bindata = cls.parent
		check_unique(cls, "superparent path")

	path = Column(Unicode(1000), nullable=False)
	modified = Column(DateTime,default=datetime.utcnow)

	def __init__(self, path, bin, **kw):
		super(StaticFile,self).__init__(**kw)
		self.path = path
		self.superparent = request.site
		self.parent = bin
		
	@property
	def as_str(self):
		if self._rec_str or not self.superparent or not self.parent: return "‽"
		try:
			self._rec_str += 1
			return u'%s in %s' % (self.path, self.superparent.as_str)
		finally:
			self._rec_str -= 1

	@property
	def hash(self):
		return self.bindata.hash
	@property
	def content(self):
		return self.bindata.content
	@property
	def mimetype(self):
		return self.bindata.mimetype

event.listen(StaticFile, 'before_insert', update_modified)

## The mysql driver ignores autoincrement on non-primary-key columns.
## Workaround:
from sqlalchemy import event
from sqlalchemy.schema import DDL
event.listen(BinData.__table__, 'after_create',
	    DDL("ALTER TABLE bindata CHANGE storage_seq storage_seq INT AUTO_INCREMENT NOT NULL", on="mysql"))

