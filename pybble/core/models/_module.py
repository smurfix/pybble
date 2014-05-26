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


from sqlalchemy import Unicode

from ..db import Column
from .object import Object,ObjectRef
from .config import ConfigData
from ._utils import Loadable

from flask._compat import text_type, string_types
from werkzeug.utils import cached_property, import_string

class Module(Loadable,Object):
	"""An abstract table which implements some sort of Pybble module"""
	__abstract__ = True
	name = Column(Unicode(30), unique=True, nullable=False, doc="Human-readable short name")
	doc = Column(Unicode(1000), nullable=True, doc="docstring")

	#config = ObjectRef(ConfigData, declared_attr=True)

	def setup(self, name,doc=None,**kw):
		self.name = name
		if doc is not None:
			self.doc = doc

		self.config = ConfigData.new(self.__class__.__name__+" "+name)

		super(Module,self).setup(**kw)

