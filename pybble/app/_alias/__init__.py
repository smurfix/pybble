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

from pybble.app import BaseApp
from pybble.core.db import refresh

class App(BaseApp):
	"""
	This app simply does the same thing as its parent.
	"""
	_parent = None
	def __call__(self, environ, start_response):
		if self._parent is None:
			s = refresh(self.site)
			self._parent = self.pybble_dispatcher.get_application(site=s.parent)
		return self._parent(environ, start_response)

