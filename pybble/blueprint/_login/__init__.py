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

##
## This module attaches to Flask.login.
## 

from .. import BaseBlueprint
from flask import abort
from jinja2 import TemplateNotFound

from pybble.render import render_template
from pybble.core.route import Exposer
expose = Exposer()

class Blueprint(BaseBlueprint):
	"""Login. Not yet actually used, let alone tested."""
	def setup(self):
		super(BaseBlueprint,self).setup()
		expose.add_to(self)

@expose('/red')
def test_red():
	return "This is Red Color"

@expose('/green')
def test_green():
	return render_template('green.haml')

@expose('/blue')
def test_blue():
	return render_template('blue.html')

@expose('/yellow')
def test_yellow():
	return "This is %s Color"%(self.params['color'],)
