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

from flask import Flask, current_app,request
from flask._compat import string_types,text_type
from werkzeug import cookie_date, get_host
from werkzeug.contrib.securecookie import SecureCookie

from .. import ROOT_SITE_NAME
from .models.user import User
from .models.site import Site
from .db import db, NoData, refresh
from .signal import all_apps,app_list

class Session(SecureCookie):
	@property
	def session_key(self):
		if 'uid' in self:
			self.pop('_sk', None)
			return self['uid']
		elif not '_sk' in self:
			self['_sk'] = md5('%s%s%s' % (random(), time(),
							current_app.config.SECRET_KEY)).digest() \
							.encode('base64').strip('\n =')
		return self['_sk']
	
	def serialize(cls,*a,**k):
		if hasattr(cls,"new"):
			del cls.new
		return super(Session,cls).serialize(*a,**k)
	
def add_session():
	data = request.cookies.get(current_app.config.SESSION_COOKIE_NAME, "")
	session = None
	expired = False
	if data:
		session = Session.unserialize(data, current_app.config.SECRET_KEY)
		if session.get('_ex', 0) < time():
			session = None
			expired = True
		else:
			session.new = False

	if session is None:
		session = Session(secret_key=current_app.config.SECRET_KEY)
		session['_ex'] = time() + current_app.config.SESSION_COOKIE_AGE
		session.new = True
	else:
		request.session_data = data
	request.session = session
	if expired and request.session.get('uid'):
		from pybble.flashing import flash
		flash(u'Deine Sitzung ist abgelaufen.  Du musst dich neu '
				u'anmelden.', session=session)

#from inyoka.utils.flashing import flash
#from inyoka.utils.html import escape

def add_user():
	user_id = request.session.get('uid')
	user = None
	if user_id is not None:
		try: user = User.q.get_by(id=user_id)
		except NoData: pass
	if user is None:
		user = request.site.anon_user
		request.session['uid'] = user.id

#	# check for bann
#	if user.is_banned:
#		flash((u'Du wurdest ausgeloggt, da der Benutzer „%s“ '
#				u'gerade gebannt wurde' % escape(user.username)), False,
#				session=request.session)
#
#		request.session.pop('uid', None)
#		user = request.site.anon_user

	now = datetime.utcnow()
	if user.cur_login is None or user.cur_login < now-timedelta(0,600):
		user.last_login = user.cur_login or now
	user.cur_login = now
	request.user = user

def save_session(response):
	new = request.session.new
	session_data = request.session.serialize()
	if new or request.session_data != session_data:
		if request.session.get('_perm'):
			expires_time = request.session.get('_ex', 0)
			expires = cookie_date(expires_time)
		else:
			expires = None
		response.set_cookie(current_app.config.SESSION_COOKIE_NAME, session_data, httponly=True, expires=expires)
	return response

def add_response_headers(response):
	s = getattr(request,"session",None)
	if not s:
		return
	if s.should_vary:
		try:
			response.headers.add('Vary','Cookie')
		except AttributeError:
			pass
	return response

def logged_in(user):
	request.session['uid'] = user.id
	request.user = user

class SubdomainDispatcher(object):
	"""
	This code creates individual app instances (one per site) and sends
	requests to the correct one.

	:param root: Only dispatch to sites within this sub-hierarchy
	"""
	def __init__(self, root=ROOT_SITE_NAME):
		if isinstance(root,string_types):
			root = Site.q.get_by(name=text_type(root))
		self.root = root
		self.lock = Lock()
		self.instances = i = {}
		all_apps.connect(self._reload)
		app_list.connect(self._reload)
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
		with self.lock:
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
					app.after_request(save_session)
				app.pybble_dispatcher = self
				# Note that this assumes that a site's app cannot change
				# TODO: this is not actually enforced anywhere

			return app

	def __call__(self, environ, start_response):
		"""Standard WSGI"""
		app = self.get_application(environ['HTTP_HOST'], testing=environ.get('testing', None))

		return app(environ, start_response)

