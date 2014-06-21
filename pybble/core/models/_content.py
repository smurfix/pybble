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

from sqlalchemy import PickleType
from sqlalchemy import event
from sqlalchemy.orm import relationship

from .. import config
from ..db import db
from . import LEN_CONTENT
from .object import ObjectRef
from .types import MIMEtype

## Template

from jinja2 import __version__ as jinja_version

_version = 1
_version = '|'.join(str(x) for x in ('j2',jinja_version,_version,sys.version_info[0],sys.version_info[1]))
_not_cached = "not compiled"

class _Content(object):
	"""\
		This is a Content version without "mime", assuming that this reference
		is defined elsewhere.
		"""
	content = db.Column(db.Unicode(LEN_CONTENT), nullable=False)

	def setup(self,content=None,**k):
		if content is not None:
			self.content = content
		super(_Content,self).setup(**k)

class Content(_Content):
	"""\
		This is a small ad-hoc mix-in which provides a MIME-tagged content column.

		It intentionally provides no methods.
		"""
	mime = ObjectRef(MIMEtype, doc="Content type of my data")

	def setup(self,mime=None,**k):
		if mime is not None:
			self.mime = mime
		super(Content,self).setup(**k)

class ContentObj(object):
	def __init__(self, mime,content):
		self.mime = mime
		self.content = content

	def __composite_values__(self):
		return self.mime, self.content

class Cached(object):
	"""\
		This is a mix-in to provide a statically-cached version of some content.

		You provide: a "this_version" property, which returns a check value to determine if the cache still works

		Usage:

			foo = self.cache
			if foo is None:
				self.cache = foo = somehow_mangle(self)

		Note that this module does not check whether the est of your model
		has been modified. You need to do that yourself, e.g. in a "set"
		handler which invalidates the cache (`del self.cache`) when any of
		your content changes.
		"""
	_cache = db.Column("cache",PickleType(pickler=marshal), nullable=False, default="")
	_version = db.Column("version",db.Unicode(30), nullable=False, default="")
	form_hidden = ('_cache','_version')

	def get_cache(self,version):
		if self._version != version:
			self._version = ""
			self._cache = ""
			return None
		return self._cache
	def set_cache(self,data,version):
		self._cache = data
		self._version = version
	def del_cache(self):
		self._cache = ""
		self._version = ""

