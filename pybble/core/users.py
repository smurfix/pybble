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

import os
import sys
import logging
from time import time

from flask import Flask, request, render_template, g, session, Markup, Response, current_app
from flask.config import Config
from flask.templating import DispatchingJinjaLoader
from flask.ext.script import Server
from flask._compat import text_type

from hamlish_jinja import HamlishExtension
from jinja2 import Template,BaseLoader, TemplateNotFound

from werkzeug import import_string

from .. import FROM_SCRIPT,ROOT_SITE_NAME,ROOT_USER_NAME
from ..core.db import db, NoData, ManyDataExc
from ..core.models.template import Template as DBTemplate
from ..core.models.site import Site,App
from ..core.models.config import ConfigVar
from ..core.models.user import User
from ..manager import Manager,Command
from ..blueprint import load_app_blueprints
from ..render import load_app_renderer

logger = logging.getLogger('pybble.core.users')

###################################################
# User management

def create_user(site,name,pw=None):
	try:
		user = User.q.get_by(username=name)
	except NoData:
		pass
	else:
		return ManyDataExc("The user ‘{}’ already exists (site ‘{}’).".format(name,user.site.name))

	user = User(username=name,password=pw)
	db.flush()
	return user

def drop_user(name):
	if isinstance(name,string_types):
		try:
			user = User.q.get_by(name=name)
		except NoData:
			user = User.q.get_by(email=name)
	else:
		assert isinstance(user,User)
		user=name
	Delete(user)

