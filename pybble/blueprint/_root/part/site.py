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

from flask import request, url_for, flash, render_template
from werkzeug import redirect
from werkzeug.exceptions import NotFound
from wtforms import Form, BooleanField, TextField, TextAreaField, \
	SelectField, PasswordField, HiddenField, validators
from wtforms.validators import ValidationError

from pybble.render import render_my_template
from pybble.core.db import db,NoData
from pybble.core.models import TM_DETAIL_PAGE
from pybble.core.models.site import Site
from pybble.core.session import logged_in
from ..views import view_oid
from .._base import expose
expose = expose.sub("part.site")

from datetime import datetime

###
### Site page editor
###

def free_name(form, field):
	filter = [ Site.name == field.data ]
	try: id = form.id
	except AttributeError: pass
	else:
		if id is not None:
			filter.append(Site.id != id)

	try:
		obj = Site.q.get(*filter)
	except NoData:
		pass
	else:
		raise ValidationError(u"Seiten namens '%s' gibt es hier bereits!" % (field.data,))

def free_domain(form, field):
	filter = [ Site.domain == field.data ]
	try: id = form.id
	except AttributeError: pass
	else:
		if id is not None:
			filter.append(Site.id != id)

	try:
		obj = Site.q.get(*filter)
	except NoData:
		pass
	else:
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

