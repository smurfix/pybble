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

import os
import sys
import logging

from flask import request
from flask.config import Config
from flask._compat import text_type

from jinja2 import Template,BaseLoader, TemplateNotFound

from ..core.db import db, NoData, refresh
from ..core.models.template import Template as DBTemplate, TemplateMatch
from ..core.models.site import Site,SiteBlueprint,Blueprint
from . import ContentData

logger = logging.getLogger('pybble.render.loader')

def get_template(c, trace=None):
	"""\
		This code's purpose is to find a template which matches the given
		requirements which is "close" to wherever the current object is.
		I.e. the template might be attached to the object, or its parent
		(and so on).

		:param:`c`: a ContentData instance.
		:param:`trace`: If given, called with (template,weight,docstr) for every candidate template.

		So we're looking for a templatematch which points to a template
		(or, if we have a template name, use that directly)
		which points to a mimeadapter which knows about our from_mime and
		to_mime and which points us to the mimetranslator which actually
		interprets the template. If that is an eyeful, well, it is.
		
		The templatematches have a weight attached. So do the intermediate
		objects. In addition, indirection steps increase weight. This way,
		you can tune the whole thing to pick the right template for you by
		default even if your site is a bit nonstandard. Or you can add
		a lot of templatematches.

		If you set "trace" to something callable, you get all possible
		matches, i.e. the function gets called with (templatematch,owner,weight).

		The best matching Template object, i.e. that with the lowest
		weight, gets returned.

		This code auto-lookups wildcard records and penalizes them by +100.

		TODO: Cache all of this. Heavily.
		"""
	q = gen_q(c)
	site = c.anchor
	seen = set()

	res = None
	res_weight = None
	def got(t,weight, doc=None):
		weight += t.weight
		a = t.adapter
		weight += a.weight
		tr = a.translator
		weight += tr.weight

		if trace: trace(t,weight, doc)
		if res is None or res_weight > weight:
			res = t
			res_weight = weight
		
	weight = 0
	while site is not None:
		if site in seen:
			break
		seen.add(site)

		if site is c.site:
			get_site_template(c,weight,trace)
			if c.blueprint:
				get_one_site(c,c.blueprint.blueprint,55+weight,got,q)
				get_one_site(c,c.blueprint,got,53+weight,got,q)
		for t in q.filter(TemplateMatch.parent==site):
			got(t.template,weight+t.weight)

			break
		if site.parent in seen:
			site = site.superparent or site.parent.superparent
			weight += 10
		else:
			site = site.parent
			weight += 1

	if not res:
		raise TemplateNotFound(c)
	return res

def get_site_template(c,weight,got):
	bn = None
	sn = None
	if c.name:
		i = c.name.index('/')
		if i > 0:
			bn = c.name[:i]
			sn = c.name[i+1:]
		else:
			sn = c.name
			weight += 30

	if bn:
		try: # the name might refer to a SiteBlueprint
			sbp = SiteBlueprint.q.get_by(parent=c.site,name=bn)
		except NoData: # or to the Blueprint it points to
			try: bp = db.query(SiteBlueprint).filter(SiteBlueprint.parent==c.site).join(Blueprint, SiteBlueprint.superparent).filter(Blueprint.name==bn).limit(1).one().blueprint
			except NoData: bp = None
		else:
			# we get here if the prefix refers to a SiteBlueprint entity
			try: t = DBTemplate.q.get_by(parent=sbp, name=sn)
			except NoData: pass
			else: got(t,0+weight)
			bp = sbp.blueprint

		if bp is not None:
			try: t = DBTemplate.q.get_by(parent=bp, name=sn)
			except NoData: pass
			else: got(t,0+weight)

		if c.site.name == bn:
			try: t = DBTemplate.q.get_by(parent=site.app, name=sn)
			except NoData: pass
			else: got(t,5+weight)

		if c.site.app.name == bn:
			try: t = DBTemplate.q.get_by(parent=site.app, name=sn)
			except NoData: pass
			else: got(t,10+weight)

	if c.name:
		try: t = DBTemplate.q.get_by(parent=site.app, name=c.name)
		except NoData: pass
		else: got(t,10)

def gen_q(c):
	from_wild = None
	if from_mime.subtyp != "*":
		try: from_wild = MIMEtype.get(from_mime.typ+'/*')
		except NoData: pass
	if from_wild is None:
		from_mime = MIMEtranslator.from_mime == from_mime
	else:
		from_mime = or_(MIMEtranslator.from_mime == from_mime, MIMEtranslator.from_mime == from_wild)

	to_wild = None
	if to_mime.subtyp != "*":
		try: to_wild = MIMEtype.get(to_mime.typ+'/*')
		except NoData: pass
	if to_wild is None:
		to_mime = MIMEtranslator.to_mime == to_mime
	else:
		to_mime = or_(MIMEtranslator.to_mime == to_mime, MIMEtranslator.to_mime == to_wild)
	
	if c.name:
		if c.blueprint: ## actually the SiteBlueprint, hence the chain
			names = (c.name,c.blueprint.name,c.blueprint.blueprint.name)
		else:
			names = (c.name,)
	else:
		names = ()
	nf = tuple((Template.name == n) for n in names)
	
	q = TemplateMatch.q.join(Template, TemplateMatch.template).filter(*names).join(MIMEadapter,Template.adapter).filter(from_mime,to_mime).join(MIMEtranslator,MIMEadapter.translator).filter_by(mime=Template.mime)
	q._from_wild=from_wild
	q._to_wild=to_wild
	q._names = names
	return q

def get_one_site(c,site, weight,got, q):

	while site is not None:
		if site in seen:
			break
		seen.add(site)
		for t in build_q(site):
			m = t.template.translator
			w = m.weight+m.adapter.weight+t.weight
			if m.from_mime is from_wild: w += 100
			if m.to_mime is to_wild: w += 100
			if w_min is None or w_min > w:
				w_min = w
				res = t
			if trace:
				trace(t,site,w)

		if not site.parent:
			break
		if res is not None and isinstance(site,Site):
			break
		if site.parent in seen:
			site = site.superparent or site.parent.superparent
		else:
			site = site.parent
	return res

class SiteTemplateLoader(BaseLoader):
	"""\
		This loader is used for legacy Jinja templates.
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

		c = ContentData(site=refresh(self.site), name=template)
		if current_app.debug:
			trace = []
			def tracer(*t):
				trace.append(t)
			t = get_template(c, tracer)
			g.context.setdefault('LOADER_TRACE',[]).append((c,trace))
		else:
			t = get_template(c)
		mtime = t.modified
		def t_is_current():
			#db.refresh(refresh(t),('modified',))
			return mtime == refresh(t).modified
		return t.data, t.oid(), t_is_current

