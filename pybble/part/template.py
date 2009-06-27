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

def known_name(form, field):
	site = obj_get(form.site.data)
	m = db.filter_by(Template, parent=site, name=field.data)

	id = getattr(form,"id",None)
	if id:
		m = m.filter(Template.id != id)

	if m.count():
		raise ValidationError("Diese Vorlage existiert bereits.")

class NamedTemplateForm(Form):
	site = TextField('Site', [valid_obj])
	name = TextField('Name', [validators.length(min=3, max=30), known_name])
	page = TextAreaField('Template')

def editor(request, obj, parent=None):
	form = NamedTemplateForm(request.form, prefix="template")
	form.id = obj.id
	if request.method == 'POST' and form.validate():
		if parent:
			obj = Template(form.name.data, form.page.data.replace("\r",""), parent=obj_get(form.site.data))
			obj.record_creation()
			obj.name = form.name.data
		else:
			obj.record_change()
			obj.parent = obj_get(form.site.data)
			obj.name = form.name.data
			obj.data = form.page.data.replace("\r","")
		flash(u"Template '%s' gespeichert." % (form.name.data,), True)
		return redirect(url_for("pybble.admin.list_templates", oid=obj.parent.oid()))
	
	elif request.method == 'GET':
		form.site.data = parent.oid() if parent else obj.parent.oid()
		form.name.data = obj.name if obj else ""
		form.page.data = obj.data if obj else ""
	return render_template('edit/template.html', obj=obj, form=form, parent=parent, title_trace=[obj.name,"Template-Editor"])


def newer(request, parent):
	return editor(request, parent=parent)


