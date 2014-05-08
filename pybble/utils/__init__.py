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

from flask import request
from urlparse import urlparse
from random import sample, randrange
from jinja2 import Environment, BaseLoader, Markup
from werkzeug import Local, LocalManager, cached_property, import_string
from werkzeug.exceptions import Unauthorized
from time import time
from pybble.core import config
from markdown import Markdown
import sys
from unicodedata import normalize

class NotGiven:
	"""
	A keyword value which indicates that there is no value passed.
	Distinct from None because somwtimes it is known that there is no
	value.

	TODO: Also used when setting up variables et al. (causing them to be deleted).
	"""
	pass

# copied from Quokka
def slugify(text, encoding=None,
            permitted_chars='abcdefghijklmnopqrstuvwxyz0123456789-'):
    if isinstance(text, str):
        text = text.decode(encoding or 'ascii')
    text = text.strip().replace(' ', '-').lower()
    text = normalize('NFKD', text).encode('ascii', 'ignore')
    text = ''.join(x if x in permitted_chars else '' for x in text)
    while '--' in text:
        text = text.replace('--', '-')
    return text

ALLOWED_SCHEMES = frozenset(['http', 'https', 'ftp', 'ftps'])
URL_CHARS = 'abcdefghijkmpqrstuvwxyzABCDEFGHIJKLMNPQRST23456789'

local = Local()
local_manager = LocalManager([local])

application = local('application')

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

def make_permanent():
	"""Make this session a permanent one."""
	request.session['_perm'] = True

def close_with_browser():
	"""Close the session with the end of the browser session."""
	request.session.pop('_perm', None)

def test_session_cookie():
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

def all_addons():
	if not config.addons:
		return
	for n in config.addons:
		m = import_string("pybble.ext."+n)
		if hasattr(m,"__ALL__"):
			yield m
		else:
			print("While trying to load %s: no export list ('__ALL__')" % (n,), file=sys.stderr)

def hash_data(content):
	"""
	Create an URL-compatible ASCII hash from this content
	"""
	from base64 import b64encode
	try:
		from hashlib import sha1
	except ImportError:
		from sha import sha as sha1
	return b64encode(sha1(content).digest(),altchars=str("-_")).rstrip("=")

def getsubattr(data,key):
	"""
	Split `key` by dots, access data.key.parts by attribute or index as
	appropriate
	"""
	for k in key.split('.'):
		if isinstance(data,(list,tuple)):
			data = data[int(k)]
		elif isinstance(data,dict):
			data = data[k]
		else:
			data = getattr(data,k)
	return data
