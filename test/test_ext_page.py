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

import unittest
import datetime
import flask

from .manager import ManagerTC
from .base import WebTC
from pybble.core.db import NoData
from pybble.core.models.site import Site
from webunit.webunittest import WebTestCase

class AppRunTestCase(ManagerTC,WebTC,WebTestCase):
	def setupData(self):
		super(AppRunTestCase,self).setupData()
		try:
			Site.q.get_by(domain="ptest")
		except NoData:
			self.run_manager("mgr -Dt core add pybble.ext.page")
			self.run_manager("mgr -Dt site add PageTest _test ptest")

			self.run_manager("mgr -Dt -s ptest blueprint add PageDisplay / BlueTest")
			self.run_manager("mgr -Dt -s ptest obj add Page name=TestPage mime==M:text/plain content=Test_for_Testing order=1")

	def test_page(self):
		from pybble.ext.page.model import Page
		p = Page.q.get_by(name='TestPage')
		self.assertContent("http://ptest/"+p.oid,"Test_for_Testing")
			