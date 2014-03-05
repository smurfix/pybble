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

from pybble.app import WrapperApp

class App(WrapperApp):
	"""
	This app simply does the same thing as its parent.
	"""
	def __call__(self, environ, start_response):
		return self.pybble_dispatcher.get_application(site=self.site.parent)(environ, start_response)

