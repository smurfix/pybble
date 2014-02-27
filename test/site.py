#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

import unittest
import datetime
import flask

from flask.ext.mongoengine import MongoEngine
from mongoengine.errors import NotUniqueError,DoesNotExist
from .base import TC
from pybble.core.models import Site,ConfigVar,User

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


	def test_config(self):
		with self.app.test_request_context():
			Site.objects.delete()
			self.assertEqual(Site.objects.count(), 0)
			site = Site(name='root', domain='test.example.com')
			site.save()

			ConfigVar.objects.delete()
			self.assertEqual(ConfigVar.objects.count(), 0)
			ConfigVar.exists("TEST","testing 123",123)
			ConfigVar.exists("TEST2","testing 234","234")
			self.assertEqual(ConfigVar.objects.count(), 2)
			self.assertRaises(NotUniqueError,ConfigVar.exists,"TEST","testing 123",123)
			self.assertEqual(ConfigVar.objects.count(), 2)

			cf = ConfigVar.get("TEST")
			self.assertEquals(cf.default,123)
			self.assertEquals(cf.default,123)

			self.assertEquals(site.config,{"TEST":123,"TEST2":"234"})

			site.config["TEST"] = [12,34]
			self.assertEquals(site.config,{"TEST":[12,34],"TEST2":"234"})

	def test_user(self):
		with self.app.test_request_context():
			User.objects.delete()
			Site.objects.delete()
			self.assertEqual(Site.objects.count(), 0)
			site = Site(name='root', domain='test.example.com')
			site.save()
			site1 = Site(name='foo', domain='foo.test.example.com', parent=site)
			site1.save()
			site2 = Site(name='bar', domain='bar.test.example.com', parent=site)
			site2.save()
			site21 = Site(name='barf', domain='barf.test.example.com', parent=site2)
			site21.save()

			self.assertEqual(User.objects.count(), 0)
			u1 = User(name="U1",email="u1@example.com",password="U1_PW", site=site)
			u2 = User(name="U2",email="u2@example.com",password="U2_PW", site=site1)
			u3 = User(name="U3",email="u3@example.com",password="U3_PW", site=site2)
			u1.save(); u2.save(); u3.save();
			self.assertNotEquals(u1,u2)
			self.assertNotEquals(u2,u3)
			self.assertNotEquals(u1,u3)

			self.assertEquals(u1,User.find("U1",site))
			self.assertEquals(u2,User.find("U2",site1))
			self.assertEquals(u3,User.find("U3",site2))
			self.assertEquals(u3,User.find("U3",site21))

			self.assertEquals(u1,User.find("U1",site1))
			self.assertEquals(u1,User.find("U1",site2))
			self.assertEquals(u1,User.find("U1",site21))

			self.assertRaises(DoesNotExist, User.find,"U2",site)
			self.assertRaises(DoesNotExist, User.find,"U3",site)

			self.assertRaises(DoesNotExist, User.find,"U2",site2)
			self.assertRaises(DoesNotExist, User.find,"U3",site1)
			self.assertRaises(DoesNotExist, User.find,"U2",site21)


