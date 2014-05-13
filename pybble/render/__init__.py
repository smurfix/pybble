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
from werkzeug import cached_property
from werkzeug.http import parse_etags, remove_entity_headers, http_date
from werkzeug.routing import Map, Rule
from flask import request,current_app, get_flashed_messages, Response

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

import logging
logger = logging.getLogger('pybble.render')

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

def render_my_template(obj, detail=None, mimetype=NotGiven, **context):
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

class TaggedMarkup(Markup):
	success = None
	@property
	def text(self):
		return self

def render_template(template, mimetype=NotGiven, **context):
	#template = current_app.jinja_env.get_template(template)
	from .loader import get_template
	template = get_template(template)

	user = getattr(request,"user",None)
	msgs = []
	for c,m in get_flashed_messages(with_categories=True):
		m = TaggedMarkup.escape(m)
		m.success = c
		msgs.append(m)

	context.update(
		# CURRENT_URL=request.build_absolute_uri(),
		USER=getattr(request,"user",None),
		MESSAGES=msgs,
		SITE=request.site,
		CRUMBS=(user.groups+list(p.parent for p in user.all_visited()[0:20])) if user else None,
		NOW=datetime.utcnow(),
	)

	r = template.render(**context)
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
	return render_my_template(mimetype=None, **ctx)

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
		return render_my_template(mimetype=None, **ctx)
	except AuthError:
		if detail == TM_DETAIL_EMAIL:
			raise
		else:
			return Markup("<p>'%s' kann nicht dargestellt werden (Zugriffsfehler).</p>" % (obj.oid(),))

pybble_dtd = None
def get_dtd():
	"""\
		Pybble now does HTML5. No DTD stupidity and no incomplete charsets allowed.
		"""
	return """\
<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
"""

import smtplib
import email.Message

def send_mail(to='', template='', server=None, **context):
	if "site" not in context:
		context["site"] = request.site
	if "user" not in context:
		context["user"] = request.user
	rand = random_string(8)
	for x in range(3):
		context["id"+str(x)] = "%d.%s%d@%s" % (time(),random_string(10),x,request.site.domain)
	
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
