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

## jinja extensions
try:
	from flask import request,current_app
	from .. import Renderer as BaseRenderer
	from markdown import Markdown
	from .md_quotes import makeExtension as md_quotes
	from jinja2 import contextfunction

	marker = Markdown(
    	extensions = ['wikilinks','headerid',md_quotes()], 
    	extension_configs = {'wikilinks': [
	                                      ('base_url', '/wiki/'), 
	                                      ('end_url', ''), 
	                                      ('html_class', 'wiki') ],
		                     'headerid': [('level',1), ('forceid',False)],
										  },
    	safe_mode = False
	)

	@contextfunction
	def convert(ctx,s,extern=False):
		b = ""
		if extern:
			b = "http://"+current_app.site.domain
		b += "/wiki/"
		obj = ctx.get("obj",None)
		if obj and isinstance(obj,WikiPage):
			if not obj.mainpage and isinstance(obj.parent,WikiPage):
				b += obj.parent.name+"/"
			elif isinstance(obj,WikiPage):
				b += obj.name+"/"
		marker.inlinePatterns["wikilink"].config["base_url"][0] = b
		return Markup(marker.convert(s))

	def setup_app(app):
		app.jinja_env.filters['markdown'] = convert

except TypeError: # old markdown
	from markdown import markdown
	def setup_app(app):
		app.jinja_env.filters['markdown'] = lambda a,b=None: Markup(markdown(a))

class Renderer(BaseRenderer):
	def render(self,obj):
		return Markup(marker.convert(obj.data))

