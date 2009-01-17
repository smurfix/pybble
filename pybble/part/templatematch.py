# -*- coding: utf-8 -*-

from werkzeug import redirect
from werkzeug.exceptions import NotFound
from pybble.utils import current_request, make_permanent
from pybble.render import url_for, expose, render_template, valid_obj, \
	discr_list
from pybble.models import Template, TemplateMatch, Discriminator, \
	Permission, obj_get, TM_DETAIL, PERM, TM_DETAIL_PAGE

from pybble.database import db,NoResult
from pybble.flashing import flash
from pybble.session import logged_in
from wtforms import Form, BooleanField, TextField, TextAreaField, \
	SelectField, PasswordField, HiddenField
from wtforms.validators import ValidationError
from sqlalchemy.sql import and_, or_, not_
from datetime import datetime

###
### Template editor
###


tmc = TM_DETAIL.items()
tmc.sort()

def known_match(form, field):
	if form.inherit.data == "Yes": inherit = True
	elif form.inherit.data == "No": inherit = False
	elif form.inherit.data == "*": inherit = None
	else: assert False

	dest = obj_get(form.oid.data)

	m = TemplateMatch.q.filter(TemplateMatch.inherit == inherit)
	id = getattr(form,"id",None)
	if id:
		m = m.filter(TemplateMatch.id != id)
	m = m.filter_by(discr=int(form.discr.data), detail=int(form.detail.data), obj=dest)

	if m.count():
		raise ValidationError("Diese Vorlage existiert dort bereits.")

class TemplateMatchForm(Form):
	oid = TextField('OID', [valid_obj])
	detail = SelectField('Detail', choices=tuple((str(x),y) for x,y in tmc))
	discr = SelectField('Object type', choices=tuple((str(q.id),q.name) for q in discr_list))
	inherit = SelectField('Applies to', choices=(('Yes','All sub-pages'), ('No','this page only'),('*','This page and all sub-pages')), validators=[known_match])
	page = TextAreaField('Template')

def newer(request, parent=None):
	return editor(request, parent=None)

def editor(request, obj=None, parent=None):
	form = TemplateMatchForm(request.form, prefix="template")
	if not parent:
		form.id = obj.id
	if request.method == 'POST' and form.validate():
		if form.inherit.data == "Yes": inherit = True
		elif form.inherit.data == "No": inherit = False
		elif form.inherit.data == "*": inherit = None
		else: assert False

		dest = obj_get(form.oid.data)

		if parent:
			obj = TemplateMatch(parent,int(form.discr.data),int(form.detail.data),form.page.data.replace("\r",""))
			obj.record_creation()
			db.session.flush()
		else:
			obj.record_change()
			obj.data = form.page.data.replace("\r","")

		obj.discr = int(form.discr.data)
		obj.detail = int(form.detail.data)
		obj.inherit = inherit
		db.session.flush()

		flash(u"Gespeichert.",True)

		# Now filter other templates to look for overlaps
		if obj.inherit is None:
			m = TemplateMatch.q.filter(TemplateMatch.inherit != None)
		else:
			m = TemplateMatch.q.filter(TemplateMatch.inherit == None)
		m = m.filter_by(discr=obj.discr, detail=obj.detail, obj=obj)
		if obj.inherit is None:
			if m.count():
				flash(u"Vorherige Assoziation(en) entfernt.")
				for mm in m:
					db.session.delete(mm)
		else:
			if m.count():
				flash(u"Bestehende Assoziation eingeschränkt.")
				for mm in m:
					mm.inherit = not obj.inherit

		return redirect(url_for("pybble.views.view_oid", oid=dest.oid()))

	
	elif request.method == 'GET':
		if obj:
			form.page.data = obj.data
			form.discr.data = str(obj.discr)
			form.detail.data = str(obj.detail)
			form.inherit.data = "*" if obj.inherit is None else "Yes" if obj.inherit else "No"
		else:
			form.detail.data = str(TM_DETAIL_PAGE)
			form.discr.data = str(parent.discriminator)
			form.inherit.data = "*"
		if parent:
			form.oid.data = parent.oid()
		else:
			form.oid.data = obj.parent.oid()

	return render_template('edit/templatematch.html', obj=obj, parent=parent, form=form, title_trace=["Template-Editor"])


