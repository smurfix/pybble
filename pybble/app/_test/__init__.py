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

# This is the site's root app.
# It contains the default templates and basic user+site administration.

from flask import render_template
from .. import BaseApp
from pybble.core.route import Exposer
expose = Exposer()

class App(BaseApp):
	"""Test app. Not suitable for production use."""
	VAR = (
	        ("appiti","pappiti", "Test for passing a parameter into a site"),
		)

	def setup(self):
		super(App,self).setup()
		expose.add_to(self)

@expose('/')
def get_root():
	return "This is a test app. Do not use."

@expose('/one')
def get_one():
	return "This is Number One"

@expose('/two')
def get_two():
	return render_template('_test/two.haml')

@expose('/three')
def get_three():
	return render_template('_test/three.html')

