# -*- coding: utf-8 -*-

from werkzeug import redirect
from werkzeug.exceptions import NotFound
from pybble.utils import render_template, expose, \
     url_for, send_mail, current_request, make_permanent
from pybble.models import Template, TemplateMatch, Discriminator, obj_get, \
	TM_DETAIL, PERM

from pybble.database import db,NoResult
from pybble.flashing import flash
from pybble.session import logged_in
from wtforms import Form, BooleanField, TextField, TextAreaField, \
	SelectField, PasswordField, HiddenField, validators
from wtforms.validators import ValidationError
from sqlalchemy.sql import and_, or_, not_
from datetime import datetime


def valid_obj(form, field):
	try:
		obj_get(field.data)
	except Exception:
		raise ValidationError(u"Das Objekt '%s' gibt es nicht" % (field.data,))

###
### Template editor
###

@expose("/admin/template")
def show_templates(request):
	t = Template.q.filter(and_(Template.superparent == request.site, Template.name != None)).order_by(Template.name)
	return render_template('templates.html', templates=t, title_trace=["Templates"])
	
@expose("/admin/template/for/<oid>")
def edit_template_for(request, oid=None):
	obj = obj_get(oid)

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
def edit_template_at(request, template, id):
	t = obj_get(template)
	tm = TemplateMatch.q.get_by(id=id)
	assert tm.template == t
	return edit_assoc_template(request,tm,t,tm.obj)

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


tmc = TM_DETAIL.items()
tmc.sort()
dsc = list(Discriminator.q.all())
dsc.sort(cmp=lambda a,b: cmp(a.name,b.name))

class TemplateForm(Form):
	oid = TextField('OID', [valid_obj])
	detail = SelectField('Detail?', choices=tuple((str(x),y) for x,y in tmc))
	discr = SelectField('Object type?', choices=tuple((str(q.id),q.name) for q in dsc))
	inherit = SelectField('Applies to?', choices=(('Yes','All sub-pages'), ('No','this page only'),('*','This page and all sub-pages')))
	page = TextAreaField('Template')
	clone = SelectField('Copy?', choices=(('Yes','Store new template'),('Link','Add new assoc'),('No','Replace old assoc')))

def edit_assoc_template(request, match, template, obj):
	form = TemplateForm(request.form, prefix="template")
	error = ""
	if request.method == 'POST' and form.validate():
		if form.clone.data == "Yes":
			template = Template(None, form.page.data)
			db.session.add(template)
		elif template.data != form.page.data:
			template.data = form.page.data
			template.modified = datetime.utcnow()

		if form.inherit.data == "Yes": inherit = True
		elif form.inherit.data == "No": inherit = False
		elif form.inherit.data == "*": inherit = None
		else: assert False

		obj = obj_get(form.oid.data)

		if match and form.clone.data == "No":
			match.discriminator = int(form.discr.data)
			match.type = int(form.detail.data)
			match.inherit = inherit
			match.template = template
			match.obj = obj
		else:
			try:
				match = TemplateMatch.q.get_by(discriminator = int(form.discr.data), type=int(form.detail.data), obj=obj, inherit=inherit)
			except NoResult:
				match = TemplateMatch(obj,int(form.discr.data),int(form.detail.data),template)
				match.inherit = inherit
				db.session.add(match)
			else:
				match.discriminator = int(form.discr.data)
				match.type = int(form.detail.data)
				match.inherit = inherit
				match.template = template

		flash("Gespeichert.",True)

		if match.inherit is None:
			m = TemplateMatch.q.filter(TemplateMatch.inherit != None)
		else:
			m = TemplateMatch.q.filter(TemplateMatch.inherit == None)
		m = m.filter_by(discriminator=match.discriminator, type=match.type, obj=obj)
		if match.inherit is None:
			if length(m):
				flash("Vorherige Assoziation(en) entfernt.")
			m.delete()
		else:
			m.inherit = not match.inherit
			flash("Bestehende Assoziation eingeschränkt.")

		return redirect(url_for("pybble.admin.edit_template", template=obj.oid()))

	
	elif request.method == 'GET':
		form.page.data = template.data
		if obj:
			form.oid.data = obj.oid()
		if match:
			form.discr.data = str(match.discriminator)
			form.detail.data = str(match.type)
			form.inherit.data = "*" if match.inherit is None else "Yes" if match.inherit else "No"
	return render_template('itemplate.html', obj=obj, templ=template, form=form, error=error, title_trace=[template.name])


#plc = PERM.items()
#plc.sort()
#
#
#class PermissionForm(Form):
#	user = TextField('User', [valid_obj])
#	object = TextField('Object', [valid_obj])
#
#	discr = SelectField('Object type?', choices=[ (str(q.id),q.name) for q in Discriminator.q.all() ])
#	inherit = SelectField('Applies to?', choices=(('Yes','All sub-pages'), ('No','this page only'),('*','This page and all sub-pages')))
#	right = SelectField('Access to:', choices=((str(x),y) for x,y in plc))
#	clone = SelectField('Copy?', choices=(('Yes','Store new permission'),('No','Modify existing permission')))
#
#def edit_permision(request, match, template, obj):
#	form = TemplateForm(request.form, prefix="template")
#	error = ""
#	if request.method == 'POST' and form.validate():
#		if form.clone.data == "Yes":
#			template = Template(None, form.page.data)
#			db.session.add(template)
#		elif template.data != form.page.data:
#			template.data = form.page.data
#			template.modified = datetime.utcnow()
#
#		if form.inherit.data == "Yes": inherit = True
#		elif form.inherit.data == "No": inherit = False
#		elif form.inherit.data == "*": inherit = None
#		else: assert False
#
#		obj = obj_get(form.oid.data)
#
#		if match and form.clone.data == "No":
#			match.discriminator = int(form.discr.data)
#			match.type = int(form.detail.data)
#			match.inherit = inherit
#			match.template = template
#			match.obj = obj
#		else:
#			try:
#				match = TemplateMatch.q.get_by(discriminator = int(form.discr.data), type=int(form.detail.data), obj=obj, inherit=inherit)
#			except NoResult:
#				match = TemplateMatch(obj,int(form.discr.data),int(form.detail.data),template)
#				match.inherit = inherit
#				db.session.add(match)
#			else:
#				match.discriminator = int(form.discr.data)
#				match.type = int(form.detail.data)
#				match.inherit = inherit
#				match.template = template
#
#		flash("Gespeichert.",True)
#
#		if match.inherit is None:
#			m = TemplateMatch.q.filter(TemplateMatch.inherit != None)
#		else:
#			m = TemplateMatch.q.filter(TemplateMatch.inherit == None)
#		m = m.filter_by(discriminator=match.discriminator, type=match.type, obj=obj)
#		if match.inherit is None:
#			if m.count():
#				flash("Vorherige Assoziation(en) entfernt.")
#			m.delete()
#		else:
#			m.inherit = not match.inherit
#			flash("Bestehende Assoziation eingeschränkt.")
#
#		return redirect(url_for("pybble.admin.edit_template", template=obj.oid()))
#
#	
#	elif request.method == 'GET':
#		form.page.data = template.data
#		if obj:
#			form.oid.data = obj.oid()
#		if match:
#			form.discr.data = str(match.discriminator)
#			form.detail.data = str(match.type)
#			form.inherit.data = "*" if match.inherit is None else "Yes" if match.inherit else "No"
#	return render_template('itemplate.html', obj=obj, templ=template, form=form, error=error, title_trace=[template.name])
#
#
