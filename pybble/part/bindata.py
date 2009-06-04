# -*- coding: utf-8 -*-

from werkzeug import redirect
from werkzeug.exceptions import NotFound
from pybble.utils import current_request, make_permanent
from pybble.render import url_for, render_template, expose, render_my_template
from pybble.models import WikiPage, Site, Comment, TM_DETAIL_PAGE, BinData, MIMEtype, \
	find_mimetype
from pybble.views import view_oid

from pybble.database import db,NoResult
from pybble.flashing import flash
from pybble.session import logged_in
from wtforms import Form, BooleanField, TextField, TextAreaField, \
	SelectField, PasswordField, HiddenField, validators
from wtforms.validators import ValidationError
from sqlalchemy.sql import and_, or_, not_
from datetime import datetime
import sys

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
			mt = find_mimetype(f.content_type)
		except NoResult:
			raise ValidationError("Unknown MIME type: %s" % (f.content_type,))
		else:
			if str(mt.id) != field.data:
				raise ValidationError("Wrong MIME type: %s vs. %s" % \
					(MIMEtype.q.get_by(int(field.data)).mimetype, mt.mimetype))
			form.mimetype = mt
				
	
class FileForm(Form):
	name = TextField('Name', [validators.length(min=3, max=30)])
	mime = SelectField('MIME Type', [check_type], choices=[(str(x.id),x.name) for x in MIMEtype.q.all()])

def newer(request, parent, name=None):
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
		obj = BinData(parent=parent, name=form.name.data, content=data, mimetype=form.mimetype)
		obj.record_creation()
		obj.save()
		flash(u"Daten '%s' gespeichert." % (obj.name), True)
		return redirect(url_for("pybble.views.view_oid", oid=obj.oid()))

	elif request.method == 'GET':
		pass

	return render_template('edit/bindata.html', parent=parent, form=form, name=form.name.data, title_trace=["Datei-Upload"])

	
def editor(request, obj=None):
	form = FileForm(request.form, prefix="bindata")
	form.obj = obj
	if request.method == 'POST' and form.validate():
		if obj.data != form.page.data:
			obj.record_change(comment=form.name.data)

			flash(u"Datei-Info '%s' geändert." % (obj.name), True)
		else:
			flash(u"Datei-Info '%s' unverändert." % (obj.name))

		return redirect(url_for("pybble.views.view_oid", oid=obj.oid()))

	elif request.method == 'GET':
		form.name.data = obj.name if obj else name
		form.mime.daat = obj.mime_id
	return render_template('edit/bindata.html', obj=obj, form=form, name=form.name.data, title_trace=["Datei-Info editieren"])


