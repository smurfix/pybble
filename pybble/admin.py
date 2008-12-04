# -*- coding: utf-8 -*-

from werkzeug import redirect
from werkzeug.exceptions import NotFound
from pybble.utils import send_mail, current_request, make_permanent
from pybble.render import url_for, expose, render_template
from pybble.models import Template, TemplateMatch, Discriminator, \
	Permission, obj_get, TM_DETAIL, PERM, TM_DETAIL_PAGE

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

@expose("/admin/del/template/<template>/<id>/<obj>")
def del_template_at(request, template, id, obj=None):
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


tmc = TM_DETAIL.items()
tmc.sort()
try:
	dsc = list(Discriminator.q.all())
except Exception:
	dsc = [] # if not set up yet
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
			match.discr = int(form.discr.data)
			match.detail = int(form.detail.data)
			match.inherit = inherit
			match.template = template
			match.obj = obj
		else:
			try:
				match = TemplateMatch.q.get_by(discr = int(form.discr.data), detail=int(form.detail.data), obj=obj, inherit=inherit)
			except NoResult:
				match = TemplateMatch(obj,int(form.discr.data),int(form.detail.data),template)
				match.inherit = inherit
				db.session.add(match)
			else:
				match.discr = int(form.discr.data)
				match.detail = int(form.detail.data)
				match.inherit = inherit
				match.template = template

		flash(u"Gespeichert.",True)

		if match.inherit is None:
			m = TemplateMatch.q.filter(TemplateMatch.inherit != None)
		else:
			m = TemplateMatch.q.filter(TemplateMatch.inherit == None)
		m = m.filter_by(discr=match.discr, detail=match.detail, obj=obj)
		if match.inherit is None:
			if m.count():
				flash(u"Vorherige Assoziation(en) entfernt.")
			for mm in m:
				db.session.delete(mm)
		else:
			m.inherit = not match.inherit
			flash(u"Bestehende Assoziation eingeschränkt.")

		return redirect(url_for("pybble.admin.edit_template", template=obj.oid()))

	
	elif request.method == 'GET':
		form.page.data = template.data
		if obj:
			form.oid.data = obj.oid()
			form.discr.data = str(obj.discriminator)
		form.detail.data = str(TM_DETAIL_PAGE)
		if match:
			form.discr.data = str(match.discr)
			form.detail.data = str(match.detail)
			form.inherit.data = "*" if match.inherit is None else "Yes" if match.inherit else "No"
		else:
			form.inherit.data = "*"

	return render_template('itemplate.html', obj=obj, templ=template, form=form, error=error, title_trace=[template.name])


@expose("/admin/perm/<permission>")
def edit_permission(request, permission=None):
	p = obj_get(permission)
	if isinstance(p,Permission):
		return edit_single_permission(request,p)
	else:
		# show list of templates for that object
		return render_template('permissionlist.html', obj=p, title_trace=["Permissions"])

plc = PERM.items()
plc.sort()

class PermissionForm(Form):
	user = TextField('User', [valid_obj])
	object = TextField('Object', [valid_obj])

	discr = SelectField('Object type?', choices=tuple((str(q.id),q.name) for q in dsc))
	inherit = SelectField('Applies to?', choices=(('Yes','All sub-pages'), ('No','this page only'),('*','This page and all sub-pages')))
	right = SelectField('Access to:', choices=tuple((str(x),y) for x,y in plc))
	clone = SelectField('Copy?', choices=(('Yes','Store new permission'),('No','Modify existing permission')))


def edit_single_permission(request, perm):
	form = PermissionForm(request.form, prefix="perm")
	error = ""
	if request.method == 'POST' and form.validate():
		user = obj_get(form.user.data)
		obj = obj_get(form.object.data)
		discr = int(form.discr.data)
		right = int(form.right.data)

		if form.inherit.data == "Yes": inherit = True
		elif form.inherit.data == "No": inherit = False
		elif form.inherit.data == "*": inherit = None
		else: assert False

		if form.clone.data == "Yes":
			perm = Permission(user, obj, discr, right, inherit)
			db.session.add(perm)
		else:
			perm.owner = user
			perm.parent = obj
			perm.discr = discr
			perm.right = right
			perm.inherit = inherit

		flash(u"Gespeichert.",True)

		if perm.inherit is None:
			m = Permission.q.filter(TemplateMatch.inherit != None)
		else:
			m = Permission.q.filter(TemplateMatch.inherit == None)
		m = m.filter_by(discr=discr, parent=obj, owner=user)
		if perm.inherit is None:
			if m.count():
				flash(u"Vorherige Berechtigung(en) entfernt.")
			# m.delete()
			m.parent=None ## TODO: recycle
		else:
			m.inherit = not perm.inherit
			flash(u"Bestehende Berechtigung eingeschränkt.")

		return redirect(url_for("pybble.admin.edit_permission", permission=obj.oid()))

	
	elif request.method == 'GET':
		form.object.data = perm.parent.oid()
		form.user.data = perm.owner.oid()
		form.discr.data = str(perm.discr)
		form.inherit.data = "*" if perm.inherit is None else "Yes" if perm.inherit else "No"
		form.right.data = str(perm.right)
		form.clone.data = "Yes"

	return render_template('iperm.html', obj=perm.parent, user=perm.owner, form=form, error=error, title_trace=["Edit permission"])


