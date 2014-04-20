#!/usr/bin/python
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

import unittest
import datetime
import flask

from .manager import ManagerTC
from .base import WebTC
from pybble.core.models import Site
from pybble.core.models.doc import ContentType,Content
from webunit.webunittest import WebTestCase

class ContentTestCase(ManagerTC,WebTC,WebTestCase):
	def setupData(self):
		super(AppRunTestCase,self).setupData()
		self.run_manager("mgr -t new ContentTest _test test")
		self.run_manager("mgr -t -s test blueprint add Homepage _page /")

		self.run_manager("mgr -t contenttype add PageContent page 'Your basic text page'")
		self.run_manager("mgr -t content add TextContent unfug 'Dies ist Unfug'")
		self.run_manager("mgr -t content set unfug text u'Dies ist kompletter Unfug'")

	def clear_db(self):
		Site.objects.update(homepage=None)
		Content.objects.delete()
		ContentType.objects.delete()
		super(ContentTestCase,self).clear_db()

	def test_one(self):
		with self.app.test_request_context():
			g.site.homepage = None
			g.site.save()
			self.assertContent("http://test/blue/red","Red Color")
			
	def test_two(self):
		with self.app.test_request_context():
			self.assertContent("http://test/blue/green","Green Color")

	def test_three(self):
		with self.app.test_request_context():
			self.assertContent("http://test/blue/blue","Blue Color")

	def test_four(self):
		with self.app.test_request_context():
			self.assertContent("http://test/blue/yellow","Yellow Color")
