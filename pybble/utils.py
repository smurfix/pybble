# -*- coding: utf-8 -*-

from os import path
from urlparse import urlparse
from random import sample, randrange
from jinja2 import Environment, BaseLoader, Markup
from werkzeug import Local, LocalManager, cached_property, import_string
from werkzeug.exceptions import Unauthorized
from time import time
from pybble import _settings as settings
from markdown import Markdown
import sys

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

class AuthError(Unauthorized):
	def __init__(self,obj,perm):
		super(AuthError,self).__init__()
		self.obj = obj
		self.perm = perm

class AuthError(Unauthorized):
	def __init__(self,obj,perm):
		super(AuthError,self).__init__()
		self.obj = obj
		self.perm = perm


def all_addons():
	for n in settings.ADDONS:
		m = import_string("pybble.addon."+n)
		if hasattr(m,"__ALL__"):
			yield m
		else:
			print >>sys.stderr,"While trying to load %s: no export list ('__ALL__')" % (n,)

