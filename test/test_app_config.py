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

import pytest
import datetime
import flask

from .base import TC
from pybble.core.db import db,NoData,ManyData
from pybble.core.models.site import Site,App
from pybble.core.models.config import ConfigVar,SiteConfigVar
from pybble.app import create_app

class AppConfigTestCase(TC):

	def setup_sites(self):
		self.clear_db()

		app = App.q.get_by(name="_test")
		try: site = Site.q.get_by(domain='test.example.com')
		except NoData: site = Site.new(name='root', domain='test.example.com', app=app)
		try: site2 = Site.q.get_by(domain='foo.example.com')
		except NoData: site2 = Site.new(name='foo', domain='foo.example.com', parent=site, app=app)
		try: site3 = Site.q.get_by(domain='bar.example.com')
		except NoData: site3 = Site.new(name='bar', domain='bar.example.com', parent=site, app=app)
		try: site21 = Site.q.get_by(domain='foo.foo.example.com')
		except NoData: site21 = Site.new(name='foofoo', domain='foo.foo.example.com', parent=site2, app=app)
		db.commit()

		with pytest.raises(ManyData):
			site21a = Site.new(name='foofoo', domain='foo2.foo.example.com', parent=site2)
		db.rollback()
		with pytest.raises(ManyData):
			site21a = Site.new(name='foofoo3', domain='foo.foo.example.com', parent=site2)
		db.rollback()

		ConfigVar.exists(site,"test1","Test One",-1)
		ConfigVar.exists(site,"test2","Test Two",-2)

		app = create_app(site="root", testing=True)
		app1 = create_app(site="foo", testing=True)
		app2 = create_app(site="bar", testing=True)
		app11 = create_app(site="foofoo", testing=True)

		self.assertEqual(app11.config["test1"],-1)
		self.assertEqual(app11.config["test2"],-2)

		return (app,app1,app2,app11)

	def test_config(self):
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

