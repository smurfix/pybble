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

from . import Command,Option

class TestCommand(Command):
	"""Run py.test"""
	capture_all_args = True

	def __init__(self):
		super(TestCommand,self).__init__()
		#self.add_option(Option("-f","--force", dest="force",action="store_true",help="Override all database changes"))

	def __call__(self,app, *args):
		from pytest import main as testmain
		from pybble import cache

		cache.delete("*")
		testmain(*args)
