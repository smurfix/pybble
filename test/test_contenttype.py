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
import pytest
import datetime
import flask

from .manager import ManagerTC
from .base import WebTC
#from pybble.core.models import Site
#from pybble.core.models.doc import ContentType,Content
from webunit.webunittest import WebTestCase

pytestmark = pytest.mark.skipif(True, reason="We don't actually have contenttypes yet, if ever")

class ContentTestCase(ManagerTC,WebTC,WebTestCase):
	def setupData(self):
		super(AppRunTestCase,self).setupData()
		self.run_manager("mgr -Dt new ContentTest _test test")
		self.run_manager("mgr -Dt -s test blueprint add Homepage _page /")

		self.run_manager("mgr -Dt contenttype add PageContent page 'Your basic text page'")
		self.run_manager("mgr -Dt content add TextContent unfug 'Dies ist Unfug'")
		self.run_manager("mgr -Dt content set unfug text u'Dies ist kompletter Unfug'")

	def test_one(self):
		g.site.homepage = None
		g.site.save()
		self.assertContent("http://test/blue/red","Red Color")
			
	def test_two(self):
		self.assertContent("http://test/blue/green","Green Color")

	def test_three(self):
		self.assertContent("http://test/blue/blue","Blue Color")

	def test_four(self):
		self.assertContent("http://test/blue/yellow","Yellow Color")
