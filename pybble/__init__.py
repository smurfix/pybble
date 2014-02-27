#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

VERSION = (0, 1, 0)

__version__ = ".".join(map(str, VERSION))
__status__ = "Alpha"
__description__ = "Smurf's Magic All-In-One CMS"
__author__ = "Matthias Urlichs"
__email__ = "matthias@urlichs.de"
__license__ = "None. All rightes reserved. For now."
__copyright__ = "Copyright © 2014, Matthias Urlichs"

import os
from pybble.core.admin import create_admin
#from quokka.core.app import QuokkaApp
	# from .core.middleware import HTTPMethodOverrideMiddleware

try:
	admin = create_admin()
except:
	# Fix setup install:
	# If new environment not return error
	pass


import logging

from flask import Flask, request, render_template, render_template_string, g, session, Markup, Response
from time import time
import os

from hamlish_jinja import HamlishExtension
from jinja2 import Template

from quokka.core.app import QuokkaApp

###################################################
# web server setup

class HamlQuokka(QuokkaApp):
	def create_jinja_environment(self):
		"""Add support for .haml templates."""
		rv = super(HamlQuokka,self).create_jinja_environment()
 
		rv.extensions["jinja2.ext.HamlishExtension"] = HamlishExtension(rv)
		rv.hamlish_file_extensions=('.haml',)
		rv.hamlish_mode='debug'
		rv.hamlish_enable_div_shortcut=True

		rv.filters['datetime'] = datetimeformat
		return rv

	def select_jinja_autoescape(self, filename):
		"""Returns `True` if autoescaping should be active for the given template name.
		"""
		if filename is None:
			return False
		if filename.endswith('.haml'):
			return True
		return super(HamlQuokka,self).select_jinja_autoescape(filename)


def datetimeformat(value, format='%d-%m-%Y %H:%M %Z%z'):
	if isinstance(value,(int,float)):
		value = datetime.utcfromtimestamp(value)
	return value.astimezone(TZ).strftime(format)


class CustomProxyFix(object):
	def __init__(self, app):
		self.app = app
	def __call__(self, environ, start_response):
		host = environ.get('HTTP_X_FORWARDED_HOST', '')
		if host:
			environ['HTTP_HOST'] = host
		return self.app(environ, start_response)


#def setup_app(main=None):
#	app.config.from_object(config)
#	websockets = Sockets(app)
#
#	from zuko.web import ui,admin,user,monitor
#	from zuko.db import register as db_register
#	from zuko.web import register as web_register
#	db_register(app)
#	web_register(app)
#	ui.register(app)
#	admin.register(app)
#	user.register(app)
#	if main is not None:
#		monitor.register(app,websockets,main)
#
#	from zuko.btest import simple_page
#	app.register_blueprint(simple_page, url_prefix="/one", url_defaults={"special":False})
#	app.register_blueprint(simple_page, url_prefix="/two", url_defaults={"special":True})





def create_app(config=None, test=False, admin_instance=None, **settings):
	app = HamlQuokka('pybble', template_folder=os.path.join(os.getcwd(),'templates'), static_folder=os.path.join(os.getcwd(),'static'))
	app.wsgi_app = CustomProxyFix(app.wsgi_app)

	app.config.from_object(config or 'quokka.settings')
	mode = os.environ.get('MODE', 'local')
	if test:
		mode = 'quokka.test'
	try:
		app.config.from_object('%s_settings' % mode)
	except ImportError:
		pass

	app.config.update(settings)

	if not test:
		app.config.from_envvar("QUOKKA_SETTINGS", silent=True)
	else:
		app.config.from_envvar("QUOKKATEST_SETTINGS", silent=True)

	# testing trick
	# with app.test_request_context():
	from quokka.ext import configure_extensions
	configure_extensions(app, admin_instance or admin)

	# app.wsgi_app = HTTPMethodOverrideMiddleware(app.wsgi_app)
	return app


def create_api(config=None, **settings):
	return None


def create_celery_app(app=None):
	from celery import Celery
	app = app or create_app()
	celery = Celery(__name__, broker=app.config['CELERY_BROKER_URL'])
	celery.conf.update(app.config)
	TaskBase = celery.Task

	class ContextTask(TaskBase):
		abstract = True

		def __call__(self, *args, **kwargs):
			with app.app_context():
				return TaskBase.__call__(self, *args, **kwargs)

	celery.Task = ContextTask
	return celery
