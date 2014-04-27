# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, division, unicode_literals
##
## This is part of Pybble, a WMS (Whatever Management System) based on
## Jinja2/Haml, Werkzeug, Flask, and Optimism.
##
## Pybble is Copyright © 2009-2014 by Matthias Urlichs <matthias@urlichs.de>,
## it is licensed under the GPLv3. See the file `README.md` for details
## as well as hopeful statements by the author.
##
## This paragraph is auto-generated and may self-destruct at any time.
## Please do not remove the next line, or insert any blank lines before it.
##BP

import markdown
from markdown.preprocessors import Preprocessor
import re

class BQproc(Preprocessor):
	blockquote_re = re.compile(r'^(>\s?)*')

	def run (self, lines):
		res = []
		depth = -1
		for l in lines:
			if l == "":
				depth = -1
				res.append("")
			else:
				m = self.blockquote_re.search(l)
				assert m
				c = l[m.start():m.end()].count(">")
				if c != depth:
					if depth != -1:
						res.append("")
					depth = c
				res.append("> "*c + l[m.end():])
		return res

class BQExtension(markdown.Extension):
	""" Extension to separate differently-indented blockquotes. """

	def __init__ (self, configs):
		""" Setup configs. """
#        self.config = {'PLACE_MARKER':
#                       ["///Footnotes Go Here///",
#                        "The text string that marks where the footnotes go"]}
#
#        for key, value in configs:
#            self.config[key][0] = value
			

	def extendMarkdown(self, md, md_globals):
		""" Add pieces to Markdown. """
		md.registerExtension(self)
		self.parser = md.parser
		# Insert a preprocessor before ReferencePreprocessor
		md.preprocessors.add("blockquote-sep", BQproc(self),
							"<reference")
	def reset(self):
		pass

def makeExtension(configs=[]):
	""" Return an instance of the FootnoteExtension """
	return BQExtension(configs=configs)

