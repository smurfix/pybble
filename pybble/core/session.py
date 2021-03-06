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

try:
	from hashlib import md5
except ImportError:
	from md5 import md5
import sys
from time import time
from random import random
from datetime import datetime,timedelta
from threading import Lock
import logging

from flask import Flask, current_app,request,session, flash
from flask._compat import string_types,text_type
from werkzeug import cookie_date, get_host
from werkzeug.contrib.securecookie import SecureCookie
from werkzeug.debug import DebuggedApplication

from .. import ROOT_SITE_NAME
from ..render import ContentData
from ..utils import random_string
from .models.user import User
from .models.site import Site
from .db import db, NoData, refresh
from ..globals import current_site
from .signal import all_apps,app_list

logger = logging.getLogger('pybble.core.session')

def add_session():
	if '_ex' not in session:
		assert 'uid' not in session
	expired = False
	if session.get('_ex', 0) < time():
		expired = True
	session['_ex'] = time() + current_app.config.SESSION_COOKIE_AGE
	if expired and session.get('uid'):
		del session['uid']
		flash(u'Deine Sitzung ist abgelaufen.  Du musst dich neu anmelden.')

#from inyoka.utils.flashing import flash
#from inyoka.utils.html import escape

def add_user():
	user_id = session.get('uid')
	user = None
	if user_id is not None:
		# TODO: This is a good place to create a new anon user if the site
		# wants to track its visitors. Make sure there's only one creator!
		# (Use dogpile)
		try:
			user = User.q.get_by(id=user_id)
		except NoData:
			pass
		else:
			if user.this_login is None or user.this_login < datetime.now() - current_app.config.PERMANENT_SESSION_LIFETIME:
				## Last login was too long ago.
				user = None
	if user is None:
		# Anon user. We put an anon_id in the session, instead of creating
		# a user right away, because otherwise each request without cookies
		# would create a new anon user: not a good idea.
		user = current_site.anon_user(None)
		session['uid'] = user.id
		session['anon_id'] = random_string(10)

#	# check for bann
#	if user.is_banned:
#		flash((u'Du wurdest ausgeloggt, da der Benutzer ‘%s’ '
#				u'gerade gebannt wurde' % escape(user.username)), False,
#				session=session)
#
#		session.pop('uid', None)
#		user = current_site.anon_user
#		session['uid'] = user.id

	user.cur_login = datetime.now()
	request.user = user

def unique_anon_user():
	"""Enforce a unique user. Useful e.g. for tracking a shopper."""
	if request.user and request.user.username != ANON_USER_NAME:
		return
	request.user = user = current_site.anon_user(session.get('anon_id') or random_string(10))
	session['uid'] = user.id

def logged_in(user):
	if session.get('uid',0) == user.id:
		return
	session['uid'] = user.id
	request.user = user

	now = datetime.utcnow()
	if user.cur_login is None or user.cur_login < now-timedelta(0,600):
		user.last_login = user.this_login or now
		user.this_login = user.cur_login = now

def logged_out():
	request.user = user = current_site.anon_user(None)
	session['uid'] = user.id

class PdbApplication(object):
	"""Debugs a given application."""

	def __init__(self, app):
		self.app = app

	def pdb_application(self, environ, start_response):
		"""Run the application and conserve the traceback frames."""
		app_iter = None
		try:
			app_iter = self.app(environ, start_response)
			for item in app_iter:
				yield item
			if hasattr(app_iter, 'close'):
				app_iter.close()
		except Exception as e:
			exc_info = sys.exc_info()
			if hasattr(app_iter, 'close'):
				app_iter.close()
			
			try:
				start_response(b'500 INTERNAL SERVER ERROR', [
					('Content-Type', 'text/html; charset=utf-8'),
					# Disable Chrome's XSS protection, the debug
					# output can cause false-positives.
					('X-XSS-Protection', '0'),
				])
			except Exception:
				# if we end up here there has been output but an error
				# occurred.  in that situation we can do nothing fancy any
				# more, better log something into the error log and fall
				# back gracefully.
				environ['wsgi.errors'].write(
					'Debugging middleware caught exception in streamed '
					'response at a point where response headers were already '
					'sent.\n')
			else:
				import pdb;pdb.set_trace()
				yield "ERROR, debugging"

			finally:
				print("POSTMORTEM",file=sys.stderr)
				import pdb
				pdb.post_mortem(exc_info[2])

	def __call__(self, environ, start_response):
		"""Dispatch the requests."""
		# important: don't ever access a function here that reads the incoming
		# form data!  Otherwise the application won't have access to that data
		# any more!
		from werkzeug.wrappers import BaseRequest as Request, BaseResponse as Response
		request = Request(environ)
		response = self.pdb_application
		return response(environ, start_response)

class SubdomainDispatcher(object):
	"""
	This code creates individual app instances (one per site) and sends
	requests to the correct one.

	:param root: Only dispatch to sites within this sub-hierarchy
	"""
	def __init__(self, app):
		with app.app_context():
			root = app.site
			if root is None:
				root = Site.q.get_by(parent=None)
			elif isinstance(root,string_types):
				root = Site.q.get_by(name=text_type(root))
		self.app = app
		self.root = root
		self.lock = Lock()
		self.instances = {}
		all_apps.connect(self._reload)
		app_list.connect(self._reload)
		with app.app_context():
			self._reload(sender=self)

	def _reload(self,sender):
		# This pre-loads the instances with the sites necessary to
		# later instantiate the apps.
		i = self.instances
		seen = set()
		r = refresh(self.root)
		for s in r.all_sites:
			if s.domain not in i:
				i[s.domain] = s
			seen.add(s.domain)
		for s in i.keys():
			if s not in seen:
				del i[s]

	def get_application(self, host=None, site=None, testing=None):
		if site:
			assert host is None
			host = site.domain
		else:
			host = host.split(':')[0]
		with self.lock, self.app.app_context():
			try:
				app = self.instances[host]
			except KeyError:
				logger.warn("Unknown site: {}".format(host))
				return DeadApp(NotFound,'The domain “{}” is unknown here.'.format(host))
			if isinstance(app,Site):
				# first request: create an instance and re-save in
				# `self.instances` for convenience
				from ..app import create_app
				self.instances[host] = app = create_app(site=app, testing=testing)
				if isinstance(app,Flask):
					app.before_request(add_session)
					app.before_request(add_user)
				app.pybble_dispatcher = self
				# Note that this assumes that a site's app cannot change
				# TODO: this is not actually enforced anywhere

			if app.config.DEBUG is True:
				app.wsgi_app = DebuggedApplication(app.wsgi_app, evalex=True, show_hidden_frames=True)
			elif app.config.DEBUG is False:
				app.wsgi_app = PdbApplication(app.wsgi_app)
			return app

	def __call__(self, environ, start_response):
		"""Standard WSGI"""
		app = self.get_application(environ['HTTP_HOST'], testing=environ.get('testing', None))
		res = app(environ, start_response)
		return res

