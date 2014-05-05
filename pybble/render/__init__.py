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

from jinja2 import Environment, BaseLoader, Markup, contextfunction, contextfilter
from werkzeug import cached_property, Response
from werkzeug.http import parse_etags, remove_entity_headers, http_date
from werkzeug.routing import Map, Rule
from flask import request,current_app

from ..utils import random_string, AuthError, NotGiven
from ..core.models import PERM, PERM_NONE, PERM_ADD, obj_get, \
	Discriminator, TM_DETAIL_PAGE, TM_DETAIL_SUBPAGE, TM_DETAIL_STRING, obj_class, obj_get, TM_DETAIL, \
	TM_DETAIL_DETAIL, TM_DETAIL_RSS, TM_DETAIL_EMAIL, TM_DETAIL_name, MissingDummy
from ..core.models._descr import D
from ..core.models.user import Permission
from ..core.models.template import TemplateMatch, Template
from ..core.models.files import StaticFile
from ..core.db import db,NoData
from ..utils.diff import textDiff,textOnlyDiff

from wtforms.validators import ValidationError
from time import time
from datetime import datetime,timedelta
import sys,os

url_map = Map([Rule('/static/<file>', endpoint='static', build_only=True)])

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
			if not request.user.can_do(obj, discr=obj,want=right):
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
			if isinstance(template,str): template = unicode(template)
			site = current_app.site
			t = None
			while site:
				try: t = Template.q.get_by(name=template,superparent=site)
				except NoData: pass
				else: break
				site = site.parent
			if t is None:
				raise TemplateNotFound(template)
		mtime = t.modified
		return (t.data,
				"//db/%s/%s/%s" % (t.__class__.__name__,(t.superparent or current_app.site).domain,getattr(t,"name",t.oid())),
				lambda: False ) # t.modified != mtime) 
	
def add_to_jinja(jinja_env):

	expose_map = {}
	def expose(rule, **kw):
		def decorate(f):
			name = "%s.%s" % (f.__module__,f.__name__)
			kw['endpoint'] = name
			expose_map[name] = f
			url_map.add(Rule(rule, **kw))
			return f
		return decorate

	def render(obj, *a,**kw):
		if hasattr(obj,"render"):
			return obj.render(*a,**kw)
		else:
			return Markup.escape(unicode(obj))
	jinja_env.filters['render'] = render

	def cdata(data): ## [[[[
		return Markup("<![CDATA[")+data.replace("]]>","]] >")+Markup("]]>")
	jinja_env.filters['cdata'] = cdata

	def datetimeformat(value, format='%Y-%m-%d %H:%M'):
		return value.strftime(format)
	jinja_env.filters['date'] = datetimeformat

	jinja_env.globals['url'] = lambda: request.url

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
	jinja_env.globals['textdiff'] = textOnlyDiff

	for did,dname in D.items():
		jinja_env.globals[str("d_"+dname.lower())] = did

	for tm,name in TM_DETAIL.items():
		jinja_env.globals[str("tm_"+name.lower())] = tm

	def addables(obj):
		u = request.user
		if not hasattr(u,"_can_add"):
			u._can_add = {}
		u = u._can_add

		g = u.get(obj.id,None)
		if g is None:
			g = []
			for d in db.store.find(Discriminator, ):
