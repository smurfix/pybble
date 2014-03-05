# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, division
##
## This is part of Pybble, a WMS (Whatever Management System) based on
## Jinja2/Haml, Werkzeug, Flask, and Optimism.
##
## Pybble is Copyright © 2014 by Matthias Urlichs <matthias@urlichs.de>,
## it is licensed under the GPLv3. See the file `README.md` for details
## as well as hopeful statements by the author.
##
## This paragraph is auto-generated and may self-destruct at any time.
## Please do not remove the next line, or insert any blank lines before it.
##BP

# This is the site's root app.
# It contains the default templates and basic user+site administration.

from flask import render_template
from .. import BaseApp

class App(BaseApp):
	def init_routing(self):
		@self.route('/one')
		def get_one():
			return "This is Number One"

		@self.route('/two')
		def get_two():
			return render_template('two.haml')

		@self.route('/three')
		def get_three():
			return render_template('three.html')

	pass

