# -*- coding: utf-8 -*-

from jinja2 import Environment, BaseLoader, Markup
from werkzeug import cached_property, Response
from werkzeug.routing import Map, Rule
from markdown import Markdown
from pybble.utils import current_request, local
from pybble.models import PERM, PERM_NONE, Permission

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
marker = Markdown(
    extensions = ['wikilinks'], 
    extension_configs = {'wikilinks': [
                                      ('base_url', '/wiki/'), 
                                      ('end_url', ''), 
                                      ('html_class', 'wiki') ]},
    safe_mode = True,
)
jinja_env.filters['markdown'] = lambda a: Markup(marker.convert(a))

def url_for(endpoint, _external=False, **values):
	return local.url_adapter.build(endpoint, values, force_external=_external)
jinja_env.globals['url_for'] = url_for

jinja_env.globals['url'] = lambda: current_request.url

def name_discr(id):
	from pybble.models import Discriminator
	if id is None or id == "None":
		return "*"
	return Discriminator.q.get_by(id=int(id)).name
jinja_env.globals['name_discr'] = name_discr

def name_detail(id):
	from pybble.models import TM_DETAIL_name
	return TM_DETAIL_name(id)
jinja_env.globals['name_detail'] = name_detail

def name_permission(id):
	from pybble.models import PERM_name
	return PERM_name(id)
jinja_env.globals['name_permission'] = name_permission


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



# Permission checks for templates: {% if can_edit() %} -- menu -- {% endif %}
for a,b in PERM.iteritems():
	def can_do_closure(a,b):
		def can_do(env, obj=None):
			if obj is None:
				obj = env.vars['obj']
			if a > PERM_NONE:
				return Permission.can_do(current_request.user, obj) >= a
			else:
				return Permission.can_do(current_request.user, obj) <= a
		can_do.contextfunction = 1 # Jinja
		return can_do
	jinja_env.globals['can_' + b.lower()] = can_do_closure(a,b)


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


