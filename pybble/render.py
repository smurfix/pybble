# -*- coding: utf-8 -*-

from jinja2 import Environment, BaseLoader, Markup, contextfunction
from werkzeug import cached_property, Response
from werkzeug.http import parse_etags, remove_entity_headers
from werkzeug.routing import Map, Rule
from werkzeug.utils import http_date
from pybble.utils import current_request, local, random_string
from pybble.models import PERM, PERM_NONE, PERM_ADD, Permission, obj_get, TemplateMatch, Template, \
	Discriminator, TM_DETAIL_PAGE, TM_DETAIL_SUBPAGE, TM_DETAIL_STRING, obj_class, StaticFile, obj_get, TM_DETAIL
from pybble.database import NoResult
from pybble.diff import textDiff
from wtforms.validators import ValidationError
from time import time
from datetime import datetime,timedelta
import settings

url_map = Map([Rule('/static/<file>', endpoint='static', build_only=True)])

try:
	discr_list = list(Discriminator.q.all())
except Exception:
	discr_list = [] # if not set up yet
discr_list.sort(cmp=lambda a,b: cmp(a.name,b.name))

def valid_obj(form, field):
	"""Field verifier which checks that an object ID is valid"""
	try:
		obj_get(field.data)
	except Exception:
		raise ValidationError(u"Das Objekt '%s' gibt es nicht" % (field.data,))

def valid_access(o):
	"""\
		Return a validator which checks that the user has
		the rights on the object in field 'o'
		"""
	def v_a(form, field):
		try:
			obj = obj_get(getattr(form,o).data)
			right = int(field.data)
		except Exception:
			return # checked by others
		else:
			if not current_request.user.can_do(obj,obj.discriminator,want=right):
				raise ValidationError(u"Das darfst du selbst nicht.")

	return v_a

class TemplateNotFound(IOError, LookupError):
	"""
	A template was not found by the template loader.
	"""

	def __init__(self, name):
		IOError.__init__(self, name)
		self.name = name

class DatabaseLoader(BaseLoader):
	def get_source(self, environment, template):
		if isinstance(template,(Template,TemplateMatch)):
			t = template
		else:
			s = current_request.site
			t = None
			while s:
				try: t = Template.q.get_by(name=template)
				except NoResult: pass
				else: break
				s = s.parent
			if t is None:
				raise TemplateNotFound(template)
		mtime = t.modified
		return (t.data,
				"//db/%s/%s" % (t.__class__.__name__,getattr(t,"name",t.oid())),
				lambda: True ) # t.modified != mtime) 
	
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
try:
	from markdown import Markdown
	marker = Markdown(
    	extensions = ['wikilinks'], 
    	extension_configs = {'wikilinks': [
	                                      ('base_url', '/wiki/'), 
	                                      ('end_url', ''), 
	                                      ('html_class', 'wiki') ]},
    	safe_mode = False
	)
	jinja_env.filters['markdown'] = lambda a: Markup(marker.convert(a))
except TypeError: # old markdown
	from markdown import markdown
	jinja_env.filters['markdown'] = markdown.markdown

def render(obj, *a,**kw):
	if hasattr(obj,"render"):
		return obj.render(*a,**kw)
	else:
		return Markup.escape(unicode(obj))
jinja_env.filters['render'] = render

def render_markdown(obj):
	return Markup(marker.convert(obj.data))

def url_for(endpoint, _external=False, **values):
	return local.url_adapter.build(endpoint, values, force_external=_external)
jinja_env.globals['url_for'] = url_for

jinja_env.globals['url'] = lambda: current_request.url

def name_discr(id):
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
	return PERM_name(id).lower()
jinja_env.globals['name_permission'] = name_permission

jinja_env.globals['diff'] = textDiff

for d in discr_list:
	jinja_env.globals[str("d_"+d.name.lower())] = d.id

for tm,name in TM_DETAIL.items():
	jinja_env.globals[str("tm_"+name.lower())] = tm

def addables(obj):
	u = current_request.user
	if not hasattr(u,"_can_add"):
		u._can_add = {}
	u = u._can_add

	g = u.get(obj.id,None)
	if g is None:
		g = []
		for d in Discriminator.q.all():
#			if getattr(obj_class(d.id),"_no_crumbs",False):
#				continue
			if current_request.user.can_add(obj, discr=obj.discriminator, new_discr=d.id):
				g.append((d.id,d.name))
		u[obj.id] = g
	return g
jinja_env.globals['addables'] = addables

class NotGiven: pass

