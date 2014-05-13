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

logger = logging.getLogger('pybble.render.loader')

def get_template(template, site=None):
	if site is None:
		site = request.site

	if isinstance(template,TemplateMatch):
		template = template.template
	if isinstance(template,DBTemplate):
		mtime = template.modified
		def t_is_current():
			#db.refresh(refresh(t),('modified',))
			return mtime == refresh(template).modified
		return template.data, template, t_is_current

	name = text_type(template)
	i = name.find('/')

	seen = set()
	while site is not None:
		if site in seen:
			break
		seen.add(site)
		t = None
		try: t = DBTemplate.q.get_by(site=site,name=name)
		except NoData:
			if isinstance(site,Site):
				if i>0:
					try: # the name might refer to a SiteBlueprint
						sbp = SiteBlueprint.q.get_by(parent=site,name=name[:i])
					except NoData: # or to the Blueprint it points to
						try:
							bp = db.query(SiteBlueprint).filter(SiteBlueprint.parent==site).join(Blueprint, SiteBlueprint.superparent).filter(Blueprint.name==name[:i]).limit(1).one().blueprint
						except NoData:
							bp = None
					else:
						# we get here if the prefix refers to a SiteBlueprint entity
						try:
							t = DBTemplate.q.get_by(parent=sbp, name=name[i+1:])
						except NoData:
							# not found, so check the blueprint
							bp = sbp.blueprint
					if t is None and bp is not None:
						try: t = DBTemplate.q.get_by(parent=bp, name=name[i+1:])
						except NoData: pass

					if t is None and site.app.name == name[:i]:
						try: t = DBTemplate.q.get_by(parent=site.app, name=name[i+1:])
						except NoData: pass

				if t is None:
					try: t = DBTemplate.q.get_by(parent=site.app, name=name)
					except NoData: pass

				if t is None:
					try: t = DBTemplate.q.get_by(parent=site, name=name)
					except NoData: pass

		if t is not None:
			return t

		if not site.parent:
			break
		if site.parent in seen:
			site = site.superparent or site.parent.superparent
		else:
			site = site.parent

	raise TemplateNotFound(name)


class SiteTemplateLoader(BaseLoader):
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
		t = get_template(template, refresh(self.site))
		mtime = t.modified
		def t_is_current():
			#db.refresh(refresh(t),('modified',))
			return mtime == refresh(t).modified
		return t.data, t.oid(), t_is_current
