# -*- coding: utf-8 -*-

from werkzeug import redirect
from werkzeug.exceptions import NotFound
from pybble.utils import render_template, expose, \
     url_for, send_mail, current_request, make_permanent
from pybble.models import Template, obj_get
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

class NamedTemplateForm(Form):
	name = TextField('Name', [validators.length(min=3, max=30)])
	page = TextAreaField('Template')

class TemplateForm(Form):
	page = TextAreaField('Template')
	inherit = SelectField('Applies to?', choices={'Yes':'All sub-pages', 'No':'this page only','*':'This page and all sub-pages'})

@expose("/admin/template")
def show_templates(request):
	t = Template.q.filter(and_(Template.superparent == request.site, Template.name != None)).order_by(Template.name)
	return render_template('templates.html', templates=t, title_trace=["Templates"])
	
@expose("/admin/template/<template>")
def edit_template(request, template=None):
	template = obj_get(template)
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
				flash("Du hast eine neue Template '%s' angelegt." % (form.name.data,))
			template.name = form.name.data
			template.data = form.page.data
			template.modified = datetime.utcnow()
			flash("Template '%s' gespeichert." % (form.name.data,), True)
			return redirect(url_for("pybble.admin.show_templates"))

	
	elif request.method == 'GET':
		form.name.data = template.name
		form.page.data = template.data
	return render_template('template.html', templ=template, form=form, error=error, title_trace=[template.name])