def render_my_template(request, obj, detail=None, mimetype=NotGiven, **context):
	"""Global render"""

	if isinstance(obj,basestring):
		obj = obj_get(obj)
	if detail is None:
		detail = TM_DETAIL_PAGE
	if detail == TM_DETAIL_PAGE:
		request.user.will_read(obj)
	else:
		request.user.will_list(obj)

	context["obj"] = obj

	t = None
	discr = obj.discriminator
	no_inherit = True

	try:
		t = obj.get_template(detail=detail)
	except NoResult:
		t = "missing_%d.html" % (detail,)

	return render_template(t, mimetype=mimetype, **context)

def render_template(template, mimetype=NotGiven, **context):
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
	if mimetype:
		if mimetype is NotGiven:
			mimetype="text/html"
		r = Response(r, mimetype=mimetype)
	else:
		r = Markup(r)
	return r

@contextfunction
def render_subpage(ctx,obj, detail=TM_DETAIL_SUBPAGE, discr=None):
	ctx = ctx.get_all()
	ctx["obj"] = obj
	if discr is not None:
		ctx["sub"] = obj_class(discr).q.filter_by(parent=obj).count()
	return render_my_template(current_request, mimetype=None, detail=detail, **ctx)

@contextfunction
def render_subline(ctx,obj):
	return render_subpage(ctx,obj, detail=TM_DETAIL_STRING)

jinja_env.globals['subpage'] = render_subpage
jinja_env.globals['subline'] = render_subline


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
		dtd_path = url_for('static', file='xhtml1-strict-pybble.dtd')
		pybble_dtd = '<!DOCTYPE html SYSTEM "%s">' % dtd_path
	try:
		ua = UserAgent(current_request.META['HTTP_USER_AGENT'])
		if ua.browser == 'msie':
			return pybble_dtd
	except Exception:
		pass
	return '<?xml version="1.0" encoding="utf-8"?>\n' + pybble_dtd


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



# Permission checks for templates: {% if can_edit() %} -- menu -- {% endif %}
for a,b in PERM.iteritems():
	def can_do_closure(a,b):
		def valid_do(form, field):
			obj = obj_get(field.data)
			if (current_request.user.can_do(obj, discr=obj.discriminator, want=a) < a) \
				if (a > PERM_NONE) \
				else (current_request.user.can_do(obj, discr=obj.discriminator, want=a) != a):
				raise ValidationError(u"Kein Zugriff auf Objekt '%s' (%s)" % (field.data,b))

		def can_do(env, obj=None, discr=None):
			if discr is None:
				if isinstance(obj,int):
					discr=obj
					obj=None
			if obj is None:
				obj = env.get('obj',None)
			if a > PERM_NONE:
				return current_request.user.can_do(obj, discr=discr) >= a
			elif a == PERM_ADD:
				return current_request.user.can_do(obj, discr=obj.discriminator, new_discr=discr, want=a) == a
			else:
				return current_request.user.can_do(obj, discr=discr, want=a) == a
		can_do.contextfunction = 1 # Jinja

		def will_do(env, obj=None):
			if obj is None:
				obj = env.vars['obj']
			if a > PERM_NONE:
				if current_request.user.can_do(obj) < a:
					raise AuthError(obj,a)
			else:
				if current_request.user.can_do(obj, want=a) != a:
					raise AuthError(obj,a)
		will_do.contextfunction = 1 # Jinja

		return can_do,will_do,valid_do
	c,d,e = can_do_closure(a,b)
	jinja_env.globals['can_' + b.lower()] = c
	jinja_env.globals['will_' + b.lower()] = d
	globals()['valid_' + b.lower()] = e


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


@expose("/static/<path:path>")
def serve_path(request,path):
	sf = StaticFile.q.get_by(superparent=request.site, path=path)

	if parse_etags(request.environ.get('HTTP_IF_NONE_MATCH')).contains(sf.hash):
		r = Response("", mimetype=sf.mimetype)
		r.status_code = 304
		remove_entity_headers(r.headers)
	else:
		r = Response(sf.content, mimetype=sf.mimetype)
	r.set_etag(sf.hash)
	r.headers['Cache-Control']='public'
	r.headers['Expiry']=http_date(datetime.utcnow()+timedelta(0,settings.STATIC_EXPIRE))
	r.headers['Last-Modified']=http_date(sf.modified)
	return r

@expose("/download/<oid>")
@expose("/download/<oid>/<name>")
def download(request,oid,name=None):
	obj = obj_get(oid)
	r = Response(obj.content, mimetype=obj.mimetype)

	if parse_etags(request.environ.get('HTTP_IF_NONE_MATCH')).contains(obj.hash):
		r = Response("", mimetype=obj.mimetype)
		r.status_code = 304
		remove_entity_headers(r.headers)
	else:
		r = Response(obj.content, mimetype=obj.mimetype)

	r.set_etag(obj.hash)
	r.headers['Cache-Control']='public'
	r.headers['Expiry']=http_date(datetime.utcnow()+timedelta(999))
	r.headers['Last-Modified']=http_date(obj.timestamp)
	return r

