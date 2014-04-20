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

from datetime import datetime,timedelta

from sqlalchemy import Integer, Unicode, DateTime
from sqlalchemy.orm import relationship,backref

from pybble.compat import py2_unicode

from ..db import Base, Column

from pybble.utils import current_request

from pybble.core import config
import os

from . import ObjectRef
from ._descr import D

@py2_unicode
class Storage(ObjectRef):
	"""A box for binary data files"""
	_descr = D.Storage
	_no_crumbs = True

	name = Column(Unicode(30), nullable=False)
	path = Column(Unicode(1000), nullable=False)
	url = Column(Unicode(200), nullable=False)

	def __init__(self, name,path,url):
		super(Storage,self).__init__()
		self.name = unicode(name)
		self.path = unicode(path)
		self.url = unicode(url)
		self.superparent = current_request.site
		try: os.makedirs(path)
		except OSError: pass

	def __str__(self):
		return u"‹%s %s: %s %s›" % (self.__class__.__name__, self.id,self.name,unicode(self.path))
	__repr__ = __str__

