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

from jinja2 import Markup, contextfunction, contextfilter, TemplateNotFound
from werkzeug.utils import reraise
from flask import request,current_app, get_flashed_messages, Response, g, escape
from flask._compat import string_types, text_type
from sqlalchemy.orm import aliased
from sqlalchemy import or_

from ..utils import random_string, AuthError, NotGiven
from ..core.models._const import PERM, PERM_NONE, PERM_ADD, \
	TM_DETAIL_PAGE, TM_DETAIL_SUBPAGE, TM_DETAIL_STRING, TM_DETAIL, \
	TM_DETAIL_DETAIL, TM_DETAIL_RSS, TM_DETAIL_EMAIL, TM_MIME, TM_DETAIL_name
from ..core.models.permit import Permission
from ..core.models.site import SiteBlueprint,Blueprint
from ..core.models.template import TemplateMatch, Template
from ..core.models.files import StaticFile
from ..core.models.types import MIMEtype,MIMEadapter
from ..core.models.object import Object
from ..core.db import db,NoData
from ..globals import current_site

from wtforms.validators import ValidationError
from time import time
from datetime import datetime
import sys,os

import logging
logger = logging.getLogger('pybble.render')

class MIMEprop(object):
	"""\
		A referral to a cached MIME property. Use as:

			class Whatever(Object):
				mimetype = MIMEprop('something_unique')
		"""
	def __init__(self, name):
		self.name = '_'+name+'_mime'

	def __get__(self, obj, type=None):
		if obj is None:
			return self
		return getattr(obj,self.name)

	def __set__(self, obj, value):
		if value is not None:
			value = MIMEtype.get(value)
		setattr(obj,self.name,value)
	def __delete__(self, obj):
		setattr(obj,self.name,None)

