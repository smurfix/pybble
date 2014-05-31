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
from pybble.core.models.object import Object
from pybble.core.models.objtyp import ObjType
from pybble.core.models._const import PERM, PERM_NONE
from pybble.core.models.permit import Permission
from pybble.core.models.types import MIMEtype
from pybble.core.models.template import Template, TemplateMatch
from pybble.core.db import db,NoData
from pybble.core.session import logged_in
from .._base import expose
expose = expose.sub("part.permission")

from datetime import datetime

@expose("/admin/perm/<permission>")
def show_permission(permission=None):
	p = Object.by_oid(permission)
	return render_template('permissionlist.html', obj=p, title_trace=["Permissions"])

plc = PERM.items()
plc.sort()

class PermissionForm(Form):
	user = TextField('User', [valid_obj,valid_admin])
	target = TextField('Object', [valid_obj,valid_read])

	for_objtyp = SelectField('Existing Object type')
	new_objtyp = SelectField('New Object type')
	new_mimetyp = SelectField('New MIME type')
	inherit = SelectField('Applies to', choices=(('Yes','All sub-pages'), ('No','this page only'),('*','This page and all sub-pages')))
	right = SelectField('Access to', choices=tuple((str(x),y) for x,y in plc),validators=[valid_access('object')])

def newer(parent, name=None):
	return editor(parent=parent)

def editor(obj=None, parent=None):
	form = PermissionForm(request.form, prefix="perm")
	form.for_objtyp.choices = tuple((str(x.id),x.name) for x in ObjType.q.all())
	form.new_objtyp.choices = (('-','–'),) + form.for_objtyp.choices
	form.new_mimetyp.choices = (('-','–'),) + tuple((str(x.id),x.name) for x in MIMEtype.q.all())
	if request.method == 'POST' and form.validate():
		user = Object.by_oid(form.user.data)
		dest = Object.by_oid(form.target.data)
		for_objtyp = int(form.for_objtyp.data)
		new_objtyp = ObjType.q.get_by(id=form.new_objtyp.data) if form.new_objtyp.data != "-" else None
		new_mimetyp = MIMEtype.id.get_by(form.new_mimetyp.data) if form.new_mimetyp.data != "-" else None
		right = int(form.right.data)

		if form.inherit.data == "Yes": inherit = True
		elif form.inherit.data == "No": inherit = False
		elif form.inherit.data == "*": inherit = None
		else: assert False

		if parent:
			obj = Permission.new(user, dest, for_objtyp,new_objtyp=new_objtyp,new_mimetyp=new_mimetyp, right=right, inherit=inherit)
		else:
			obj.owner = user
			obj.parent = dest
			obj.for_objtyp = for_objtyp
			obj.right = right
			obj.inherit = inherit
			obj.new_objtyp = new_objtyp
			obj.new_mimetyp = new_mimetyp

		flash(u"Gespeichert.",True)

		return redirect(url_for("pybble.views.view_oid", oid=dest.oid))

	
	elif request.method == 'GET':
		if obj:
			form.target.data = parent.oid if parent else obj.parent.oid
			form.user.data = obj.owner.oid
			form.for_objtyp.data = str(obj.for_objtyp.id)
			form.new_objtyp.data = str(obj.new_objtyp.id) if obj.new_objtyp else "-"
			form.new_mimetyp.data = str(obj.new_mimetyp.id) if obj.new_mimetyp else "-"
			form.inherit.data = "*" if obj.inherit is None else "Yes" if obj.inherit else "No"
			form.right.data = str(obj.right)
		else:
			form.target.data = parent.oid
			form.user.data = request.user.oid
			form.right.data = str(PERM_NONE)
			form.for_objtyp.data = str(parent.type.id)
			form.new_objtyp.data = "-"
			form.new_mimetyp.data = "-"
			form.inherit.data = "*"

	return render_template('edit/permission.html', parent=parent, obj=obj, form=form, title_trace=["New permission" if parent else "Edit permission"])

editor.no_check_perm = True

def may_delete(obj):
	request.user.will_admin(obj.owner)
	
