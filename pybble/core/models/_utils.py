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

from ..db import Column, no_update

from werkzeug.utils import cached_property, import_string

class Loadable(object):
	"""A mix-in which translates a path into the object it references"""
	path = Column(Unicode(100), nullable=True, doc="Python object name")
	_module = None

	def setup(self, path, **kw):
		self.path = path
		assert self.mod is not None, path
		super(Loadable,self).setup(**kw)

	@classmethod
	def __declare_last__(cls):
		no_update(cls.path)
		super(Loadable,cls).__declare_last__()

	@cached_property
	def mod(self):
		"""Load the module"""
		return import_string(self.path)

	def __call__(self,*a,**k):
		"""Call the referenced code"""
		return self.mod(*a,**k)

