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

from flask.ext.mongoengine import MongoEngine
from mongoengine.errors import NotUniqueError,DoesNotExist
from .manager import ManagerTC
from pybble.core.models import Site,ConfigVar,SiteConfigVar,User,Blueprint
from .base import WebTC
from webunit.webunittest import WebTestCase

class AppRunTestCase(ManagerTC,WebTC,WebTestCase):
	def setUp2(self):
		with self.app.test_request_context():
			Blueprint.objects.delete()
			User.objects.delete()
			SiteConfigVar.objects.delete()
			Site.objects.delete()
			ConfigVar.objects.delete()
			self.run_manager("mgr -t new _test test BlueprintAppTest")
			self.run_manager("mgr -t -s test blueprint add _test /blue BlueprintTestPrint")
		super(AppRunTestCase,self).setUp2()

	def test_one(self):
		with self.app.test_request_context():
			self.assertContent("http://test/blue/red","Red Color")
			
	def test_two(self):
		with self.app.test_request_context():
			self.assertContent("http://test/blue/green","Green Color")

	def test_three(self):
		with self.app.test_request_context():
			self.assertContent("http://test/blue/blue","Blue Color")

