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

from .base import TC
from pybble.core.models import Site,ConfigVar,SiteConfigVar
from pybble.app import create_app

class AppConfigTestCase(TC):

	def setup_sites(self):
		self.clear_db()

		self.assertEqual(Site.objects.count(), 0)
		site = Site(name='root', domain='test.example.com')
		site.save()
		site2 = Site(name='foo', domain='foo.example.com', parent=site)
		site2.save()
		site3 = Site(name='bar', domain='bar.example.com', parent=site)
		site3.save()
		site21 = Site(name='foofoo', domain='foo.foo.example.com', parent=site2)
		site21.save()

		ConfigVar.exists("test1","Test One",-1)
		ConfigVar.exists("test2","Test Two",-2)

		app = create_app(site="root", test=True)
		app1 = create_app(site="foo", test=True)
		app2 = create_app(site="bar", test=True)
		app11 = create_app(site="foofoo", test=True)

		self.assertEqual(app11.config["test1"],-1)
		self.assertEqual(app11.config["test2"],-2)

		return (app,app1,app2,app11)

	def test_config(self):
		with self.app.test_request_context():
			(app,app1,app2,app11) = self.setup_sites()

			app.config["test1"] = 0
			self.assertEqual(app.config["test1"],0)
			self.assertEqual(app1.config["test1"],0)
			self.assertEqual(app11.config["test1"],0)
			self.assertEqual(app2.config["test1"],0)

			app1.config["test2"] = 2
			self.assertEqual(app.config["test2"],-2)
			self.assertEqual(app1.config["test2"],2)
			self.assertEqual(app11.config["test2"],2)
			self.assertEqual(app2.config["test2"],-2)

			app.config["test2"] = 3
			self.assertEqual(app.config["test2"],3)
			self.assertEqual(app1.config["test2"],2)
			self.assertEqual(app11.config["test2"],2)
			self.assertEqual(app2.config["test2"],3)

