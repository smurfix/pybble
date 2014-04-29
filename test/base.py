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

import sys,os
sys.path.insert(0,os.pardir)

from pybble import ROOT_SITE_NAME
import unittest
import datetime
import flask
from wsgi_intercept import WSGI_HTTPConnection,WSGI_HTTPSConnection
from pybble.manager.main import SubdomainDispatcher

main_app = None

class Fake_HTTPConnection(WSGI_HTTPConnection):
	def get_app(self, host, port):
		return main_app,""
class Fake_HTTPSConnection(WSGI_HTTPSConnection):
	def get_app(self, host, port):
		return main_app,""

try:
	from wsgi_intercept import http_client_intercept
except ImportError:
	skip_httpclient = True
else:
	skip_httpclient = False
	http_client_intercept.HTTPInterceptorMixin = Fake_HTTPConnection
	http_client_intercept.HTTPSInterceptorMixin = Fake_HTTPSConnection

try:
	from wsgi_intercept import httplib2_intercept
except ImportError:
	skip_httplib2 = True
else:
	skip_httplib2 = False
	httplib2_intercept.InterceptorMixin = Fake_HTTPConnection

try:
	from wsgi_intercept import requests_intercept
except ImportError:
	skip_requests = True
else:
	skip_requests = False
	requests_intercept.InterceptorMixin = Fake_HTTPConnection

try:
	from wsgi_intercept import urllib_intercept
except ImportError:
	skip_urllib = True
else:
	skip_urllib = False
	urllib_intercept.HTTPInterceptorMixin = Fake_HTTPConnection
	urllib_intercept.HTTPSInterceptorMixin = Fake_HTTPSConnection

from pybble.core.db import db
from pybble.core.models.site import Site,Blueprint
from pybble.core.models.config import ConfigVar,SiteConfigVar

class TC(unittest.TestCase):
	TEST = True
	app_class = flask.Flask
	testsite=None

	def clear_db(self):
		pass

	def setUp(self):
		super(TC,self).setUp()
		app = self.app_class(__name__)
		app.config.from_object(self)

		self.app = app
		self.ctx = app.test_request_context()
		self.ctx.push()
		self.cleanData()
		if self.testsite:
			try:
				s = Site.q.get_by(name=self.testsite)
			except NoData:
				s = Site(name=self.testsite, domain=self.testsite)
				db.flush()
			flask.request.site = s
		else:
			flask.request.site = Site.q.get_by(name=ROOT_SITE_NAME)
		self.setupData()
		self.setupRest()

	def cleanData(self):
		pass
	def setupData(self):
		pass
	def setupRest(self):
		pass
	
	def tearDown(self):
		self.ctx.pop()
		super(TC,self).tearDown()

class WebTC(TC):
	def setupRest(self):
		super(WebTC,self).setupRest()
		global main_app
		main_app = SubdomainDispatcher()

		if not skip_httpclient:
			http_client_intercept.install()
		if not skip_httplib2:
			httplib2_intercept.install()
		if not skip_requests:
			requests_intercept.install()
		if not skip_urllib:
			urllib_intercept.install_opener()

	def tearDown(self):
		if not skip_httpclient:
			http_client_intercept.uninstall()
		if not skip_httplib2:
			httplib2_intercept.uninstall()
		if not skip_requests:
			requests_intercept.uninstall()
		if not skip_urllib:
			urllib_intercept.uninstall_opener()
		
