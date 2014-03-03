# -*- coding: utf-8 -*-
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
from pybble.manager import Manager

from pytest import raises

class ManagerFlask(Flask):
	def init_manager(self,manager):
		@manager.command
		def hello(foo=12,*what,**kw):
			print "Oh hello",foo
	pass

class TestManager(TC):
	def setUp(self):
		super(TestManager,self).setUp()
		self.app = ManagerFlask(__name__)
		self.manager = Manager(self.app)

	@capture
	def test_simple_command_decorator(self, capsys):
		code = run('manage.py app hello --foo=fubar', self.manager.run)
		out, err = capsys.readouterr()
		assert 'Oh hello' in out

