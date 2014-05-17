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

from flask import request, flash,url_for, render_template
from werkzeug import redirect
from werkzeug.exceptions import NotFound
from wtforms import Form, BooleanField, TextField, TextAreaField, \
	SelectField, PasswordField, HiddenField, validators
from wtforms.validators import ValidationError

from pybble.render import valid_obj, \
	valid_admin,valid_access,valid_read
from pybble.core.models import obj_get, TM_DETAIL, PERM, TM_DETAIL_PAGE, PERM_NONE
from pybble.core.models.user import Permission
from pybble.core.models.template import Template, TemplateMatch
from pybble.core.db import db,NoData
from pybble.core.models._descr import D
from pybble.core.session import logged_in
from .._base import expose
expose = expose.sub("part.permission")

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
			m = Permission.q.filter(*m)
			if m.count():
				flash(u"Vorherige Berechtigung(en) entfernt.")
				for mm in m:
					Delete(mm)
		else:
			m.append(Permission.inherit == None)
			m = Permission.q.filter(*m)
			if m.count():
				flash(u"Bestehende Berechtigung eingeschränkt.")
				for mm in m:
					mm.inherit = not obj.inherit
					Change(mm,data=dict(inherit=[None,mm.inherit]))

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
	
