# -*- coding: utf-8 -*-

from werkzeug import redirect
from werkzeug.exceptions import NotFound
from pybble.utils import current_request, make_permanent
from pybble.render import url_for, expose, render_template, valid_obj, \
	objtyp_list, valid_admin,valid_access,valid_read,valid_write
from pybble.core.models.template import Template, TemplateMatch
from pybble.core.models.objtyp import ObjType
from pybble.core.models.user import Member
from pybble.core.models.object import Object

from pybble.database import db,NoResult
from pybble.flashing import flash
from pybble.session import logged_in
from wtforms import Form, BooleanField, TextField, TextAreaField, \
	SelectField, PasswordField, HiddenField, validators
from wtforms.validators import ValidationError
from datetime import datetime

class MemberForm(Form):
	user = TextField('User', [valid_obj,valid_write])
	group = TextField('Group', [valid_obj,valid_write])

	excluded = BooleanField(u'ausschließen')

def newer(request, parent, name=None):
	return editor(request, parent=parent)

def editor(request, obj=None, parent=None):
	form = MemberForm(request.form, prefix="perm")
	if request.method == 'POST' and form.validate():
		user = Object.by_oid(form.user.data)
		group = Object.by_oid(form.group.data)
		excluded = bool(form.excluded.data)

		if parent:
			obj = Member.new(user, group)
			obj.record_creation()
		else:
			data = obj.data
			obj.owner = user
			obj.parent = group
			obj.excluded = excluded
			obj.record_change(data)

		flash(u"Gespeichert.",True)

		return redirect(url_for("pybble.views.view_oid", oid=user.oid))

	
	elif request.method == 'GET':
		if obj:
			form.group.data = parent.oid if parent else obj.parent.oid
			form.user.data = obj.owner.oid
			form.excluded.data = obj.excluded
		else:
			form.user.data = request.user.oid
			form.group.data = parent.oid
			form.excluded.data = False

	return render_template('edit/member.html', parent=parent, obj=obj, form=form, title_trace=["New Member" if parent else "Edit Member"])

editor.no_check_perm = True

def may_delete(obj):
	current_request.user.will_admin(obj.owner)
	
