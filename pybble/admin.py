# -*- coding: utf-8 -*-

from pybble.render import expose, render_template
from pybble.models import Template, obj_get

###
### Template editor
###

@expose("/admin/template")
@expose("/admin/template/<oid>")
def list_templates(request,oid=None):
	"""List all named templates"""
	obj = obj_get(oid) if oid else request.site
	s = obj
	t = []
	while s:
		t.extend(Template.q.filter(Template.superparent == s).order_by(Template.name).all())
		s = s.parent
	return render_template('templates.html', templates=t, obj=obj, title_trace=["Templates",request.site.name])
	
@expose("/admin/template_for/<oid>")
def show_templates(request, oid):
	"""show list of templates for that object"""
	obj = obj_get(oid)
	return render_template('templatelist.html', obj=obj, title_trace=["Template list",obj.oid()])
	
