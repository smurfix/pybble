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

from .base import TC
from pybble.core.models.site import Site,Blueprint
from pybble.core.models.config import ConfigVar,SiteConfigVar
from pybble.core.db import ManyData
from pybble import ROOT_SITE_NAME

class SiteTestCase(TC):

	def test_create_multi(self):
		site = Site(name='sroot', domain='test.site.example.com')
		site1 = Site(name='sfoo', domain='foo.site.example.com', parent=site)
		site2 = Site(name='sbar', domain='bar.site.example.com', parent=site)
		site11 = Site(name='sfoofoo', domain='foo.foo.site.example.com', parent=site1)
		site111 = Site(name='sfoofoofoo', domain='foo.foo.foo.site.example.com', parent=site11)
		self.assertEqual(len(site.children), 2)
		self.assertEqual(len([x for x in site.all_sites]), 5)
		self.assertEqual(len([x for x in site1.all_sites]), 3)

		assert site.parent.name == ROOT_SITE_NAME
		self.assertEqual(site.name,site1.parent.name)
		self.assertEqual(site.name,site2.parent.name)
		self.assertEqual(site1.name,site11.parent.name)

		c = set(s.name for s in site.all_children("Site"))
		self.assertNotIn("root",c)
		self.assertIn("sfoo",c)
		self.assertNotIn("sfoofoo",c)
		self.assertNotIn("sfoofoofoo",c)
		self.assertIn("sbar",c)

		c = set(s.name for s in site.all_sites)
		self.assertIn("sroot",c)
		self.assertIn("sfoo",c)
		self.assertIn("sfoofoo",c)
		self.assertIn("sfoofoofoo",c)
		self.assertIn("sbar",c)

		c = set(s.name for s in site1.all_children("Site"))
		self.assertNotIn("sroot",c)
		self.assertNotIn("sfoo",c)
		self.assertIn("sfoofoo",c)
		self.assertNotIn("sfoofoofoo",c)
		self.assertNotIn("sbar",c)

		c = set(s.name for s in site1.all_sites)
		self.assertNotIn("sroot",c)
		self.assertIn("sfoo",c)
		self.assertIn("sfoofoo",c)
		self.assertIn("sfoofoofoo",c)
		self.assertNotIn("sbar",c)

	def test_config(self):
		site = Site(name='s2root', domain='test.site2.example.com')
		site1 = Site(name='s2foo', domain='foo.site2.example.com', parent=site)

		n = ConfigVar.q.count()
		v1 = ConfigVar.exists(site,"TEST","testing 123",123)
		v2 = ConfigVar.exists(site,"TEST2","testing 234","234")
		self.assertEqual(ConfigVar.q.count(), n+2)
		v1a = ConfigVar.exists(site,"TEST","testing 123",123)
		assert v1 is v1a
		self.assertEqual(ConfigVar.q.count(), n+2)

		cf = ConfigVar.get(site,"TEST")
		cf2 = ConfigVar.get(site,"TEST2")
		self.assertEquals(cf.value,123)
		self.assertEquals(cf2.value,u"234")
		self.assertEquals(site.config.TEST,123)
		self.assertEquals(site.config.TEST2,"234")

		assert SiteConfigVar.q.filter_by(parent=site).count() == 0
		site.config["TEST"] = [12,34]
		assert SiteConfigVar.q.filter_by(parent=site).count() == 1
		assert site.config["TEST"] == [12,34]
		assert site1.config["TEST"] == [12,34]
		site1.config["TEST"] = [56,67]
		assert site.config["TEST"] == [12,34]
		assert site1.config["TEST"] == [56,67]
		del site.config["TEST"]
		assert site.config["TEST"] == 123
		assert site1.config["TEST"] == [56,67]

		site1.config["TEST2"] = 987
		assert site1.config["TEST2"] == 987
		assert site.config["TEST2"] == u"234"
		site.config["TEST2"] = u"345"
		assert site1.config["TEST2"] == 987
		assert site.config["TEST2"] == u"345"
		del site1.config["TEST2"]
		assert site1.config["TEST2"] == u"234"
		assert site.config["TEST2"] == u"345"
		del site.config["TEST2"]
		assert site.config["TEST2"] == u"234"
		assert site1.config.TEST == [56,67]

#	def test_user(self):
#		site = Site(name='root', domain='test.example.com')
#		site1 = Site(name='foo', domain='foo.test.example.com', parent=site)
#		site2 = Site(name='bar', domain='bar.test.example.com', parent=site)
#		site21 = Site(name='barf', domain='barf.test.example.com', parent=site2)
#
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
