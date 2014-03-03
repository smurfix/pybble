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

import sys,os
sys.path.insert(0,os.pardir)

import unittest
import datetime
import flask

from flask.ext.mongoengine import MongoEngine
from pybble.core.db import db

class TC(unittest.TestCase):
	MONGODB_DB = 'pybble_test'
	TESTING = True

	def setUp(self):
		app = flask.Flask(__name__)
		app.config.from_object(self)

		class Todo(db.Document):
			title = db.StringField(max_length=60)
			text = db.StringField()
			done = db.BooleanField(default=False)
			pub_date = db.DateTimeField(default=datetime.datetime.now)

		db.init_app(app)

		Todo.drop_collection()
		self.Todo = Todo

		self.app = app
		self.db = db

#	def test_request_context(self):
#		with self.app.test_request_context():
#			todo = self.Todo(title='Test', text='test')
#			todo.save()
#			self.assertEqual(self.Todo.objects.count(), 1)

