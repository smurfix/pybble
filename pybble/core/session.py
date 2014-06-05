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
		try:
			user = User.q.get_by(id=user_id)
		except NoData:
			pass
		else:
			if user.this_login is None or user.this_login < datetime.now() - current_app.config.PERMANENT_SESSION_LIFETIME:
				## Last login was too long ago.
				user = None
	if user is None:
		user = current_site.anon_user
		session['uid'] = user.id

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

def logged_in(user):
	if session.get('uid',0) == user.id:
		return
	session['uid'] = user.id
	request.user = user

	now = datetime.utcnow()
	if user.cur_login is None or user.cur_login < now-timedelta(0,600):
		user.last_login = user.this_login or now
		user.this_login = user.cur_login = now

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
		self.instances = {}
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
				app.pybble_dispatcher = self
				# Note that this assumes that a site's app cannot change
				# TODO: this is not actually enforced anywhere

			if app.config.DEBUG is True:
				app = DebuggedApplication(app, evalex=True)
			return app

	def __call__(self, environ, start_response):
		"""Standard WSGI"""
		app = self.get_application(environ['HTTP_HOST'], testing=environ.get('testing', None))
		with app.app_context():
			try:
				res = app(environ, start_response)
				if isinstance(res,ContentData):
					res = res(environ, start_response)
				return res
	
			except Exception as e:
				if not app or app.config.DEBUG is not False:
					raise
	
				x=sys.exc_info()
				try:
					print("ERROR:",str(e))
				except Exception:
					print("ERROR: ‹error message could not be printed›")
				import pdb
				pdb.post_mortem(x[2])

