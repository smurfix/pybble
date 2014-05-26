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
from flask import _app_ctx_stack, request

from .base import TC
from pybble.core.models.site import Site
from pybble.core.models.user import User
from pybble.core.models.config import ConfigVar,SiteConfigVar
from pybble.core.db import ManyData
from pybble.globals import current_site
from pybble.app import create_app
from pybble import ROOT_SITE_NAME,ROOT_USER_NAME

class PermTestCase(TC):

	def setup(self):
		request.user = User.q.get_by(username=ROOT_USER_NAME)
		# request.user = User.q.get_by(username=ROOT_USER_NAME)

	def test_basic(self):
		request.user = User.q.get_by(username=ROOT_USER_NAME)
		app = create_app(testing=True)
		with app.app_context():
			anon = current_site.anon_user
			assert anon.can_read(current_site)
			assert not anon.can_write(current_site)
			assert not anon.can_add(current_site)

			root = Site.q.get_by(parent=None)
			supi = User.q.get_by(username=ROOT_USER_NAME,site=root)
			assert supi.can_read(current_site)
			assert supi.can_write(current_site)
			assert supi.can_add(current_site)

