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

from sqlalchemy import Unicode,Boolean,DateTime,Integer

from pybble.core.db import db
from pybble.core.models import LEN_NAME
from pybble.core.models.object import Object,ObjectRef
from pybble.core.models._content import Content
from pybble.core.models._const import PERM_READ,PERM_ADMIN
from pybble.globals import current_site

from datetime import datetime

class Page(Content, Object):
	"""\
		A page (or whatever) of content.
		Parent: The "main" wikipage we're a parent of, or whatever parent there is
		Superparent: Our site (main page) or empty (subpage)
		Owner: Whoever created the page
		"""
	NAME="Page"
	DOC="A basic content page"

	_site_perm=PERM_READ
	_site_add_perm=()
	_anon_perm=PERM_READ
	_anon_add_perm=()
	_admin_perm=PERM_ADMIN
	_admin_add_perm=('Site','Page')

	name = db.Column(Unicode(LEN_NAME), nullable=False)
	parent = ObjectRef()

	modified = db.Column(DateTime, default=datetime.utcnow)
	order = db.Column(Integer, nullable=True, doc="Include on parent page? if so, in what order?")

	# the `Content` mix-in provides everything required for rendering

	def setup(self, name,parent=None,order=None, **k):
		self.name=name
		self.parent = parent or current_site
		if order is not None:
			self.order=order

		super(Page,self).setup(**k)
	
