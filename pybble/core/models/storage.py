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

from datetime import datetime,timedelta

from sqlalchemy import Integer, Unicode, DateTime, Boolean, Column
from sqlalchemy.orm import relationship,backref

from ...globals import current_site
from ..db import check_unique
from .object import Object,ObjectRef
from .site import Site

from flask import request,current_app

from pybble.core import config
import os

## Storage

class Storage(Object):
	"""A box for binary data files"""

	site = ObjectRef(Site)
	name = Column(Unicode(30), nullable=False)
	path = Column(Unicode(500), nullable=False)
	url = Column(Unicode(200), nullable=False)
	default = Column(Boolean, default=False, nullable=False)

	@classmethod
	def __declare_last__(cls):
		check_unique(cls, "name site")
		check_unique(cls, "default site")
		check_unique(cls, "path")
		super(Storage,cls).__declare_last__()

	@property
	def parent(self):
		return self.site

	def setup(self, name,path,url, site=None, **kw):
		self.name = unicode(name)
		self.path = unicode(path)
		self.url = unicode(url)
		if site is None:
			site = current_site
		self.site = site

		try: os.makedirs(path)
		except OSError: pass

		super(Storage,self).setup(**kw)

	@property
	def as_str(self):
		return u"%s at %s" % (self.name,unicode(self.path))

