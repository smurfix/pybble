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

import os
from importlib import import_module

from flask import render_template, abort
from jinja2 import TemplateNotFound

from pybble.blueprint import BaseBlueprint
from pybble.core.route import Exposer
expose = Exposer()

_doc="""\
This is the standard blueprint for your site root,
used for global administration and visualization.

It is auto-added to your site root when populated.

TODO: replace this with a “real” site root.

"""
class Blueprint(BaseBlueprint):
	def setup(self):
		super(Blueprint,self).setup()
		expose.add_to(self)

@expose('/')
def test_root():
	return """This is the colorful root, having <a href="red">red</a>, <a href="yellow">yellow</a>, <a href="green">green</a>, and <a href="blue">blue</a>."""

@expose('/red')
def test_red():
	return "This is Red Color"

@expose('/green')
def test_green():
	return render_template('green.haml')

@expose('/blue')
def test_blue():
	return render_template('blue.html')

@self.route('/yellow')
def test_yellow():
	return "This is %s Color"%(self.params['color'],)

#class TheView(AdminBaseView):
#	@expose('/')
#	def index(self):
#		self._template_args['model'] = self.base.model
#		return self.render(['admin/index.haml','admin/index.html'])
#
#class FakeAdmin(object):
#	def __init__(self,bp):
#		self.url = bp.url_prefix
#	def menu(self):
#		return ()
#	def menu_links(self):
#		return ()
#	subdomain = None
#	static_url_path = "/static"
#	url = None
#	base_template="admin/base.html"
#
#class Blueprint(BaseBlueprint):
#	__doc__=_doc
#	def setup(self):
#		super(Blueprint,self).setup()
#		try:
#			base,model = self.params['model'].rsplit('.',1)
#		except KeyError:
#			pass
#		else:
#			self.model = getattr(import_module(base),model)
#
#		try:
#			base,view = self.params['view'].rsplit('.',1)
#		except KeyError:
#			view = TheView
#		else:
#			view = getattr(import_module(base), view)
#
#		self.view = view(self.name+"_view", endpoint=self.name, url=self.url_prefix)
#		self.view.base = self
#		view_bp = self.view.create_blueprint(FakeAdmin(self))
#		view_bp.name = self.name+"_view"
#		self.app.register_blueprint(view_bp)
#
#		static_folder=os.path.join(os.path.dirname(os.path.abspath(os.path.dirname(__name__))),'static')
#		def send_file(filename):
#			return send_from_directory(static_folder, filename)
#		self.app.add_url_rule(self.url_prefix + '/static/<path:filename>', endpoint='admin.static', view_func=send_file)
#
