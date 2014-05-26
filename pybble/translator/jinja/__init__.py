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
from pybble.core.models._const import PERM, PERM_NONE, PERM_ADD, \
	TM_DETAIL_PAGE, TM_DETAIL_SUBPAGE, TM_DETAIL_STRING, TM_DETAIL, \
		TM_DETAIL_DETAIL, TM_DETAIL_RSS, TM_DETAIL_EMAIL, TM_DETAIL_name
from pybble.core.models.user import access_logger
from pybble.core.models.objtyp import ObjType
from pybble.core.db import db,NoData
from pybble.utils.diff import textDiff,textOnlyDiff
from pybble.render import render_subpage,render_subline,render_subrss
from pybble.render.jinja import SiteTemplateLoader,Environment

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
			c = self.env.compile(dbt.content, dbt.source, dbt.oid)
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

