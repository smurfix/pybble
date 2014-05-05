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
import pytest

from pybble.core.db import db,NoData
from .manager import ManagerTC
from .base import WebTC
from webunit.webunittest import WebTestCase

#class TheData(db.Document):
#	foo = db.StringField(unique=True, required=True)
#	bar = db.IntField(default=123)

class VarsTestCase(ManagerTC,WebTC,WebTestCase):
	def setupData(self):
		from pybble.core.models.site import Site

		super(VarsTestCase,self).setupData()
		try:
			s = Site.q.get_by(name=u"test")
		except NoData:
			self.run_manager("mgr -t site add test _test test")
			self.run_manager("mgr -t -s test blueprint add _test /doc VarsTest")

#		d = TheData(foo="Test Me Hard")
#		d.save()

## not yet
#	def test_index_present(self):
#		self.assertContent("http://test/doc/","Test Me Hard")
#		## TODO do a lookup involving the parameter
	
	def test_site_vars(self):
		from pybble.core.models.site import Site, SiteBlueprint
		s = Site.q.get_by(name=u"test")

		res = s.config.appiti
		assert res == "pappiti"
		self.run_manager("mgr -t -s test site param appiti foo")
		res = s.config.appiti
		assert res == "foo"
		self.run_manager("mgr -t -s test site param appiti bar")
		assert s.config.appiti == "bar"
		self.run_manager("mgr -t -s test site param appiti -")
		assert s.config.appiti == "pappiti"
		with pytest.raises(KeyError):
			self.run_manager("mgr -t -s test site param nuppi foo") # does not exist

	def test_blueprint_vars(self):
		from pybble.core.models.site import Site, SiteBlueprint
		s = Site.q.get_by(name=u"test")
		b = SiteBlueprint.q.get_by(name=u"VarsTest",parent=s)
		assert b.path=="/doc"

		assert b.config.color == "yellow"
		self.run_manager("mgr -t -s test blueprint param VarsTest color green")
		assert b.config.color == "green"
		self.run_manager("mgr -t -s test blueprint param VarsTest color foo")
		assert b.config.color == "foo"
		self.run_manager("mgr -t -s test blueprint param VarsTest color -")
		assert b.config.color == "yellow"
		with pytest.raises(KeyError):
			self.run_manager("mgr -t -s test blueprint param VarsTest nuppsi fu") # does not exist

		
