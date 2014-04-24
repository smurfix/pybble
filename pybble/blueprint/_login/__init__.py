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

_doc="""
This module attaches to Flask.login.
"""

from pybble.blueprint import BaseBlueprint
from flask import render_template, abort
from jinja2 import TemplateNotFound

class Blueprint(BaseBlueprint):
	def setup(self):
		super(Blueprint,self).setup()

		@self.route('/red')
		def test_red():
			return "This is Red Color"

		@self.route('/green')
		def test_green():
			return render_template('green.haml')

		@self.route('/blue')
		def test_blue():
			return render_template('blue.html')

		@self.route('/yellow')
		def test_yellow():
			return "This is %s Color"%(self.params['color'],)