class ContentData(object):
	"""\
		This object defines the data I want, the data I have, and the
		search space used for going from A to B.

		Actual search is handled in pybble.render.loader.

		Values:
			`obj`: The object which the original URL refers to
			`anchor`: Start of the template search; usually the object, else the site.
			`from_mime`: Type of this content
			`to_mime`: Type I want conversion to
			`blueprint`: The current/named blueprint, which the search should also examine.
			`name`: If looking for a named template
			`template_in_blueprint`: Flag whether the template name may have the blueprint name as a prefix
			`content`: the content `from_mime` applies to
			`site`: the domain we're looking at. A template search proceeds from the `anchor` through its `parent` pointer, but when encountering `site`, the process is interrupted while the blueprint is examined.
		
		"""
	from_mime = MIMEprop('from')
	to_mime = MIMEprop('to')

	def __init__(self, obj=None, content=None, anchor=None, site=None, from_mime=NotGiven,to_mime=NotGiven, name=None, blueprint=None):

		if site is None:
			site = current_site

		if from_mime is NotGiven:
			if content is None:
				content = obj
			if content is None:
				from_mime = MIMEtype.get('pybble','_empty')
			elif hasattr(content,"mime"):
				from_mime = content.mime
			else:
				raise RuntimeError("No source MIME type")
		if to_mime is NotGiven:
			best = request.accept_mimetypes.best
			if best is None: ## no Accept header sent
				best = "text/html"
			try:
				to_mime = MIMEtype.get(best)
			except KeyError as e:
				exc_info = sys.exc_info()
				for k in ('text/html','text/plain','application/json'):
					if request.accept_mimetypes[k]:
						try:
							to_mime = MIMEtype.get(k)
						except KeyError:
							pass
						else:
							break
				else:
					reraise(*exc_info)
			## TODO: use some other type if the client wants something exotic
			#			    return best == 'application/json' and \
			#				        request.accept_mimetypes[best] > \
			#						        request.accept_mimetypes['text/html']
			
		template_in_blueprint = False

		if blueprint is None:
			blueprint = getattr(request,'bp',None)
			if blueprint is None and name is not None and '/' in name:
				bpname,tname = name.split('/',1)
				try: # the name might refer to my SiteBlueprint
					bp = SiteBlueprint.q.get_by(site=site,name=bpname)
				except NoData: # or to the Blueprint it points to
					try:
						bp = SiteBlueprint.q.filter(SiteBlueprint.site==site).join(Blueprint, SiteBlueprint.blueprint).filter(Blueprint.name==bpname).limit(1).one()
					except NoData:
						bp = None
				if bp is not None:
					blueprint = bp

		self.obj = obj
		self.anchor = anchor or getattr(g,'anchor',None) or obj or site
		self.from_mime = from_mime
		self.to_mime = to_mime
		self.blueprint = blueprint
		self.name = name
		self.template_in_blueprint = template_in_blueprint
		self.content = content
		self.site = site

	def environment(self):
		return dict((k,v) for k,v in self.__dict__.items() if not k.startswith('_') and v is not None)
	
	def clone(self,**vars):
		c = type(self)()
		c.__dict__.update(self.__dict__)
		c.__dict__.update(vars)
		return c

	def __call__(self, environ,start_response):
		raise NotImplementedError("completely untested and probably wrong")
		from pybble.app import Response
		res = Response.force_type(self)
		return res(environ,start_response)

	@property
	def template(self):
		from .loader import get_template
		return get_template(self)[0]
		
	def render(self, _vars={}, _intermediate = True, **vars):
		if _vars:
			assert not vars
			vars=_vars
		logger.debug("RENDER: "+repr(self.__dict__))
		if self.from_mime == self.to_mime:
			assert self.content
			return self.content
		try:
			old_anchor = getattr(g,'anchor',None)
			try:
				t = self.template
			except TemplateNotFound:
				## try to find some intermediate solution?
				if not _intermediate:
					raise
				self.render_with_intermediate(vars)
			else:
				t.render(self, vars)

			if self.to_mime.typ == "html" or self.to_mime.subtyp == "html":
				self.content = Markup(self.content)
			return self.content

		finally:
			g.anchor = old_anchor
	
	def render_with_intermediate(self, vars):
		from .loader import get_template

		r1 = r2 = w = None
		ma = aliased(MIMEadapter)
		mb = aliased(MIMEadapter)
		for a,b in ma.q.join(mb).filter(
				or_(ma.from_mime==self.from_mime,ma.from_mime==MIMEtype.get(self.from_mime.typ,"*")),
				mb.to_mime==self.to_mime,
				ma.to_mime_id==mb.from_mime_id,
				ma.id != mb.id):
			try:
				wx = 100 if a.from_mime.subtyp == "*" else 0
				c1 = self.clone(to_mime=a.to_mime, from_mime=a.from_mime)
				c2 = self.clone(from_mime=b.from_mime)
				t1,w1 = get_template(c1)
				t2,w2 = get_template(c2)
				if w is None or w > w1+w2+wx:
					w = w1+w2+wx
					r1 = t1
					r2 = t2
			except TemplateNotFound:
				pass
		if w is None:
			raise
		c2.content = c1.render(_intermediate = False, _vars=vars).content
		self.content = c2.render(_intermediate = False, _vars=vars).content
		return self.content

	def __str__(self):
		if self.content:
			return self.content
		return ("{}({})".format(self.__class__.__name__,",".join( str(k)+'='+repr(v) for k,v in self.__dict__.items() if k[0] != '_' and v is not None)))

	def __html__(self):
		if self.content:
			return escape(self.content)
		return escape(str(self))

	def __iter__(self):
		yield self.content

def valid_obj(form, field):
	"""Field verifier which checks that an object ID is valid"""
	try:
		Object.by_oid(field.data)
	except Exception:
		raise ValidationError(u"Das Objekt '%s' gibt es nicht" % (field.data,))

def valid_access(o):
	"""\
		Return a validator which checks that the user has
		the rights on the object in field 'o'
		"""
	def v_a(form, field):
		try:
			obj = Object.by_oid(getattr(form,o).data)
			right = int(field.data)
		except Exception:
			return # checked by others
		else:
			if not request.user.can_do(obj, objtyp=obj,want=right):
				raise ValidationError(u"Das darfst du selbst nicht.")

	return v_a

