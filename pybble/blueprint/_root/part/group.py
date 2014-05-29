# -*- coding: utf-8 -*-

from werkzeug import redirect
from werkzeug.exceptions import NotFound
from pybble.utils import current_request, make_permanent
from pybble.render import url_for, expose, render_template, valid_obj, \
	objtyp_list, valid_admin,valid_access,valid_read,valid_write
from pybble.core.models.template import Template, TemplateMatch
from pybble.core.models.user import Group
from pybble.core.models.site import Site
from pybble.core.models.object import Object

from pybble.database import db,NoResult
from pybble.flashing import flash
from pybble.session import logged_in
from wtforms import Form, BooleanField, TextField, TextAreaField, \
	SelectField, PasswordField, HiddenField, validators
from wtforms.validators import ValidationError
from datetime import datetime

class GroupForm(Form):
	name = TextField('Name', [validators.required(u"Die Gruppe braucht einen Namen."), validators.length(min=3, max=30)])

def newer(request, parent, name=None):
	return editor(request, parent=parent)

def editor(request, obj=None, parent=None):
	form = GroupForm(request.form, prefix="perm")
	if request.method == 'POST' and form.validate():
		name = form.name.data

		if parent is None:
			obj = Group.new(name=name, parent=parent)
		else:
			data = obj.data
			obj.name = name
			obj.record_change(data)

		flash(u"Gespeichert.",True)
		return redirect(url_for("pybble.views.view_oid", oid=obj.oid))
	
	elif request.method == 'GET':
		if obj:
			form.name.data = obj.name
		else:
			form.name.data = ""

	return render_template('edit/group.html', parent=parent, obj=obj, form=form, title_trace=["New Group" if parent else "Edit Group"])

editor.no_check_perm = True

def may_delete(obj):
	current_request.user.will_admin(obj.owner)
	
