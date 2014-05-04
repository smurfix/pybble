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

from pybble.core.models.user import User

class AppRunTestCase(ManagerTC,WebTC,WebTestCase):
	def setupData(self):
		super(AppRunTestCase,self).setupData()
		self.run_manager("mgr -t site add UserTest _test utest")
		self.run_manager("mgr -t -s utest user add Joe")

	def test_added(self):
		u = User.q.get_by(name=Joe)
		assert u.site.name == utest
			
	def test_password(self):
		u = User.q.get_by(name=Joe)
		assert u.password is None
		self.run_manager("mgr -t -s obj User {} passwort blafasel")
		assert u.password
		assert u.password != "blafasel"
