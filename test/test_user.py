#!/usr/bin/python
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

import pytest
import datetime
import flask

from .manager import ManagerTC, run
from .base import WebTC
from webunit.webunittest import WebTestCase

from pybble.core.db import refresh
from pybble.core.models.user import User

def u_test():
	# set a class attribute on the invoking test context
	run("mgr -Dt site add UserTest _test utest")
	run("mgr -Dt -s utest user add Joe")

class AppRunTestCase(ManagerTC,WebTC,WebTestCase):
	def test_added(self):
		self.once(u_test)
		u = User.q.get_by(username="Joe")
		assert u.site.name == "UserTest"
			
	def test_password(self):
		self.once(u_test)
		u = User.q.get_by(username="Joe")
		assert u.password is None
		self.run_manager("mgr -Dt -s UserTest obj update User {} password=blafasel".format(u.id))
		u = refresh(u)
		assert ":" in u.password # make sure it's hashed
