# -*- coding: utf-8 -*-

from os import path
from urlparse import urlparse
from random import sample, randrange
from jinja2 import Environment, BaseLoader, Markup
from werkzeug import Response, Local, LocalManager, cached_property
from werkzeug.routing import Map, Rule
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

url_map = Map([Rule('/static/<file>', endpoint='static', build_only=True)])


class TemplateNotFound(IOError, LookupError):
	"""
	A template was not found by the template loader.
	"""

	def __init__(self, name):
		IOError.__init__(self, name)
		self.name = name

class DatabaseLoader(BaseLoader):
	def get_source(self, environment, template):
		from pybble.models import Template
		from pybble.database import NoResult

		if isinstance(template,Template):
			t = template
		else:
			try:
				t = Template.q.get_by(name=template)
			except NoResult:
				raise TemplateNotFound(template)
		mtime = t.modified
		return (t.data,
				"//db/%s/%s/%s" % (t.__class__.__name__,t.id,template),
				lambda: t.modified != mtime) 
	
jinja_env = Environment(loader=DatabaseLoader(), autoescape=True)

expose_map = {}
def expose(rule, **kw):
	def decorate(f):
		name = "%s.%s" % (f.__module__,f.__name__)
		kw['endpoint'] = name
		expose_map[name] = f
		url_map.add(Rule(rule, **kw))
		return f
	return decorate

## jinja extensions
marker = Markdown(extensions = ['wikilinks'])
jinja_env.filters['markdown'] = lambda a: Markup(marker.convert(a))

def url_for(endpoint, _external=False, **values):
	return local.url_adapter.build(endpoint, values, force_external=_external)
jinja_env.globals['url_for'] = url_for

def name_discr(id):
	from pybble.models import Discriminator
	if id is None:
		return "*"
	return Discriminator.q.get_by(id=id).name
jinja_env.globals['name_discr'] = name_discr

def name_detail(id):
	from pybble.models import TM_DETAIL_name
	return TM_DETAIL_name(id)
jinja_env.globals['name_detail'] = name_detail


def render_my_template(request, obj, detail=None, resp=True, **context):
	"""Global render"""
	from pybble.models import TemplateMatch, TM_DETAIL_PAGE
	from pybble.database import NoResult

	if detail is None:
		detail = TM_DETAIL_PAGE

	context["obj"] = obj

	t = None
	discr = obj.discriminator
	no_inherit = True

	try:
		t = obj.get_template(detail=detail)
	except NoResult:
		t = "missing_%d.html" % (detail,)

	return render_template(t, resp=resp, **context)

def render_template(template, resp=True,**context):
	if current_request:
		from pybble.flashing import get_flashed_messages
		context.update(
			XHTML_DTD=Markup(get_dtd()),
			# CURRENT_URL=current_request.build_absolute_uri(),
			USER=current_request.user,
			MESSAGES=get_flashed_messages(),
			SITE=current_request.site,
		)
	r = jinja_env.get_template(template).render(**context)
	if resp:
		r = Response(r, mimetype='text/html')
	else:
		r = Markup(r)
	return r

jinja_env.globals['subpage'] = lambda a,b: render_my_template(current_request,a,b,resp=False)

def validate_url(url):
	return urlparse(url)[0] in ALLOWED_SCHEMES

def get_random_uid():
	return ''.join(sample(URL_CHARS, randrange(3, 9)))

pybble_dtd = None

def get_dtd():
	"""
	This returns either our dtd or our dtd + xml comment.  Neither is stricly
	valid as XML documents with custom doctypes must be served as XML but
	currently as MSIE is pain in the ass we have to workaround that IE bug
	by removing the XML PI comment.
	"""
	global pybble_dtd
	if pybble_dtd is None:
		dtd_path = url_for('static', file='xhtml1-strict-uu.dtd')
		pybble_dtd = '<!DOCTYPE html SYSTEM "%s">' % dtd_path
	try:
		ua = UserAgent(current_request.META['HTTP_USER_AGENT'])
		if ua.browser == 'msie':
			return pybble_dtd
	except Exception:
		pass
	return '<?xml version="1.0" encoding="utf-8"?>\n' + pybble_dtd


class Pagination(object):

	def __init__(self, query, per_page, page, endpoint):
		self.query = query
		self.per_page = per_page
		self.page = page
		self.endpoint = endpoint

	@cached_property
	def count(self):
		return self.query.count()

	@cached_property
	def entries(self):
		return self.query.offset((self.page - 1) * self.per_page) \
						.limit(self.per_page).all()

	has_previous = property(lambda x: x.page > 1)
	has_next = property(lambda x: x.page < x.pages)
	previous = property(lambda x: url_for(x.endpoint, page=x.page - 1))
	next = property(lambda x: url_for(x.endpoint, page=x.page + 1))
	pages = property(lambda x: max(0, x.count - 1) // x.per_page + 1)

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

