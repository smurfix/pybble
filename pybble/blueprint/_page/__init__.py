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

## Basic homepage.

from pybble.blueprint import BaseBlueprint
from flask import render_template, abort, g
from jinja2 import TemplateNotFound
from pybble.core.route import Exposer
expose = Exposer()

_doc="""
This blueprint is the mains erver for content, as stored in Pybble's MongoDB.
"""

class Blueprint(BaseBlueprint):
	def setup(self):
		super(Blueprint,self).setup()
		expose.add_to(self)

@expose('/')
def homepage():
	page = g.site.homepage
	if page is None:
		return render_template('empty.haml')
	return page.render_as("page")
