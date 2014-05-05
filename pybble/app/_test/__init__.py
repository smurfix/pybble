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

class App(BaseApp):
	PARAMS = (
	        ("appiti","pappiti", "Test for passing a parameter into a site"),
		)

	def setup(self):
		@self.route('/one')
		def get_one():
			return "This is Number One"

		@self.route('/two')
		def get_two():
			return render_template('_test/two.haml')

		@self.route('/three')
		def get_three():
			return render_template('_test/three.html')

	pass

