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

import re
import sys
import unittest
from functools import wraps
import logging

from flask import Flask,current_app
from flask.ext.script._compat import StringIO, text_type
from flask.ext.script import Command, Option, prompt, prompt_bool
from werkzeug.utils import cached_property

from .script import capture
from .base import TC
from pybble.manager.main import RootManager

from pytest import raises

logger = logging.getLogger('test.manager')

class ManagerFlask(Flask):
	testing = True
	def init_manager(self,manager):
		@manager.command
		def hello(foo=12,*what,**kw):
			print("Oh hello",foo)

class ManagerTC(TC):
	app_class = ManagerFlask

	def manager(self, app=None):
		return RootManager(app)

	def run_manager(self, *args, **kwargs):
		logger.debug("MGR: "+" ".join(args))
		if len(args) == 1:
			sys.argv = args[0].split(" ")
		else:
			sys.argv = args
		exit_code = None
		try:
			exit_code = self.manager(kwargs.get('app',None)).run()
		except SystemExit as e:
			exit_code = e.code 
		self.assertEqual(exit_code, kwargs.get('exit_code',0), " ".join(args))

def run(*args):
	mgr = RootManager()
	if len(args) == 1:
		args = args[0].split(" ")
	mgr.handle(args[0],args[1:])

