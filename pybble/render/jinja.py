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

from jinja2 import Markup, contextfunction, BaseLoader, is_undefined
from flask import request,current_app,g,get_flashed_messages,session,g,url_for
from flask.helpers import locked_cached_property
from flask.templating import Environment as BaseEnvironment
from flask._compat import text_type

from ..utils import AuthError
from ..core.models._const import PERM, PERM_NONE, PERM_ADD, \
                          TM_DETAIL_PAGE, TM_DETAIL_SUBPAGE, TM_DETAIL_STRING, TM_DETAIL, \
                          TM_DETAIL_DETAIL, TM_DETAIL_RSS, TM_DETAIL_EMAIL, TM_DETAIL_name
from ..core.models.objtyp import ObjType
from ..core.models.object import Object
from ..core.models.user import access_logger
from ..core.models.template import TemplateMatch, Template as DBTemplate
from ..core.models._const import PERM_name
from ..core.db import db,NoData, refresh
from ..utils.diff import textDiff,textOnlyDiff
from . import render_subpage,render_subline,render_subrss, ContentData
from .loader import get_template

from time import time

import logging
logger = logging.getLogger('pybble.render')

class Environment(BaseEnvironment):
	"""Set up our Jinja environment"""

	def __init__(self, app):
		super(Environment,self).__init__(app, loader=SiteTemplateLoader(app.site))
		self.globals.update(
			url_for=url_for,
			get_flashed_messages=get_flashed_messages,
			config=app.config,
			request=request,
			session=session,
			g=g,
		)
		# off since we'll do our own JSON handling
		#self.filters['tojson'] = json.tojson_filter
		# off since this needs to be app-context specific
		#self.globals['site'] = app.site

		## setup template loader
		app.jinja_loader = self.loader

		## TODO: do the same thing with static files

		def render(obj, *a,**kw):
			if hasattr(obj,"render"):
				return obj.render(*a,**kw)
			else:
				return Markup.escape(unicode(obj))
		self.filters['render'] = render

		def cdata(data): ## [[[[
			return Markup("<![CDATA[")+data.replace("]]>","]] >")+Markup("]]>")
		self.filters['cdata'] = cdata

		def datetimeformat(value, format='%Y-%m-%d %H:%M'):
			return value.strftime(format)
		self.filters['date'] = datetimeformat
		self.filters['datetime'] = datetimeformat

		def is_object(obj):
			return isinstance(obj,Object)

		self.tests['object'] = is_object

		self.globals['url'] = lambda: request.url

		def name_objtyp(id):
			if id is None or id == "-":
				return "*"
			try:
				id = int(id)
			except ValueError:
				return Object.by_oid(id).name
			else:
				return ObjType.q.get_by(id=id)
		self.globals['name_objtyp'] = name_objtyp

		def name_detail(id):
			from pybble.models import TM_DETAIL_name
			return TM_DETAIL_name(id)
		self.globals['name_detail'] = name_detail

		def name_permission(id):
			return PERM_name(id).lower()
		self.globals['name_permission'] = name_permission

		self.globals['diff'] = textDiff
		self.globals['textdiff'] = textOnlyDiff

		for typ in ObjType.q.all():
			dname = typ.name
			i = dname.rfind(".")
			if i > 0:
				dname = dname[i+1:]
			self.globals[str("d_"+dname.lower())] = typ.id

		for tm,name in TM_DETAIL.items():
			self.globals[str("tm_"+name.lower())] = tm

		def addables(obj):
			"""Cache a list of object types the user can add to this object"""
			u = request.user
			if not hasattr(u,"_can_add"):
				u._can_add = {}
			u = u._can_add

			g = u.get(obj.id,None)
			if g is None:
				g = []
				for d in ObjType.q.all():
#			if getattr(obj_class(d.id),"_no_crumbs",False):
#				continue
					if request.user.can_add(obj, objtyp=obj.type, new_objtyp=d):
						g.append((d.id, d.name, d.doc))
				u[obj.id] = g
			return g
		self.globals['addables'] = addables

		self.globals['subpage'] = render_subpage
		self.globals['subline'] = render_subline
		self.globals['subrss'] = render_subrss

		# Permission checks for templates: {% if can_edit() %} -- menu -- {% endif %}
		for a,b in PERM.iteritems():
			def can_do_closure(a,b):
				def can_do(env, obj=None, objtyp=None):
					if objtyp is None:
						if isinstance(obj,(int,long)):
							objtyp=obj
							obj=None
					if obj is None:
						obj = env.get('obj',None)
					if isinstance(obj,basestring):
						obj = Object.by_oid(obj)
					u = getattr(request,"user",None)
					if current_app.config.DEBUG_ACCESS:
						access_logger.debug("can_do_{}: {} {} {} {}".format(b, u,obj,objtyp,a))
					if not u or is_undefined(obj):
						return False
					if a > PERM_NONE:
						return u.can_do(obj, objtyp=objtyp) >= a
					elif a == PERM_ADD:
						return u.can_do(obj, objtyp=obj, new_objtyp=objtyp, want=a) == a
					else:
						return u.can_do(obj, objtyp=objtyp, want=a) == a
				can_do.contextfunction = 1 # Jinja

				def will_do(env, obj=None):
					if obj is None:
						obj = env.vars['obj']
					if isinstance(obj,basestring):
						obj = Object.by_oid(obj)
					u = getattr(request,"user",None)
					if current_app.config.DEBUG_ACCESS:
						access_logger.debug("will_do_{} {} {} {}".format(b, u,obj,a))
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
			self.globals['can_' + b.lower()] = c
			self.globals['will_' + b.lower()] = d

	def select_jinja_autoescape(self, filename):
		"""\
			Returns `True` if autoescaping should be active for the given template name.
			We simply assume it is.
			"""
		return True

class SiteTemplateLoader(BaseLoader):
	"""\
		This loader is used for loading named Jinja includes.
		"""
	def __init__(self, site):
		self.site = site

	def get_source(self, environment, template):
		"""\
			Find a template.

			* attached to "self"
			* if this is a site:
			  * if the template name contains a slash,
			    * attached to the SiteBlueprint
			    * attached to the Blueprint
			  * attached to the app
			* recurse to my parent
			"""

		if isinstance(template,TemplateMatch):
			template = template.template
		if isinstance(template,DBTemplate):
			mtime = template.modified
			def t_is_current():
					#db.refresh(refresh(t),('modified',))
					return mtime == refresh(template).modified
			return template

		c = ContentData(site=refresh(self.site), name=text_type(template), from_mime=None,to_mime=None)
		if current_app.debug:
			trace = []
			def tracer(*t):
				trace.append(t)
			t = get_template(c, tracer)
			#g.context.setdefault('LOADER_TRACE',[]).append((c,trace))
		else:
			t = get_template(c)
		mtime = t.modified
		def t_is_current():
			#db.refresh(refresh(t),('modified',))
			return mtime == refresh(t).modified
		return t.content, t.oid, t_is_current