def render_template(template, _root=None, **context):
	"""\
		Renders a named template with the given context.

		:param template: the name of the template to be
		                 rendered, or an iterable with template names
		                 the first one existing will be rendered
		:param context: the variables that will be available in the
		                context of the template.
		"""
	if isinstance(template,string_types):
		c = ContentData(name=text_type(template), anchor=_root)
		return c.render(_vars=context)

	for tn in template:
		try:
			return render_template(tn,**context)
		except TemplateNotFound:
			pass
	raise TemplateNotFound(template)

def render_my_template(obj, detail=None, _root=None, mimetype=NotGiven, **context):
	"""\
		Renders an object's template with the given context.

		:param obj: the Pybble object that should be displayed.
		:param detail: Which aspect to show.
		               Defaults to `TM_DETAIL_PAGE`.
		:param mimetype: The MIME type of the data we want to emit.
		                 Defaults to being derived from `detail`.
		:param context: the variables that will be available in the
		                context of the template.
		"""

	if isinstance(obj,basestring):
		obj = Object.by_oid(obj)
	if detail is None:
		detail = TM_DETAIL_PAGE
	if detail == TM_DETAIL_PAGE:
		request.user.will_read(obj)
	else:
		request.user.will_list(obj)

	if mimetype is NotGiven:
		mimetype = TM_MIME(detail)

	if detail == TM_DETAIL_PAGE or detail == TM_DETAIL_SUBPAGE or detail == TM_DETAIL_DETAIL:
		request.user.visits(obj) # save a breadcrumb

	context["obj"] = obj

	c = ContentData(obj=obj,from_mime=obj.mimetype, to_mime=TM_MIME(detail), anchor=_root)
	return c.render(**context)
	
class TaggedMarkup(Markup):
	success = None
	@property
	def text(self):
		return self

def get_context():
	user = getattr(request,"user",None)
	msgs = []
	for c,m in get_flashed_messages(with_categories=True):
		m = TaggedMarkup.escape(m)
		m.success = c
		msgs.append(m)

	return dict(
		# CURRENT_URL=request.build_absolute_uri(),
		USER=getattr(request,"user",None),
		MESSAGES=msgs,
		SITE=current_site,
		CRUMBS=(user.groups+list(p.obj for p in user.all_visited()[0:20])) if user else None,
		NOW=datetime.utcnow(),
	)

import smtplib
import email.Message

def send_mail(to='', template='', server=None, **context):
	if "site" not in context:
		context["site"] = current_site
	if "user" not in context:
		context["user"] = request.user
	rand = random_string(8)
	for x in range(3):
		context["id"+str(x)] = "%d.%s%d@%s" % (time(),random_string(10),x,current_site.domain)
	
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
			obj = Object.by_oid(field.data)
			u = getattr(request,"user",None)
			if not u:
				raise ValidationError(u"Kein Benutzer")
			if current_app.config.DEBUG_ACCESS:
				print("valid can_"+b+":", u,obj,a, file=sys.stderr)
			if (u.can_do(obj, objtyp=obj, want=a) < a) \
				if (a > PERM_NONE) \
				else (u.can_do(obj, objtyp=obj, want=a) != a):
				raise ValidationError(u"Kein Zugriff auf Objekt '%s' (%s)" % (field.data,b))

		def valid_do_self(form, field):
			obj = Object.by_oid(field.data)
			u = getattr(request,"user",None)
			if not u:
				raise ValidationError(u"Kein Benutzer")
			if current_app.config.DEBUG_ACCESS:
				print("valid can_self_"+b+":", u,obj,a, file=sys.stderr)
			if u == obj:
				return
			if (u.can_do(obj, objtyp=obj, want=a) < a) \
				if (a > PERM_NONE) \
				else (u.can_do(obj, objtyp=obj, want=a) != a):
				raise ValidationError(u"Kein Zugriff auf Objekt '%s' (%s)" % (field.data,b))

		return valid_do,valid_do_self
	e,f = can_do_closure(a,b)
	globals()['valid_' + b.lower()] = e
	globals()['valid_' + b.lower() + '_self'] = f

class Renderer(object):
	"""Base class for rendering"""
	def render(self,obj):
		raise NotImplementedError("You need to implement ‘{}.render()’".format(self.__class__.__name__))
