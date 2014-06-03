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

from flask import request

from pybble.core.models.object import Object
from pybble.core.models.template import Template
from pybble.core.db import db
from pybble.globals import current_site
from ._base import expose
from pybble.render import render_template

expose = expose.sub("admin")

###
### Template editor
###

@expose("/admin/template")
@expose("/admin/template/<oid>")
def list_templates(oid=None):
	"""List all named templates"""
	obj = Object.by_oid(oid) if oid else current_site
	s = obj
	t = []
	while s:
		t.extend(Template.q.filter_by(target=s).order_by(Template.name))
		s = s.parent
	return render_template('templates.html', templates=t, obj=obj, title_trace=["Templates",current_site.name])
	
@expose("/admin/template_for/<oid>")
def show_templates(oid):
	"""show list of templates for that object"""
	obj = Object.by_oid(oid)
	return render_template('templatelist.html', obj=obj, title_trace=["Template list",obj.oid])
	
