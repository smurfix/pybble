# -*- coding: utf-8 -*-
##BP

from flask import request, url_for, flash
from werkzeug import redirect
from werkzeug.exceptions import NotFound
from wtforms import Form, BooleanField, TextField, TextAreaField, \
	SelectField, PasswordField, HiddenField, validators
from wtforms.validators import ValidationError

from pybble.utils import make_permanent
from pybble.render import render_template, render_my_template
from pybble.core.db import db,NoData
from pybble.core.models import TM_DETAIL_PAGE
from pybble.core.models.site import Site
from pybble.core.session import logged_in
from ..views import view_oid
from .._base import expose

from datetime import datetime


###
### Site page editor
###

def free_name(form, field):
	filter = [ Site.name == field.data ]
	try: id = form.id
	except AttributeError: pass
	else: filter.append(Site.id != id)

	obj = db.store.find(Site,*filter).one()
	if obj:
		raise ValidationError(u"Seiten namens '%s' gibt es hier bereits!" % (field.data,))

def free_domain(form, field):
	filter = [ Site.domain == field.data ]
	try: id = form.id
	except AttributeError: pass
	else: filter.append(Site.id != id)

	obj = db.store.find(Site,*filter).one()
	if obj:
		raise ValidationError(u"Seiten in der Domain '%s' gibt es hier bereits!" % (field.data,))


class SiteEditForm(Form):
	name = TextField('Name', [validators.required(u"Das Kind braucht einen Namen."), validators.length(min=3, max=30), free_name])
	domain = TextField('Domain', [validators.required(u"Ohne Domain habe ich ein Problem, das Kind wiederzufinden."), validators.length(min=3, max=100), free_domain])

def editor(obj, name=None, parent=None):
	assert parent is None

	form = SiteEditForm(request.form, prefix="site")
	form.id = obj.id
	if request.method == 'POST' and form.validate():
		if obj.name != form.name.data or obj.domain != form.domain.data:
			obj.record_change()
			obj.name = form.name.data
			obj.domain = form.domain.data
		return redirect(url_for("pybble.views.view_oid", oid=obj.oid()))
	
	elif request.method == 'GET':
		form.name.data = obj.name
		form.domain.data = obj.domain
	return render_template('edit/site.html', obj=obj, form=form, name=form.name.data, title_trace=["globale Einstellungen"])

def newer(parent, name=None):
	form = SiteEditForm(request.form, prefix="site")
	if request.method == 'POST' and form.validate():
		obj = Site(form.domain.data, form.name.data)
		obj.parent = parent
		obj.record_creation()
		return redirect(url_for("pybble.views.view_oid", oid=obj.oid()))
	
	return render_template('edit/site.html', obj=None, form=form, title_trace=["neue Website"])


@expose("/")
def viewer(**args):
	return render_my_template(obj=request.site, detail=TM_DETAIL_PAGE, **args)


