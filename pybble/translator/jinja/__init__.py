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

from flask import Markup
from jinja2 import contextfunction

from pybble.translator import BaseTranslator
from pybble.render.jinja import Environment

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
		res = self.template.render(**vars)
		if c.to_mime.typ == "html" or c.to_mime.subtyp == "html":
			res = Markup(res)
		return res

	@staticmethod
	def init_app(app, global_only=False):
		env = getattr(app,'jinja_env',None)
		if env is None:
			env = Environment(app)
			app.jinja_env = env
		if global_only:
			return env
		return Environment(app)

