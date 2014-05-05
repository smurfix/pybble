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

_doc="""
This module contains a few dummy URLs for testing.
"""

from pybble.blueprint import BaseBlueprint
from flask import render_template, abort
from jinja2 import TemplateNotFound

class Blueprint(BaseBlueprint):
	PARAMS = (
		("color","yellow", "Test for passing a parameter into a blueprint"),
	)
	def setup(self):
		super(Blueprint,self).setup()

		@self.route('/red')
		def test_red():
			return "This is Red Color"

		@self.route('/green')
		def test_green():
			"""Fetch template by blueprint name"""
			return render_template('_test/green.haml')

		@self.route('/blue')
		def test_blue():
			"""Fetch template by SiteBlueprint name"""
			return render_template('BlueTest/blue.html')

		@self.route('/yellow')
		def test_yellow():
			return "This is %s Color"%(self.params['color'],)
