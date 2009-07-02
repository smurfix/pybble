# -*- coding: utf-8 -*-

try:
	from hashlib import md5
except ImportError:
	from md5 import md5
from time import time
from random import random
from werkzeug import cookie_date, get_host
from werkzeug.contrib.securecookie import SecureCookie
from pybble import _settings as settings
from datetime import datetime,timedelta
from pybble.models import User,Site,DummySite
from pybble.database import NoResult
from pybble.decorators import ResultNotFound
from pybble.database import db
import sys

class Session(SecureCookie):
	@property
	def session_key(self):
		if 'uid' in self:
			self.pop('_sk', None)
			return self['uid']
		elif not '_sk' in self:
			self['_sk'] = md5('%s%s%s' % (random(), time(),
							settings.SECRET_KEY)).digest() \
							.encode('base64').strip('\n =')
		return self['_sk']
	
	def serialize(cls,*a,**k):
		if hasattr(cls,"new"):
			del cls.new
		return super(Session,cls).serialize(*a,**k)
	
try:
	from settings import ONESITE
except ImportError:
	ONESITE=False

@ResultNotFound
def add_site(request):
	host = get_host(request.environ)
	site = None
	if host.startswith("www."):
		request.environ['HTTP_X_FORWARDED_HOST'] = host[4:]
		return HttpResponsePermanentRedirect(request.url)
	
	try:
		if ONESITE:
			site = db.store.find(Site).one()
			if site is None:
				raise NoResult
		else:
			site = db.get_by(Site, domain=(host.decode("idna")))
	except NoResult:
		print >>sys.stderr,"host '%s' ... not found!" % (host,)
		site = DummySite(domain=host,name=u'Unknown domain «%s»' % (host,))
	finally:
		request.site = site

def add_session(request):
	data = request.cookies.get(settings.SESSION_COOKIE_NAME, "")
	session = None
	expired = False
	if data:
		session = Session.unserialize(data, settings.SECRET_KEY)
		if session.get('_ex', 0) < time():
			session = None
			expired = True
		else:
			session.new = False

	if session is None:
		session = Session(secret_key=settings.SECRET_KEY)
		session['_ex'] = time() + settings.SESSION_COOKIE_AGE
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

def add_user(request):
	user_id = request.session.get('uid')
	user = None
	if user_id is not None:
		try: user = db.get_by(User, id=user_id)
		except NoResult: pass
	if user is None:
		user = request.site.anon_user

#	# check for bann
#	if user.is_banned:
#		flash((u'Du wurdest ausgeloggt, da der Benutzer „%s“ '
#				u'gerade gebannt wurde' % escape(user.username)), False,
#				session=request.session)
#
#		request.session.pop('uid', None)
#		user = get_anonymous_user()

	now = datetime.utcnow()
	if user.cur_login is None or user.cur_login < now-timedelta(0,600):
		user.last_login = user.cur_login or now
	user.cur_login = now
	request.user = user

def save_session(request, response):
	new = request.session.new
	session_data = request.session.serialize()
	if new or request.session_data != session_data:
		if request.session.get('_perm'):
			expires_time = request.session.get('_ex', 0)
			expires = cookie_date(expires_time)
		else:
			expires = None
		response.set_cookie(settings.SESSION_COOKIE_NAME, session_data, httponly=True, expires=expires)

def add_response_headers(request,response):
	s = getattr(request,"session",None)
	if not s:
		return
	if s.should_vary:
		try:
			response.headers.add('Vary','Cookie')
		except AttributeError:
			pass

def logged_in(request,user):
	request.session['uid'] = user.id
	request.user = user
