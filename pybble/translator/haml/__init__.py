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

from hamlish_jinja import HamlishExtension

from pybble.translator import BaseTranslator
from ..jinja import Translator as JinjaTranslator

class AlwaysHamlishExtension(HamlishExtension):
	def preprocess(self, source, name, filename=None):
		"""\
			Don't regard filename extensions. We have none, here.
			"""
		h = self.get_preprocessor(self.environment.hamlish_mode)
		try:
			return h.convert_source(source)
		except TemplateIndentationError as e:
			raise TemplateSyntaxError(e.message, e.lineno, name=name, filename=filename)
		except TemplateSyntaxError as e:
			raise TemplateSyntaxError(e.message, e.lineno, name=name, filename=filename)

class Translator(JinjaTranslator):
	CONTENT="template/haml"

	@classmethod
	def init_app(cls,app):
		# This sets up the Jinja environment. In fact we need two: one for
		# our own toplevel templates, and one for templates that are loaded
		# by way of Jinja's template inheritance model.

		# first, install the preprocessor in Jinja's system
		env = super(Translator,cls).init_app(app, global_only=True)
		env.extensions["jinja2.ext.HamlishExtension"] = HamlishExtension(env)
		env.hamlish_file_extensions=('.haml',)
		env.hamlish_mode='debug'
		env.hamlish_enable_div_shortcut=True

		# second, use our own
		env = super(Translator,cls).init_app(app, global_only=False)
		# this ignores the global Jinja env because we already set that up
		# so we get a local one back, which is usable for HAML-only

		env.extensions["jinja2.ext.HamlishExtension"] = AlwaysHamlishExtension(env)
		env.hamlish_mode='debug'
		env.hamlish_enable_div_shortcut=True

		return env

