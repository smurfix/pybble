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

class Exposer(object):
	"""\
		This object records routes so that an app or blueprint can
		register them to itself.

		Basic Usage:
			## pybble/blueprint/foo/__init__.py:
			from .. import BaseApp
			from ...core.route import Exposer
			expose = Exposer()

			class App(BaseApp):
				def setup(self):
					expose.add_to(self)

			@expose("/path/<id>") # see Flask.route for details
			def pather(id):
				return Flask.render_template("not_here.html", id=id)

		Multi-module setup:

			## pybble/blueprint/foo/_base.py:
			from ...core.route import Exposer
			from .. import BaseApp
			expose = Exposer()

			class App(BaseApp):
				def setup(self):
					expose.add_to(self)

			## pybble/blueprint/foo/__init__.py:

			from ._base import expose,App
			from . import part, … # everything that needs to register

			## pybble/blueprint/foo/part.py:
			from ._base import expose

			@expose("/path/<id>") # see Flask.route for details
			def pather(id):
				return Flask.render_template("not_here.html", id=id)

		"""

	def __init__(self):
		self.app = None
		self.rules = []

	def add_to(self, app):
		"""\
			Add my rules to the app or blueprint.
			"""
		self.app = app
		for a,k in self.rules:
			app.add_url_rule(*a,**k)

	def add_url_rule(self, *a,**k):
		"""\
			Works like Flask.add_url_rule, but registers locally for
			addition to an app or blueprint.
		"""
		self.rules.append((a,k))
		if self.app is not None:
			self.app.add_url_rule(*a,**k)

	def __call__(self, rule, **options):
		"""\
			Works like Flask.route, but registers locally for later
			addition to an app or blueprint.
		"""
		def decorator(f):
			endpoint = options.pop('endpoint', None)
			self.add_url_rule(rule, endpoint, f, **options)
			return f
		return decorator

