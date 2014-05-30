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

from sqlalchemy import Integer, Unicode, ForeignKey, DateTime
from sqlalchemy.orm import relationship,backref
from sqlalchemy import event

from ...core import config
from ...globals import current_site
from ...utils import hash_data
from ..db import Base, Column, db, check_unique,no_update
from . import LEN_NAME,LEN_PATH
from .object import Object,ObjectRef, update_modified
from .types import MIMEtype
from .storage import Storage
from .user import User
from .site import Site

import os

logger = logging.getLogger('pybble.core.models.files')

## BinData

class BinData(Object):
	"""
		Stores (a reference to) one data file
		parent: the object this is attached to

		This object implements a content-based file system: the hash of the
		file contents is an index.
		"""
	_no_crumbs = True
	@classmethod
	def __declare_last__(cls):
		no_update(cls.hash)
		super(BinData,cls).__declare_last__()

	storage = ObjectRef(Storage)
	mime = ObjectRef(MIMEtype)

	name = Column(Unicode(LEN_NAME), nullable=False)
	hash = Column(Unicode(33), nullable=True, unique=True) ## NULL if deleted
	timestamp = Column(DateTime,default=datetime.utcnow)
	size = Column(Integer)

	@property
	def parent(self):
		return self.storage

	@staticmethod
	def lookup(content):
		return BinData.q.filter(BinData.hash == hash_data(content), BinData.storage != None).one()
			
	def setup(self,name, ext=None,mimetype=None, content=None, storage=None, **kw):
		super(BinData,self).setup(**kw)
		if not storage: storage = parent.default_storage
		if mimetype:
			self.mime = mimetype
			if ext:
				assert mimetype == MIMEtype.get(ext),"Extension doesn't match MIME type"
		elif ext:
			self.mime = MIMEtype.get(ext)
		else:
			raise RuntimeError("You need to specify MIME type or extension")
		self.name = name
		self._content = content
		self.hash = hash_data(content)
		self.size = len(content)
		self.storage = storage
		db.add(self)
		self._save_content()

	@property
	def as_str(self):
		n = self.name
		if self.ext:
			n += "."+self.ext
		return u"%s %s" % (n,self.mimetype)

	@property
	def content(self):
		## DANGER this can be pretty big; TODO: stream
		if not hasattr(self,"_content"):
			self._content = open(self.path).read()
		return self._content

	@property
	def content_reader(self):
		"""Returns a file handle for reading the data"""
		return open(self.path)

	@property
	def mimetype(self):
		try:
			return str(self.mime)
		except Exception:
			return "???/???"

	@property
	def ext(self):
		try:
			return self.mime.ext
		except Exception:
			return "???"

	def _get_chars(self):
		if self.id is None:
			db.flush((self,))
		id = self.id-1
		chars = "bcdfghjkmn" ## 100 files per end directory (long names)
		midchars = "bcdfghjkmnopqrst" ## 256 subdirectories (short names)
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

	@property
	def path(self):
		fn = self.storage.path
		fc = self._get_chars()
		dir = os.path.join(fn,*fc[:-1])
		if not os.path.isdir(dir):
			os.makedirs(dir)
		fn = os.path.join(dir,fc[-1])
		return fn

	def get_absolute_url(self):
		fc = self._get_chars()
		fn = self.storage.url + "/".join(fc)
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
			with file(p) as f:
				assert self.content == f.read()
		else:
			try:
				open(p,"w").write(self.content)
			except BaseException:
				if os.path.exists(p):
					os.remove(p)
				raise

## StaticFile

class StaticFile(Object):
	"""\
		Record that a static file belongs to a specific site.
		Superparent: The site.
		Parent: The file.
		"""
	__tablename__ = "staticfile"
	_no_crumbs = True
	@classmethod
	def __declare_last__(cls):
		check_unique(cls, "site path")
		super(StaticFile,cls).__declare_last__()

	file = ObjectRef(BinData)
	parent = ObjectRef(doc="wherever this has been uploaded into")
	site = ObjectRef(Site)

	path = Column(Unicode(LEN_PATH), nullable=False)
	modified = Column(DateTime,default=datetime.utcnow)

	def setup(self, path, bin, parent=None, site=None, **kw):
		self.path = path
		if site is None:
			site = current_site
		self.site = site
		self.parent = parent or site
		self.file = bin

		super(StaticFile,self).setup(**kw)
		
	@property
	def as_str(self):
		if self._rec_str or not self.site or not self.parent: return "‽"
		try:
			self._rec_str += 1
			return u'%s in %s' % (self.path, self.site.as_str)
		finally:
			self._rec_str -= 1

	@property
	def hash(self):
		return self.file.hash
	@property
	def content(self):
		return self.file.content
	@property
	def mimetype(self):
		return self.file.mimetype

