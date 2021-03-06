# -*- coding: utf-8 -*-

from werkzeug import redirect
from werkzeug.exceptions import NotFound
from pybble.utils import current_request, make_permanent
from pybble.render import url_for, expose, render_template, valid_obj, \
	objtyp_list
from pybble.core.models.template import Template, TemplateMatch
from pybble.core.models.objtyp import ObjType
from pybble.core.models.object import Object

from pybble.database import db,NoResult
from pybble.flashing import flash
from pybble.session import logged_in
from wtforms import Form, BooleanField, TextField, TextAreaField, \
	SelectField, PasswordField, HiddenField, validators
from datetime import datetime
from storm.locals import And

###
### Template editor
###

def known_name(form, field):
	site = Object.by_oid(form.site.data)
	m = [ Template.parent_id == site.id, Template.name == field.data ]

	id = getattr(form,"id",None)
	if id:
		m.append(Template.id != id)

	if db.store.find(Template,And(*m)).count():
		raise ValidationError("Diese Vorlage existiert bereits.")

class NamedTemplateForm(Form):
	site = TextField('Site', [valid_obj])
	name = TextField('Name', [validators.required(u"Der Name fehlt."), validators.length(min=3, max=30), known_name])
	page = TextAreaField('Template')

def editor(request, obj, parent=None):
	form = NamedTemplateForm(request.form, prefix="template")
	form.id = obj.id
	if request.method == 'POST' and form.validate():
		if parent:
			obj = Template.new(form.name.data, form.page.data.replace("\r",""), parent=Object.by_oid(form.site.data))
			obj.name = form.name.data
		else:
			obj.record_change()
			obj.parent = Object.by_oid(form.site.data)
			obj.name = form.name.data
			obj.data = form.page.data.replace("\r","")
		flash(u"Template '%s' gespeichert." % (form.name.data,), True)
		return redirect(url_for("pybble.admin.list_templates", oid=obj.parent.oid))
	
	elif request.method == 'GET':
		form.site.data = parent.oid if parent else obj.parent.oid
		form.name.data = obj.name if obj else ""
		form.page.data = obj.data if obj else ""
	return render_template('edit/template.html', obj=obj, form=form, parent=parent, title_trace=[obj.name,"Template-Editor"])


def newer(request, parent):
	return editor(request, parent=parent)


