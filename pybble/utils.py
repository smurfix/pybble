# -*- coding: utf-8 -*-

from os import path
from urlparse import urlparse
from random import sample, randrange
from jinja2 import Environment, BaseLoader, Markup
from werkzeug import Local, LocalManager, cached_property
from time import time
import settings
from markdown import Markdown

TEMPLATE_PATH = path.join(path.dirname(__file__), 'templates')
# used for initial import only

STATIC_PATH = path.join(path.dirname(__file__), 'static')
ALLOWED_SCHEMES = frozenset(['http', 'https', 'ftp', 'ftps'])
URL_CHARS = 'abcdefghijkmpqrstuvwxyzABCDEFGHIJKLMNPQRST23456789'

local = Local()
local_manager = LocalManager([local])
application = local('application')
current_request = local('request')


def validate_url(url):
	return urlparse(url)[0] in ALLOWED_SCHEMES

def get_random_uid():
	return ''.join(sample(URL_CHARS, randrange(3, 9)))

rand=None
baselen=None
strlen=None
def random_string(bytes=9, base="23456789abcdefghijkmnpqrstuvwxyz", dash="-",
				dash_step=0):
	"""Get a random string, suitable for passwords"""
	global rand
	if rand is None:
		rand = open("/dev/urandom")

	global baselen;
	global strlen;
	if strlen is None or baselen != bytes:
		from math import log,ceil
		baselen=bytes;
		strlen=int(ceil(ceil(log(len(base))/log(2))*baselen/8))
		
	passwd=rand.read(strlen)

	fm=0
	for c in passwd:
		fm = (fm<<8) + ord(c)
	passwd = ""
	while bytes:
		passwd += base[fm%len(base)]
		fm = fm // len(base)
		bytes -= 1
		if dash_step and bytes and fm and not (len(passwd)+1)%(dash_step+1):
			passwd += dash
	return passwd


import smtplib
import email.Message

def send_mail(to='', template='', **context):
	if "site" not in context:
		context["site"] = current_request.site
	if "user" not in context:
		context["user"] = current_request.user
	rand = random_string(8)
	for x in range(3):
		context["id"+str(x)] = "%d.%s%d@%s" % (time(),random_string(10),x,current_request.site.domain)
	
	mailServer = smtplib.SMTP(settings.MAILHOST)
	mailServer.sendmail(context["site"].owner.email, to, jinja_env.get_template(template).render(**context))
	mailServer.quit()


def make_permanent(request):
	"""Make this session a permanent one."""
	request.session['_perm'] = True

def close_with_browser(request):
	"""Close the session with the end of the browser session."""
	request.session.pop('_perm', None)

def test_session_cookie(request):
	"""
	Test if the session cookie works.  This is used in login and register
	to inform the user about an inproperly configured browser.  If the
	cookie doesn't work a link is returned to retry the configuration.
	"""
	if request.session.new:
		arguments = request.GET.copy()
		if '_cookie_set' not in request.GET:
			arguments['_cookie_set'] = 'yes'
			this_url = 'http://%s%s%s' % (
				request.get_host(),
				request.path,
				arguments and '?' + arguments.urlencode() or ''
			)
			raise DirectResponse(HttpResponseRedirect(this_url))
		arguments.pop('_cookie_set', None)
		retry_link = 'http://%s%s%s' % (
			request.get_host(),
			request.path,
			arguments and '?' + arguments.urlencode() or ''
		)
	else:
		retry_link = None
	return retry_link

