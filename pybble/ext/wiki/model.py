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

from pybble.core.models import ObjectRef
from pybble.core.models._descr import D

class WikiPage(ObjectRef):
	"""\
		A wiki (or similar) page.
		Parent: The "main" wikipage we're a parent of, or whatever parent there is
		Superparent: Our site (main page) or empty (subpage)
		Owner: Whoever created the page

		Wiki pages are not (yet?) nested.
		"""
	_descr = D.WikiPage

	name = Column(Unicode, nullable=False)
	data = Column(Unicode)
	mainpage = Column(Boolean, default=True, nullable=False) # main-linked page?
	modified = Column(DateTime, default=datetime.utcnow)

	def __init__(self, name, data):
		super(WikiPage,self).__init__()
		self.name = name
		self.data = data
	
	def url_html_view(self):
		if self.mainpage:
			return url_for("root.wikipage.viewer", name=self.name)
		if isinstance(self.parent,WikiPage) and self.parent.mainpage:
			return url_for("root.wikipage.viewer", name=self.name, parent=self.parent.name)

