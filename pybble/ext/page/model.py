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

from flask import url_for

from sqlalchemy import Column,Unicode,Boolean,DateTime

from pybble.core.models.object import Object
from pybble.core.models._content import Content

from datetime import datetime

class Page(Content, Object):
	"""\
		A page (or whatever) of content.
		Parent: The "main" wikipage we're a parent of, or whatever parent there is
		Superparent: Our site (main page) or empty (subpage)
		Owner: Whoever created the page
		"""
	name = Column(Unicode, nullable=False)
	modified = Column(DateTime, default=datetime.utcnow)
	order = Column(Integer, nullable=True, doc="Include on parent page? if so, in what order?")

	@classmethod
	def new(cls, name, content, order=None):
		self = cls(True)

		self.name=name
		self.order=order

		content.to(self)
		self._add()
