#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, division, unicode_literals
##
## This is part of Pybble, a WMS (Whatever Management System) based on
## Jinja2/Haml, Werkzeug, Flask, and Optimism.
##
## Pybble is Copyright © 2009-2014 by Matthias Urlichs <matthias@urlichs.de>,
## it is licensed under the GPLv3. See the file `README.md` for details
## as well as hopeful statements by the author.
##
## This paragraph is auto-generated and may self-destruct at any time.
## Please do not remove the next line, or insert any blank lines before it.
##BP

import unittest
import datetime
import flask

from .manager import ManagerTC
from .base import WebTC
from webunit.webunittest import WebTestCase

class AppRunTestCase(ManagerTC,WebTC,WebTestCase):
	def setupData(self):
		super(AppRunTestCase,self).setupData()
		self.run_manager("mgr -t new AppTest _test test")

	def test_one(self):
		with self.app.test_request_context():
			self.assertContent("http://test/one","Number One")
			
	def test_two(self):
		with self.app.test_request_context():
			self.assertContent("http://test/two","Number Two")

	def test_three(self):
		with self.app.test_request_context():
			self.assertContent("http://test/three","Number Three")

