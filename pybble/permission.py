# -*- coding: utf-8 -*-

from werkzeug import redirect
from werkzeug.exceptions import NotFound
from pybble.utils import send_mail, current_request, make_permanent
from pybble.render import url_for, expose, render_template, valid_obj, \
	discr_list
from pybble.models import Template, TemplateMatch, Discriminator, \
	Permission, obj_get, TM_DETAIL, PERM, TM_DETAIL_PAGE, PERM_READ

from pybble.database import db,NoResult
from pybble.flashing import flash
from pybble.session import logged_in
from wtforms import Form, BooleanField, TextField, TextAreaField, \
	SelectField, PasswordField, HiddenField, validators
from wtforms.validators import ValidationError
from sqlalchemy.sql import and_, or_, not_
from datetime import datetime


@expose("/admin/perm/<permission>")
def edit_permission(request, permission=None):
	p = obj_get(permission)
	if isinstance(p,Permission):
		return editor(request,p)
	else:
		# show list of templates for that object
		return render_template('permissionlist.html', obj=p, title_trace=["Permissions"])

plc = PERM.items()
plc.sort()

class PermissionForm(Form):
	user = TextField('User', [valid_obj])
	object = TextField('Object', [valid_obj])

	discr = SelectField('Existing Object type?', choices=tuple((str(q.id),q.name) for q in discr_list))
	new_discr = SelectField('New Object type?', choices=(("-","(not applicable)"),)+tuple((str(q.id),q.name) for q in discr_list))
	inherit = SelectField('Applies to?', choices=(('Yes','All sub-pages'), ('No','this page only'),('*','This page and all sub-pages')))
	right = SelectField('Access to:', choices=tuple((str(x),y) for x,y in plc))
	clone = SelectField('Copy?', choices=(('Yes','Store new permission'),('No','Modify existing permission')))

def newer(request, parent, name=None):
	return editor(request, parent=parent)

def editor(request, obj=None, parent=None):
	form = PermissionForm(request.form, prefix="perm")
	if parent:
		del form.clone
	if request.method == 'POST' and form.validate():
		user = obj_get(form.user.data)
		obj = obj_get(form.object.data)
		discr = int(form.discr.data)
		print repr(form.new_discr.data)
		new_discr = int(form.new_discr.data) if form.new_discr.data != "-" else None
		right = int(form.right.data)

		if form.inherit.data == "Yes": inherit = True
		elif form.inherit.data == "No": inherit = False
		elif form.inherit.data == "*": inherit = None
		else: assert False

		if parent or form.clone.data == "Yes":
			obj = Permission(user, obj, discr, right, inherit)
			db.session.add(obj)
			db.session.flush()
		else:
			obj.owner = user
			obj.parent = obj
			obj.discr = discr
			obj.right = right
			obj.inherit = inherit
		obj.new_discr = new_discr

		flash(u"Gespeichert.",True)

		if obj.inherit is None:
			m = Permission.q.filter(TemplateMatch.inherit != None)
		else:
			m = Permission.q.filter(TemplateMatch.inherit == None)
		m = m.filter_by(discr=discr, parent=obj, owner=user)
		if obj.inherit is None:
			if m.count():
				flash(u"Vorherige Berechtigung(en) entfernt.")
				for mm in m:
					db.session.delete(mm)
		else:
			if m.count():
				flash(u"Vorherige Berechtigung(en) entfernt.")
				for mm in m:
					mm.inherit = not obj.inherit

		return redirect(url_for("pybble.permission.edit_permission", permission=obj.oid()))

	
	elif request.method == 'GET':
		if not parent:
			form.clone.data = "Yes"
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
			form.right.data = PERM_READ
			form.discr.data = str(parent.discriminator)
			form.new_discr.data = "-"
			form.inherit.data = "*"

	return render_template('edit/permission.html', parent=parent, form=form, title_trace=["New permission" if parent else "Edit permission"])


