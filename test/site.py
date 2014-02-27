#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

import unittest
import datetime
import flask

from flask.ext.mongoengine import MongoEngine
from .base import TC
from pybble.core.models import Site

class SiteTestCase(TC):

	def setUp(self):
		super(SiteTestCase,self).setUp()

	def test_create_root(self):
		with self.app.test_request_context():
			Site.objects.delete()
			self.assertEqual(Site.objects.count(), 0)
			site = Site(name='root', domain='test.example.com')
			site.save()
			self.assertEqual(Site.objects.count(), 1)

	def test_create_multi(self):
		with self.app.test_request_context():
			Site.objects.delete()
			self.assertEqual(Site.objects.count(), 0)
			site = Site(name='root', domain='test.example.com')
			site.save()
			site2 = Site(name='foo', domain='foo.example.com', parent=site)
			site2.save()
			site3 = Site(name='bar', domain='bar.example.com', parent=site)
			site3.save()
			site21 = Site(name='foofoo', domain='foo.foo.example.com', parent=site2)
			site21.save()
			self.assertEqual(Site.objects.count(), 4)
			self.assertEqual(site.children.count(), 2)
			self.assertEqual(len([x for x in site.children_tree]), 4)
			self.assertEqual(len([x for x in site2.children_tree]), 2)


