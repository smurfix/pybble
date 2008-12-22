# -*- coding: utf-8 -*-

from werkzeug import redirect
from werkzeug.exceptions import NotFound
from pybble.utils import current_request, make_permanent
from pybble.render import url_for, expose, render_template, valid_obj, \
	discr_list
from pybble.models import Template, TemplateMatch, Discriminator, \
	Permission, obj_get, TM_DETAIL, PERM, TM_DETAIL_PAGE

from pybble.database import db,NoResult
from pybble.flashing import flash
from pybble.session import logged_in
from wtforms import Form, BooleanField, TextField, TextAreaField, \
	SelectField, PasswordField, HiddenField, validators
from sqlalchemy.sql import and_, or_, not_
from datetime import datetime

###
### Template editor
###

@expose("/admin/template")
def show_templates(request):
	"""List all named templates, allow editing"""
	t = Template.q.filter(and_(Template.superparent == request.site, Template.name != None)).order_by(Template.name)
	return render_template('templates.html', templates=t, title_trace=["Templates"])
	
@expose("/admin/template/<template>")
def edit_template(request, template=None):
	t = obj_get(template)
	if not isinstance(t,Template):
		# show list of templates for that object
		return render_template('templatelist.html', obj=t, title_trace=["Template list"])

	elif t.name is None:
		# edit unnamed template
		return edit_assoc_template(request,None,t,None)

	else:
		return edit_named_template(request,t)
	
@expose("/admin/template/<template>/<id>")
@expose("/admin/template/<template>/<id>/<obj>")
def edit_template_at(request, template, id, obj=None):
	t = obj_get(template)
	tm = TemplateMatch.q.get_by(id=id)
	assert tm.template == t
	if obj is None: obj = tm.obj
	else: obj = obj_get(obj)
	return edit_assoc_template(request,tm,t,obj)

class NamedTemplateForm(Form):
	name = TextField('Name', [validators.length(min=3, max=30)])
	page = TextAreaField('Template')

def edit_named_template(request, template):
	form = NamedTemplateForm(request.form, prefix="template")
	error = ""
	if request.method == 'POST' and form.validate():
		try:
			Template.q.filter(Template.id != template.id).get_by(name=form.name.data, superparent=request.site)
		except NoResult:
			pass
		else:
			error = "Diesen Template-Namen gibt es bereits!"

		if not error:
			if template.name != form.name.data:
				flash(u"Du hast eine neue Template '%s' angelegt." % (form.name.data,))
			template.name = form.name.data
			template.data = form.page.data
			template.modified = datetime.utcnow()
			flash(u"Template '%s' gespeichert." % (form.name.data,), True)
			return redirect(url_for("pybble.admin.show_templates"))

	
	elif request.method == 'GET':
		form.name.data = template.name
		form.page.data = template.data
	return render_template('template.html', templ=template, form=form, error=error, title_trace=[template.name])


