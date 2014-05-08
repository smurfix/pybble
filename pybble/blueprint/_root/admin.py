# -*- coding: utf-8 -*-
##BP

from flask import current_app
from pybble.render import render_template
from pybble.core.models import obj_get
from pybble.core.models.template import Template
from pybble.core.db import db
from ._base import expose

###
### Template editor
###

@expose("/admin/template")
@expose("/admin/template/<oid>")
def list_templates(oid=None):
	"""List all named templates"""
	obj = obj_get(oid) if oid else current_app.site
	s = obj
	t = []
	while s:
		t.extend(Template.q.filter_by(superparent_id == s).order_by(Template.name))
		s = s.parent
	return render_template('templates.html', templates=t, obj=obj, title_trace=["Templates",current_app.site.name])
	
@expose("/admin/template_for/<oid>")
def show_templates(oid):
	"""show list of templates for that object"""
	obj = obj_get(oid)
	return render_template('templatelist.html', obj=obj, title_trace=["Template list",obj.oid()])
	
