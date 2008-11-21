# -*- coding: utf-8 -*-

try:
	from hashlib import md5
except ImportError:
	from md5 import md5
from time import time
from random import random
from werkzeug import cookie_date, get_host
from werkzeug.contrib.securecookie import SecureCookie
import settings
from pybble.models import User,Site
from pybble.decorators import ResultNotFound

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

@ResultNotFound
def add_site(request):
	host = get_host(request.environ)
	if host.startswith("www."):
		url = 'http://%s%s' % (host[4:], request.get_full_path())
		return HttpResponsePermanentRedirect(url)
	print "SITE",host
	try:
		site = Site.q.get_by(domain=host)
	except ResultNotFound:
		print "... not found!"
		raise
	request.site = site

def add_session(request):
	data = request.cookies.get(settings.SESSION_COOKIE_NAME)
	session = None
	expired = False
	if data:
		session = Session.unserialize(data, settings.SECRET_KEY)
		if session.get('_ex', 0) < time():
			session = None
			expired = True
	if session is None:
		session = Session(secret_key=settings.SECRET_KEY)
		session['_ex'] = time() + settings.SESSION_COOKIE_AGE
	request.session = session
	if expired:
		from inyoka.utils.flashing import flash
		flash(u'Deine Sitzung ist abgelaufen.  Du musst dich neu '
				u'anmelden.', session=session)

#from inyoka.utils.flashing import flash
#from inyoka.utils.html import escape

def add_user(request):
	user_id = request.session.get('uid')
	user = None
	if user_id is not None:
		user = User.q.get_by(id=user_id)
	if user is None:
		user = User.q.get_anonymous_user(request.site)

#	# check for bann
#	if user.is_banned:
#		flash((u'Du wurdest ausgeloggt, da der Benutzer „%s“ '
#				u'gerade gebannt wurde' % escape(user.username)), False,
#				session=request.session)
#
#		request.session.pop('uid', None)
#		user = User.objects.get_anonymous_user()

	request.user = user

