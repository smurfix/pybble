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
from flask import render_template, abort, request
from pybble.render import render_template as pybble_render_template
from jinja2 import TemplateNotFound
from pybble.core.route import Exposer
expose = Exposer()

class Blueprint(BaseBlueprint):
	PARAMS = (
		("color","yellow", "Test for passing a parameter into a blueprint"),
	)
	def setup(self):
		super(Blueprint,self).setup()
		expose.add_to(self)

@expose('/red')
def test_red():
	return "This is Red Color"

@expose('/yellow')
def test_yellow():
	return "This is %s Color"%(request.bp.config['color'],)

@expose('/green')
def test_green():
	"""Fetch template by blueprint name"""
	return render_template('_test/green.haml')

@expose('/blue')
def test_blue():
	"""Fetch template by SiteBlueprint name"""
	return render_template('BlueTest/blue.html')

@expose('/p/red')
def test_p_red():
	return "This is Red Color"

@expose('/p/yellow')
def test_p_yellow():
	return "This is %s Color"%(request.bp.config['color'],)

@expose('/p/green')
def test_p_green():
	"""Fetch template by blueprint name"""
	return pybble_render_template('_test/green.haml')

@expose('/p/blue')
def test_p_blue():
	"""Fetch template by SiteBlueprint name"""
	return pybble_render_template('BlueTest/blue.html')

