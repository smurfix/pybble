# -*- coding: utf-8 -*-

from datetime import datetime
import sys

from flask import request, flash, url_for
from werkzeug import redirect
from werkzeug.exceptions import NotFound

from pybble.core.models import MIMEtype
from pybble.core.models.files import BinData
from pybble.core.db import db,NoData
from pybble.core.session import logged_in
from pybble.render import render_template

from wtforms import Form, BooleanField, TextField, TextAreaField, \
	SelectField, PasswordField, HiddenField, validators
from wtforms.validators import ValidationError

###
### Comment editor
###

def check_type(form,field):
	try:
		f = form.bindata
	except AttributeError:
		pass
	else:
		try:
			mt = MIMEtype.get(f.content_type)
		except NoData:
			raise ValidationError("Unknown MIME type: %s" % (f.content_type,))
		else:
			if str(mt.id) != field.data:
				raise ValidationError("Wrong MIME type: %s vs. %s" % \
					(db.get_by(MIMEtype, int(field.data)).mimetype, mt.mimetype))
			form.mimetype = mt
				
	
class FileForm(Form):
	name = TextField('Name', [validators.required(u"Jede Datei braucht einen Namen!"), validators.length(min=3, max=30)])
	mime = SelectField('MIME Type', [check_type], choices=[(str(x.id),x.name) for x in MIMEtype.q.all()])

def newer(parent, name=None):
	if parent is None:
		parent = request.site

	form = FileForm(request.form, prefix="bindata")
	try:
		form.bindata = request.files['bindata']
	except (KeyError,AttributeError):
		pass
	if request.method == 'POST' and form.validate():
		f = request.files['bindata']
		data = f.read()
		obj = BinData.new(parent=parent, storage=parent.default_storage, name=form.name.data, content=data, mimetype=form.mimetype)
		flash(u"Daten '%s' gespeichert." % (obj.name), True)
		return redirect(url_for("pybble.views.view_oid", oid=obj.oid))

	elif request.method == 'GET':
		pass

	return render_template('edit/bindata.html', parent=parent, form=form, name=form.name.data, title_trace=["Datei-Upload"])

	
def editor(obj=None):
	form = FileForm(request.form, prefix="bindata")
	form.obj = obj
	if request.method == 'POST' and form.validate():
		if obj.data != form.page.data:
			obj.record_change(comment=form.name.data)

			flash(u"Datei-Info '%s' geändert." % (obj.name), True)
		else:
			flash(u"Datei-Info '%s' unverändert." % (obj.name))

		return redirect(url_for("pybble.views.view_oid", oid=obj.oid))

	elif request.method == 'GET':
		form.name.data = obj.name if obj else name
		form.mime.daat = obj.mime_id
	return render_template('edit/bindata.html', obj=obj, form=form, name=form.name.data, title_trace=["Datei-Info editieren"])


