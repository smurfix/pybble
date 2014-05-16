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

from hamlish_jinja import Hamlish

from pybble.translator import BaseTranslator
from ..jinja import Translator as JinjaTranslator

class Translator(JinjaTranslator):
	FROM_MIME=("pybble/*","json/*")
	TO_MIME=("text/html","html/*")
	WEIGHT = 10
	CONTENT="template/haml"

	def __call__(self, obj,template, from_mine,to_mime, **params):
		placeholders = {
			'block_start_string': self.environment.block_start_string,
			'block_end_string': self.environment.block_end_string,
			'variable_start_string': self.environment.variable_start_string,
			'variable_end_string': self.environment.variable_end_string,
		}

		if mode == 'compact':
			output = Output(
				indent_string='',
				newline_string='',
				**placeholders)
		elif mode == 'debug':
			output = Output(
				indent_string='   ',
				newline_string='\n',
				debug=True,
				**placeholders)
		else:
			output = Output(
				indent_string=self.environment.hamlish_indent_string,
				newline_string=self.environment.hamlish_newline_string,
				debug=self.environment.hamlish_debug,
				**placeholders)

		return Hamlish(output, self.environment.hamlish_enable_div_shortcut)

