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

from sqlalchemy import Integer, Unicode, DateTime, Boolean
from sqlalchemy.orm import relationship,backref

from ..db import Base, Column, check_unique

from flask import request,current_app

from pybble.core import config
import os

from . import ObjectRef
from ._descr import D

## Storage

class Storage(ObjectRef):
	"""A box for binary data files"""
	_descr = D.Storage
	_no_crumbs = True

	name = Column(Unicode(30), unique=True, nullable=False)
	path = Column(Unicode(1000), unique=True, nullable=False)
	url = Column(Unicode(200), unique=True, nullable=False)
	default = Column(Boolean, default=False, nullable=False)
	@classmethod
	def __declare_last__(cls):
		check_unique(cls,"superparent default")

	def setup(self, name,path,url, site=None):
		self.name = unicode(name)
		self.path = unicode(path)
		self.url = unicode(url)

		try: os.makedirs(path)
		except OSError: pass

		super(Storage,self).setup()

	@property
	def as_str(self):
		return u"%s at %s" % (self.name,unicode(self.path))

