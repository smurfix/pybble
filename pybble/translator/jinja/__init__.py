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

"""
This module contains the filter which translates from HAML to HTML templates.
"""

import sys

from jinja2 import Markup, contextfunction
from flask import request,current_app
from flask.helpers import locked_cached_property

from flask.templating import Environment as BaseEnvironment

from pybble.translator import BaseTranslator
from pybble.utils import AuthError
from pybble.core.models import PERM, PERM_NONE, PERM_ADD, obj_get, \
	Discriminator, TM_DETAIL_PAGE, TM_DETAIL_SUBPAGE, TM_DETAIL_STRING, obj_class, obj_get, TM_DETAIL, \
		TM_DETAIL_DETAIL, TM_DETAIL_RSS, TM_DETAIL_EMAIL, TM_DETAIL_name
from pybble.core.models._descr import D
from pybble.core.models.user import access_logger
from pybble.core.db import db,NoData
from pybble.utils.diff import textDiff,textOnlyDiff
from pybble.render import render_subpage,render_subline,render_subrss
from pybble.render.loader import SiteTemplateLoader

import logging
logger = logging.getLogger('pybble.translator.jinja')

from jinja2 import __version__ as jinja_version
_version = 1
_version = '|'.join(str(x) for x in ('j2',jinja_version,_version,sys.version_info[0],sys.version_info[1]))
_not_cached = "not compiled"

class Translator(BaseTranslator):
	FROM_MIME=("pybble/*","json/*")
	TO_MIME=("text/html","html/*")
	WEIGHT = 10
	CONTENT="template/jinja"
	
	@property
	def bytecode(self):
		"""\
			Return the template's (possibly-cached) bytecode
			"""
		dbt = self.db_template
		c = dbt.get_cache(_version)
		if c is None:
			c = self.env.compile(dbt.content, dbt.source, dbt.oid())
			dbt.set_cache(c, _version)
		return c

	@property
	def template(self):
		return self.env.template_class.from_code(self.env, self.bytecode, self.env.globals, None)
	
	def render(self,c,globals=None, *a,**k):
		vars = dict(*a, **k)
		ctx = self.new_context(vars)
		return self.template.render(**vars)

	@staticmethod
	def init_app(app, global_only=False):
		env = getattr(app,'jinja_env',None)
		if env is None:
			env = Environment(app)
			app.jinja_env = env
		if global_only:
			return env
		return Environment(app)

class Environment(BaseEnvironment):
	"""Set up the Jinja environment"""

	def __init__(self, app):
		super(Environment,self).__init__(app, loader=SiteTemplateLoader(app.site))

		self.globals['site'] = app.site

		## setup template loader
		app.jinja_loader = self.loader = SiteTemplateLoader(app.site)

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

		self.globals['url'] = lambda: request.url

		def name_discr(id):
			if id is None or id == "None":
				return "*"
			return Discriminator.q.get_by(id=int(id)).name
		self.globals['name_discr'] = name_discr

		def name_detail(id):
			from pybble.models import TM_DETAIL_name
			return TM_DETAIL_name(id)
		self.globals['name_detail'] = name_detail

		def name_permission(id):
			from pybble.models import PERM_name
			return PERM_name(id).lower()
		self.globals['name_permission'] = name_permission

		self.globals['diff'] = textDiff
		self.globals['textdiff'] = textOnlyDiff

		for did,dname in D.items():
			i = dname.rindex(".")
			if i > 0:
				dname = dname[i+1:]
			self.globals[str("d_"+dname.lower())] = did

		for tm,name in TM_DETAIL.items():
			self.globals[str("tm_"+name.lower())] = tm

		def addables(obj):
			u = request.user
			if not hasattr(u,"_can_add"):
				u._can_add = {}
			u = u._can_add

			g = u.get(obj.id,None)
			if g is None:
				g = []
				for d in Discriminator.q.all():
#			if getattr(obj_class(d.id),"_no_crumbs",False):
#				continue
					if request.user.can_add(obj, discr=obj.discriminator, new_discr=d.id):
						g.append((d.id,d.display_name or d.name, d.infotext))
				u[obj.id] = g
			return g
		self.globals['addables'] = addables

		self.globals['subpage'] = render_subpage
		self.globals['subline'] = render_subline
		self.globals['subrss'] = render_subrss

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
						access_logger.debug("can_do_{}: {} {} {} {}".format(b, u,obj,discr,a))
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

