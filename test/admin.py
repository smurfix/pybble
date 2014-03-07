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
from pybble.core.db import db
from .manager import ManagerTC
from .base import WebTC
from webunit.webunittest import WebTestCase

class TheData(db.Document):
	foo = db.StringField(unique=True, required=True)
	bar = db.IntField(default=123)


class AdminTestCase(ManagerTC,WebTC,WebTestCase):
	def cleanData(self):
		TheData.objects.delete()
		super(AdminTestCase,self).cleanData()

	def setupData(self):
		super(AdminTestCase,self).setupData()
		self.run_manager("mgr -t new test _test test")
		self.run_manager("mgr -t -s test blueprint add AdminTest _admin /doc")
		self.run_manager("mgr -t -s test blueprint param AdminTest model test.admin.TheData")

		d = TheData(foo="Test Me")
		d.save()

	def test_index_present(self):
		with self.app.test_request_context():
			self.assertContent("http://test/doc/","Test Me")
