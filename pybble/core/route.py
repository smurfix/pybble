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
			from pybble.app import BaseApp
			#from pybble.blueprint import BaseBlueprint
			from ...core.route import Exposer
			expose = Exposer()

			#class Blueprint(BaseBlueprint):
			class App(BaseApp):
				def setup(self):
					super(App,self).setup()
					expose.add_to(self)

			@expose("/path/<id>") # see Flask.route for details
			def pather(id):
				return Flask.render_template("not_here.html", id=id)

		Multi-module setup:

			## pybble/blueprint/foo/_base.py:
			from pybble.core.route import Exposer
			from pybble.app import BaseApp
			expose = Exposer()

			class App(BaseApp):
				def setup(self):
					super(App,self).setup()
					expose.add_to(self)

			## pybble/blueprint/foo/__init__.py:

			from ._base import expose,App
			from . import part, … # everything that needs to register

			## pybble/blueprint/foo/part.py:
			from ._base import expose

			@expose("/path/<id>") # see Flask.route for details
			def pather(id):
				return Flask.render_template("not_here.html", id=id)

		If you have sub-modules (with a path like <blueprint>.admin.foo):

			## pybble/blueprint/admin.py:
			from ._base import expose
			expose = expose.sub("admin")

			@expose("/admin/foobar")
			def foo():
				…
			
		"""

	def __init__(self, sub_name=None):
		self.app = None
		self.sub_name = sub_name
		self.rules = []
		self.subs = []

	def sub(self, name):
		s = Exposer(name)
		self.subs.append(s)
		return s
		
	def add_to(self, app):
		"""\
			Add my rules to the app or blueprint.
			"""
		self.app = app
		for r,e,v,a,k in self.rules:
			app.add_url_rule(r,endpoint=e,view_func=v, *a,**k)
		for s in self.subs:
			s.add_to(app)

	def add_url_rule(self, rule, view_func, endpoint=None, *a,**k):
		"""\
			Works like Flask.add_url_rule, but registers locally for
			addition to an app or blueprint.
		"""
		if endpoint is None:
			endpoint = view_func.__name__
		if self.sub is not None:
			endpoint = self.sub_name+"."+endpoint

		self.rules.append((rule, endpoint,view_func, a,k))
		if self.app is not None:
			self.app.add_url_rule(rule, endpoint=endpoint, view_func=view_func, *a,**k)

	def __call__(self, rule, **options):
		"""\
			Works like Flask.route, but registers locally for later
			addition to an app or blueprint.
		"""
		def decorator(f):
			self.add_url_rule(rule, f, **options)
			return f
		return decorator