#			if getattr(obj_class(d.id),"_no_crumbs",False):
#				continue
				if request.user.can_add(obj, discr=obj.discriminator, new_discr=d.id):
					g.append((d.id,d.display_name or d.name, d.infotext))
			u[obj.id] = g
		return g
	jinja_env.globals['addables'] = addables

	jinja_env.globals['subpage'] = render_subpage
	jinja_env.globals['subline'] = render_subline
	jinja_env.globals['subrss'] = render_subrss

	# Permission checks for templates: {% if can_edit() %} -- menu -- {% endif %}
	for a,b in PERM.iteritems():
		def can_do_closure(a,b):
			def can_do(env, obj=None, discr=None):
				if discr is None:
					if isinstance(obj,(int,long)):
						discr=obj
						obj=None
				if obj is None:
					obj = env.get('obj',None)
				if isinstance(obj,basestring):
					obj = obj_get(obj)
				u = getattr(request,"user",None)
				if current_app.config.DEBUG_ACCESS:
					print("can_do_"+b+":", u,obj,discr,a, file=sys.stderr)
				if not u:
					return False
				if a > PERM_NONE:
					return u.can_do(obj, discr=discr) >= a
				elif a == PERM_ADD:
					return u.can_do(obj, discr=obj, new_discr=discr, want=a) == a
				else:
					return u.can_do(obj, discr=discr, want=a) == a
			can_do.contextfunction = 1 # Jinja

			def will_do(env, obj=None):
				if obj is None:
					obj = env.vars['obj']
				if isinstance(obj,basestring):
					obj = obj_get(obj)
				u = getattr(request,"user",None)
				if current_app.config.DEBUG_ACCESS:
					print("will_do_"+b+":", u,obj,a, file=sys.stderr)
				if not u:
					raise AuthError(obj,a)
				if a > PERM_NONE:
					if u.can_do(obj) < a:
						raise AuthError(obj,a)
				else:
					if u.can_do(obj, want=a) != a:
						raise AuthError(obj,a)
			will_do.contextfunction = 1 # Jinja

			return can_do,will_do
		c,d = can_do_closure(a,b)
		jinja_env.globals['can_' + b.lower()] = c
		jinja_env.globals['will_' + b.lower()] = d

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

	if detail == TM_DETAIL_PAGE or detail == TM_DETAIL_SUBPAGE or detail == TM_DETAIL_DETAIL:
		request.user.visits(obj)

	context["obj"] = obj

	try:
		t = obj.get_template(detail=detail)
	except NoData:
		t = "missing_%d.html" % (detail,)
	except MissingDummy:
		t = "missing_0.html"

	return render_template(t, mimetype=mimetype, **context)

def render_template(template, mimetype=NotGiven, **context):
	if isinstance(template,str): template = unicode(template)
	if request:
		from pybble.flashing import get_flashed_messages
		user = getattr(request,"user",None)
		context.update(
			# CURRENT_URL=request.build_absolute_uri(),
			USER=getattr(request,"user",None),
			MESSAGES=get_flashed_messages(),
			SITE=current_app.site,
			CRUMBS=(user.groups+list(p.parent for p in user.all_visited()[0:20])) if user else None,
			NOW=datetime.utcnow(),
		)
	r = current_app.jinja_env.get_template(template).render(**context)
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
	p,s,o,d = obj.pso
	ctx["obj_parent"] = p
	ctx["obj_superparent"] = s
	ctx["obj_owner"] = o
	ctx["obj_deleted"] = d
	ctx["detail"] = detail
	if discr is not None:
		ctx["sub"] = db.filter_by(obj_class(discr), parent=obj).count()
	return render_my_template(request, mimetype=None, **ctx)

@contextfunction
def render_subline(ctx,obj):
	try:
		return render_subpage(ctx,obj, detail=TM_DETAIL_STRING)
	except AuthError:
		return unicode(obj)

@contextfunction
def render_subrss(ctx,obj, detail=TM_DETAIL_RSS, discr=None):
	ctx = ctx.get_all()
	ctx["obj"] = obj.parent.parent
	ctx["tracker"] = obj.superparent
	ctx["user"] = obj.parent.owner
	ctx["usertracker"] = obj
	ctx["detail"] = detail
	try:
		return render_my_template(request, mimetype=None, **ctx)
	except AuthError:
		if detail == TM_DETAIL_EMAIL:
			raise
		else:
			return Markup("<p>'%s' kann nicht dargestellt werden (Zugriffsfehler).</p>" % (obj.oid(),))

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
		ua = UserAgent(request.META['HTTP_USER_AGENT'])
		if ua.browser == 'msie':
			return pybble_dtd
	except Exception:
		pass
	return '<?xml version="1.0" encoding="utf-8"?>\n' + pybble_dtd

import smtplib
import email.Message

def send_mail(to='', template='', server=None, **context):
	if "site" not in context:
		context["site"] = current_app.site
	if "user" not in context:
		context["user"] = request.user
	rand = random_string(8)
	for x in range(3):
		context["id"+str(x)] = "%d.%s%d@%s" % (time(),random_string(10),x,current_app.site.domain)
	
	if server:
		mailServer = server
	else:
		mailServer = smtplib.SMTP(current_app.config.MAILHOST)
	mailServer.sendmail(context["site"].owner.email, to, current_app.jinja_env.get_template(template).render(**context).encode("utf-8"))
	if not server:
		mailServer.quit()

