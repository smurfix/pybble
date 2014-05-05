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

from pybble.manager.main import RootManager
from pybble.core.models.site import Site
from .base import WebTC
from webunit.webunittest import WebTestCase
from .manager import run

def ap_test():
    # set a class attribute on the invoking test context
	run("mgr -t site add AppTest _test atest")

class AppRunTestCase(WebTC,WebTestCase):
#	def setupData(self):
#		super(AppRunTestCase,self).setupData()
#		self.run_manager("mgr -t site new AppTest _test atest")

	def test_one(self):
		self.once(ap_test)
		assert Site.q.get_by(name="AppTest").domain == "atest"
		self.assertContent("http://atest/one","Number One")
			
	def test_two(self):
		self.once(ap_test)
		self.assertContent("http://atest/two","Number Two")

	def test_three(self):
		self.once(ap_test)
		self.assertContent("http://atest/three","Number Three")

