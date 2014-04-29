#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, division, unicode_literals
##
## This is part of Pybble, a WMS (Whatever Management System) based on
## Jinja2/Haml, Werkzeug, Flask, and Optimism.
##
## Pybble is Copyright © 2009-2014 by Matthias Urlichs <matthias@urlichs.de>,
## it is licensed under the GPLv3. See the file `README.md` for details
## as well as hopeful statements by the author.
##
## This paragraph is auto-generated and may self-destruct at any time.
## Please do not remove the next line, or insert any blank lines before it.
##BP

import unittest
import datetime
import flask

from .base import TC
from pybble.core.models.site import Site,Blueprint
from pybble.core.models.config import ConfigVar,SiteConfigVar
#from pybble.core.db import NoData

class SiteTestCase(TC):

	def test_create_root(self):
		self.assertEqual(Site.q.count(), 0)
		site = Site(name='root', domain='test.example.com')
		site.save()
		self.assertEqual(Site.q.count(), 1)

	def test_create_multi(self):
		self.assertEqual(Site.q.count(), 0)
		site = Site(name='root', domain='test.example.com')
		site.save()
		site1 = Site(name='foo', domain='foo.example.com', parent=site)
		site1.save()
		site2 = Site(name='bar', domain='bar.example.com', parent=site)
		site2.save()
		site11 = Site(name='foofoo', domain='foo.foo.example.com', parent=site1)
		site11.save()
		site111 = Site(name='foofoofoo', domain='foo.foo.foo.example.com', parent=site11)
		site111.save()
		self.assertEqual(Site.q.count(), 5)
		self.assertEqual(site.children.count(), 2)
		self.assertEqual(len([x for x in site.children_tree]), 5)
		self.assertEqual(len([x for x in site1.children_tree]), 3)

		self.assertIsNone(site.parent)
		self.assertEqual(site.name,site1.parent.name)
		self.assertEqual(site.name,site2.parent.name)
		self.assertEqual(site1.name,site11.parent.name)

		c = set(s.name for s in site.children)
		self.assertNotIn("root",c)
		self.assertIn("foo",c)
		self.assertNotIn("foofoo",c)
		self.assertNotIn("foofoofoo",c)
		self.assertIn("bar",c)

		c = set(s.name for s in site.children_tree)
		self.assertIn("root",c)
		self.assertIn("foo",c)
		self.assertIn("foofoo",c)
		self.assertIn("foofoofoo",c)
		self.assertIn("bar",c)

		c = set(s.name for s in site1.children)
		self.assertNotIn("root",c)
		self.assertNotIn("foo",c)
		self.assertIn("foofoo",c)
		self.assertNotIn("foofoofoo",c)
		self.assertNotIn("bar",c)

		c = set(s.name for s in site1.children_tree)
		self.assertNotIn("root",c)
		self.assertIn("foo",c)
		self.assertIn("foofoo",c)
		self.assertIn("foofoofoo",c)
		self.assertNotIn("bar",c)

	def test_config(self):
		self.assertEqual(Site.q.count(), 0)
		site = Site(name='root', domain='test.example.com')
		site.save()
		site1 = Site(name='foo', domain='foo.example.com', parent=site)
		site1.save()

		self.assertEqual(ConfigVar.q.count(), 0)
		ConfigVar.exists("TEST","testing 123",123)
		ConfigVar.exists("TEST2","testing 234","234",True)
		self.assertEqual(ConfigVar.q.count(), 2)
		self.assertRaises(NotUniqueError,ConfigVar.exists,"TEST","testing 123",123)
		self.assertEqual(ConfigVar.q.count(), 2)

		cf = ConfigVar.get("TEST")
		cf2 = ConfigVar.get("TEST2")
		self.assertEquals(cf.default,123)
		self.assertEquals(cf2.default,u"234")
		self.assertEquals(site.config,{"TEST":123,"TEST2":[u"234"]})
		self.assertEquals(site1.config,{"TEST":123,"TEST2":[u"234"]})

		site.config["TEST"] = [12,34]
		self.assertEquals(site.config,{"TEST":[12,34],"TEST2":[u"234"]})
		self.assertEquals(site1.config,{"TEST":[12,34],"TEST2":[u"234"]})
		site1.config["TEST2"] = 987
		self.assertEquals(site1.config,{"TEST":[12,34],"TEST2":[987,u"234"]})
		del site1.config["TEST2"]
		self.assertEquals(site1.config,{"TEST":[12,34],"TEST2":[u"234"]})
		del site1.config["TEST2"]
		self.assertEquals(site1.config,{"TEST":[12,34],"TEST2":[u"234"]})
		# TODO: Cached site configs need invalidation
		# (we don't have a cache yet)

#	def test_user(self):
#		self.assertEqual(Site.q.count(), 0)
#		site = Site(name='root', domain='test.example.com')
#		site.save()
#		site1 = Site(name='foo', domain='foo.test.example.com', parent=site)
#		site1.save()
#		site2 = Site(name='bar', domain='bar.test.example.com', parent=site)
#		site2.save()
#		site21 = Site(name='barf', domain='barf.test.example.com', parent=site2)
#		site21.save()
#
#		self.assertEqual(User.q.count(), 0)
#		u1 = User.add(username="U1",email="u1@example.com",password="U1_PW", site=site)
#		u2 = User.add(username="U2",email="u2@example.com",password="U2_PW", site=site1)
#		u3 = User.add(username="U3",email="u3@example.com",password="U3_PW", site=site2)
#		self.assertNotEquals(u1,u2)
#		self.assertNotEquals(u2,u3)
#		self.assertNotEquals(u1,u3)
#
#		self.assertEquals(u1,User.find("U1",site))
#		self.assertEquals(u2,User.find("U2",site1))
#		self.assertEquals(u3,User.find("U3",site2))
#		self.assertEquals(u3,User.find("U3",site21))
#
#		self.assertEquals(u1,User.find("U1",site1))
#		self.assertEquals(u1,User.find("U1",site2))
#		self.assertEquals(u1,User.find("U1",site21))
#
#		self.assertRaises(NoData, User.find,"U2",site)
#		self.assertRaises(NoData, User.find,"U3",site)
#
#		self.assertRaises(NoData, User.find,"U2",site2)
#		self.assertRaises(NoData, User.find,"U3",site1)
#		self.assertRaises(NoData, User.find,"U2",site21)
#
#		self.assertRaises(NotUniqueError, User.add,"U1",site2)
#		self.assertRaises(NotUniqueError, User.add,"U1",site21)
#		self.assertRaises(NotUniqueError, User.add,"U3",site21)
#		# The test suite intentionally does not check whether
#		# a user may be added multiple times at different sites,
#		# e.g. whether User.add("U2",site21) succeeds
#