# Permission checks for templates: {% if can_edit() %} -- menu -- {% endif %}
for a,b in PERM.iteritems():
	def can_do_closure(a,b):
		def valid_do(form, field):
			obj = obj_get(field.data)
			u = getattr(request,"user",None)
			if not u:
				raise ValidationError(u"Kein Benutzer")
			if current_app.config.DEBUG_ACCESS:
				print("valid can_"+b+":", u,obj,a, file=sys.stderr)
			if (u.can_do(obj, discr=obj, want=a) < a) \
				if (a > PERM_NONE) \
				else (u.can_do(obj, discr=obj, want=a) != a):
				raise ValidationError(u"Kein Zugriff auf Objekt '%s' (%s)" % (field.data,b))

		def valid_do_self(form, field):
			obj = obj_get(field.data)
			u = getattr(request,"user",None)
			if not u:
				raise ValidationError(u"Kein Benutzer")
			if current_app.config.DEBUG_ACCESS:
				print("valid can_self_"+b+":", u,obj,a, file=sys.stderr)
			if u is obj:
				return
			if (u.can_do(obj, discr=obj, want=a) < a) \
				if (a > PERM_NONE) \
				else (u.can_do(obj, discr=obj, want=a) != a):
				raise ValidationError(u"Kein Zugriff auf Objekt '%s' (%s)" % (field.data,b))

		return valid_do,valid_do_self
	e,f = can_do_closure(a,b)
	globals()['valid_' + b.lower()] = e
	globals()['valid_' + b.lower() + '_self'] = f

#class Pagination(object):
#	def __init__(self, query, per_page, page, endpoint):
#		self.query = query
#		self.per_page = per_page
#		self.page = page
#		self.endpoint = endpoint
#
#	@cached_property
#	def count(self):
#		return self.query.count()
#
#	@cached_property
#	def entries(self):
#		return self.query.offset((self.page - 1) * self.per_page) \
#						.limit(self.per_page).all()
#
#	has_previous = property(lambda x: x.page > 1)
#	has_next = property(lambda x: x.page < x.pages)
#	previous = property(lambda x: url_for(x.endpoint, page=x.page - 1))
#	next = property(lambda x: url_for(x.endpoint, page=x.page + 1))
#	pages = property(lambda x: max(0, x.count - 1) // x.per_page + 1)

def add_to_app(app):
	@app.route("/static/<path:path>")
	def serve_path(request,path):
		site = current_app.site
		while site:
			try:
				sf = StaticFile.q.get_by(superparent=site, path=path)
			except NoData:
				site = site.parent
				if not site:
					raise
			else:
				break

		if parse_etags(request.environ.get('HTTP_IF_NONE_MATCH')).contains(sf.hash):
			r = Response("", mimetype=sf.mimetype)
			r.status_code = 304
			remove_entity_headers(r.headers)
		else:
			r = Response(sf.content, mimetype=sf.mimetype)
		r.set_etag(sf.hash)
		r.headers['Cache-Control']='public'
		r.headers['Expiry']=http_date(datetime.utcnow()+timedelta(0,current_app.config.STATIC_EXPIRE))
		r.headers['Last-Modified']=http_date(sf.modified)
		return r

	@app.route("/download/<oid>")
	@app.route("/download/<oid>/<name>")
	def download(request,oid,name=None):
		obj = obj_get(oid)
		r = Response(obj.content, mimetype=obj.mimetype)
		if name:
			n = obj.name
			if obj.mime.ext:
				n += "."+obj.mime.ext
			assert n == name

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

def list_renderers():
	path = os.path.dirname(os.path.abspath(__file__))
	dir_list = os.listdir(path)
	for fname in dir_list:
		if os.path.exists(os.path.join(path, fname, '__init__.py')) and \
				not os.path.exists(os.path.join(path, fname, 'DISABLED')):
			yield fname

def load_app_renderer(app):
	## TODO? if renderers can ever be parameterized per-site, do that here
	from ..core.models import Renderer
	for r in Renderer.q.all():
		r = r.mod()
		r.setup_app(app)

class Renderer(object):
	"""Base class for rendering"""
	def render(self,obj):
		raise NotImplementedError("You need to implement ‘{}.render()’".format(self.__class__.__name__))
