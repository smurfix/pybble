# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, division, unicode_literals
##
## This is part of Pybble, a WMS (Whatever Management System) based on
## Jinja2/Haml, Werkzeug, Flask, and Optimism.
##
## Pybble is Copyright © 2009-2014 by Matthias Urlichs <matthias@urlichs.de>,
## it is licensed under the GPLv3. See the file `README.md` for details
## as well as hopeful statements by the author.
##
## This paragraph is auto-generated and may self-destruct at any time.
## Please do not remove the next line, or insert any blank lines before it.
##BP

## Basic homepage.

from pybble.blueprint import BaseBlueprint
from flask import render_template, abort, g
from jinja2 import TemplateNotFound

_doc="""
This blueprint is the mains erver for content, as stored in Pybble's MongoDB.
"""

class Blueprint(BaseBlueprint):
	def setup(self):
		super(Blueprint,self).setup()

		@self.route('/')
		def homepage():
			page = g.site.homepage
			if page is None:
				return render_template('empty.haml')
			return page.render_as("page")
