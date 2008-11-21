# -*- coding: utf-8 -*-

from os import path
from urlparse import urlparse
from random import sample, randrange
from jinja2 import Environment, BaseLoader
from werkzeug import Response, Local, LocalManager, cached_property
from werkzeug.routing import Map, Rule


TEMPLATE_PATH = path.join(path.dirname(__file__), 'templates')
# used for initial import only

STATIC_PATH = path.join(path.dirname(__file__), 'static')
ALLOWED_SCHEMES = frozenset(['http', 'https', 'ftp', 'ftps'])
URL_CHARS = 'abcdefghijkmpqrstuvwxyzABCDEFGHIJKLMNPQRST23456789'

local = Local()
local_manager = LocalManager([local])
application = local('application')

url_map = Map([Rule('/static/<file>', endpoint='static', build_only=True)])

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
	
jinja_env = Environment(loader=DatabaseLoader())


def expose(rule, **kw):
    def decorate(f):
        kw['endpoint'] = f.__name__
        url_map.add(Rule(rule, **kw))
        return f
    return decorate

def url_for(endpoint, _external=False, **values):
    return local.url_adapter.build(endpoint, values, force_external=_external)
jinja_env.globals['url_for'] = url_for

def render_template(template, **context):
    return Response(jinja_env.get_template(template).render(**context),
                    mimetype='text/html')

def validate_url(url):
    return urlparse(url)[0] in ALLOWED_SCHEMES

def get_random_uid():
    return ''.join(sample(URL_CHARS, randrange(3, 9)))


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
def random_string(bytes=9, base="23456789abcdefghijkmnpqrstuvwxyz", dash="",
				dash_step=6):
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
		if dash_step and fm and not (len(passwd)+1)%dash_step:
			passwd += dash
		bytes -= 1
	return passwd

