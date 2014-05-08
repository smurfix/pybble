# -*- coding: utf-8 -*-
##BP

from flask import request, flash,url_for
from werkzeug import redirect
from werkzeug.exceptions import NotFound
from wtforms import Form, BooleanField, TextField, TextAreaField, \
	SelectField, PasswordField, HiddenField, validators
from wtforms.validators import ValidationError

from pybble.utils import make_permanent
from pybble.render import render_template, valid_obj, \
	valid_admin,valid_access,valid_read
from pybble.core.models import obj_get, TM_DETAIL, PERM, TM_DETAIL_PAGE, PERM_NONE
from pybble.core.models.user import Permission
from pybble.core.models.template import Template, TemplateMatch
from pybble.core.db import db,NoData
from pybble.core.models._descr import D
from pybble.core.session import logged_in
from .._base import expose

from datetime import datetime

@expose("/admin/perm/<permission>")
def show_permission(permission=None):
	p = obj_get(permission)
	return render_template('permissionlist.html', obj=p, title_trace=["Permissions"])

plc = PERM.items()
plc.sort()

class PermissionForm(Form):
	user = TextField('User', [valid_obj,valid_admin])
	object = TextField('Object', [valid_obj,valid_read])

	discr = SelectField('Existing Object type') ###TODO, choices=tuple((str(q.id),q.name) for q in D))
	new_discr = SelectField('New Object type') ###TODO, choices=(("-","(not applicable)"),)+tuple((str(q.id),q.name) for q in D))
	inherit = SelectField('Applies to', choices=(('Yes','All sub-pages'), ('No','this page only'),('*','This page and all sub-pages')))
	right = SelectField('Access to', choices=tuple((str(x),y) for x,y in plc),validators=[valid_access('object')])

def newer(parent, name=None):
	return editor(parent=parent)

def editor(obj=None, parent=None):
	form = PermissionForm(request.form, prefix="perm")
	if request.method == 'POST' and form.validate():
		user = obj_get(form.user.data)
		dest = obj_get(form.object.data)
		discr = int(form.discr.data)
		new_discr = int(form.new_discr.data) if form.new_discr.data != "-" else None
		right = int(form.right.data)

		if form.inherit.data == "Yes": inherit = True
		elif form.inherit.data == "No": inherit = False
		elif form.inherit.data == "*": inherit = None
		else: assert False

		if parent:
			obj = Permission(user, dest, discr, right, inherit)
			obj.record_creation()
		else:
			obj.owner = user
			obj.parent = dest
			obj.discr = discr
			obj.right = right
			obj.inherit = inherit
		obj.new_discr = new_discr

		flash(u"Gespeichert.",True)

		m = [ Permission.discr == discr, Permission.parent_id == obj.id, Permission.owner_id == user.id ]
		if obj.inherit is None:
			m.append(Permission.inherit != None)
		else:
			m.append(Permission.inherit == None)
		m = db.store.find(Permission,And(*m))
		if obj.inherit is None:
			if m.count():
				flash(u"Vorherige Berechtigung(en) entfernt.")
				for mm in m:
					db.store.remove(mm)
		else:
			if m.count():
				flash(u"Bestehende Berechtigung eingeschränkt.")
				for mm in m:
					mm.inherit = not obj.inherit

		return redirect(url_for("pybble.views.view_oid", oid=dest.oid()))

	
	elif request.method == 'GET':
		if obj:
			form.object.data = parent.oid() if parent else obj.parent.oid()
			form.user.data = obj.owner.oid()
			form.discr.data = str(obj.discr)
			form.new_discr.data = str(obj.new_discr) if obj.new_discr else "-"
			form.inherit.data = "*" if obj.inherit is None else "Yes" if obj.inherit else "No"
			form.right.data = str(obj.right)
		else:
			form.object.data = parent.oid()
			form.user.data = request.user.oid()
			form.right.data = str(PERM_NONE)
			form.discr.data = str(parent.discriminator)
			form.new_discr.data = "-"
			form.inherit.data = "*"

	return render_template('edit/permission.html', parent=parent, obj=obj, form=form, title_trace=["New permission" if parent else "Edit permission"])

editor.no_check_perm = True

def may_delete(obj):
	request.user.will_admin(obj.owner)
	