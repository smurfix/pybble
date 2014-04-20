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
import logging

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

from . import DummyObject,ObjectRef, update_modified
from ._descr import D
from .types import MIMEtype

logger = logging.getLogger('pybble.core.models.files')

@py2_unicode
class BinData(Base):
	"""
		Stores (a reference to) one data file
		owner: whoever uploaded the thing
		parent: the object this is attached to
		superparent: the storage
		"""
	__tablename__ = "bindata"
	__mapper_args__ = {'polymorphic_identity': 22}
	_no_crumbs = True
	
	# Alias for .superparent
	storage = relationship("Object", foreign_keys='(superparent_id,)')

	storage_seq = Column(Integer, primary_key=True, autoincrement=True)
	mime_id = Column(Integer, ForeignKey(MIMEtype.id), nullable=False, index=True)
	mime = relationship(mime_id, primaryjoin=mime_id==MIMEtype.id)
	name = Column(Unicode(30), nullable=False)
	hash = Column(Unicode(33), nullable=False)
	timestamp = Column(DateTime,default=datetime.utcnow)
	size = Column(Integer)

	@staticmethod
	def lookup(content):
		res = BinData.q.filter(BinData.hash == hash_data(content), BinData.superparent != None).one()
		if not res:
			raise NoResult
		return res
			
	def __init__(self,name, ext=None,mimetype=None, content=None, parent=None, storage=None):
		super(BinData,self).__init__()
		if not parent: parent = current_request.site
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
		self.owner = current_request.user
		self.parent = parent
		self.superparent = storage
		self._save_content()

	def __str__(self):
		return u"‹%s %s: %s %s›" % (self.__class__.__name__, self.id,self.name+"."+self.ext,self.mimetype)
	__repr__ = __str__

	@property
	def content(self):
		if not hasattr(self,"_content"):
			try:
				self._content = open(self.path).read()
			except IOError:
				self._content = open(self.old_path).read()
				self._move_old()
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

	def _old_get_chars(self):
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

	def _get_chars(self):
		if self.storage_seq is None:
			db.flush()
			if self.storage_seq is None:
				return "???"
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

	def _move_old(self):
		op = self.old_path
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
	def old_path(self):
		fn = self.superparent.path
		fc = self._old_get_chars()
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
			raise RuntimeError("File exists")
		try:
			open(p,"w").write(self.content)
		except BaseException:
			if os.path.exists(p):
				os.remove(p)
			raise

@py2_unicode
class StaticFile(ObjectRef):
	"""\
		Record that a static file belongs to a specific site.
		Superparent: The site.
		Parent: The file.
		"""
	__tablename__ = "staticfile"
	_descr = D.StaticFile
	_no_crumbs = True

	# alias for .parent
	bindata = relationship("Object", foreign_keys='(parent_id,)')

	path = Column(Unicode(1000), nullable=False)
	modified = Column(DateTime,default=datetime.utcnow)

	def __init__(self, path, bin):
		super(StaticFile,self).__init__()
		self.path = path
		self.superparent = current_request.site
		self.parent = bin
		
	def __str__(self):
		if self._rec_str or not self.superparent or not self.parent: return super(StaticFile,self).__str__()
		try:
			self._rec_str = True
			return u'‹%s %s: %s in %s›' % (self.__class__.__name__, self.id, self.path, unicode(self.superparent))
		finally:
			self._rec_str = False
	__repr__ = __str__

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
