#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

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

