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

import re
import sys
import unittest
from functools import wraps

from flask import Flask
from flask.ext.script._compat import StringIO, text_type
from flask.ext.script import Command, Option, prompt, prompt_bool
from .script import Catcher,capture,run
from .base import TC
from pybble.manager.main import RootManager

from pytest import raises

class ManagerFlask(Flask):
	TESTING = True
	def init_manager(self,manager):
		@manager.command
		def hello(foo=12,*what,**kw):
			print("Oh hello",foo)
	pass

class TestManager(TC):
	def setUp(self):
		super(TestManager,self).setUp()
		self.app = ManagerFlask(__name__)
		self.manager = RootManager(self.app)

	@capture
	def test_simple_command_decorator(self, capsys):
		code = run('manage.py app hello --foo=fubar', self.manager.run)
		out, err = capsys.readouterr()
		assert 'Oh hello' in out

