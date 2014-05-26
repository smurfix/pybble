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
from pybble.core.models._const import TM_DETAIL_PAGE
from pybble.core.models.object import Object
from pybble.core.models.site import Site
from pybble.core.session import logged_in
from pybble.globals import current_site
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
	app = SelectField('App')
	parent = SelectField('Parent')

def editor(obj, name=None, parent=None):
	assert parent is None
	from pybble.core.models.site import App

	import pdb;pdb.set_trace()
	form = SiteEditForm(request.form, obj, prefix="site", app=current_site.app.oid, parent=parent.oid if parent else current_site.oid)
	form.id = obj.id
	form.app.choices = tuple((o.oid,str(o)) for o in App.q.all())
	kids = set(obj.all_sites)
	form.parent.choices = tuple((o.oid,str(o)) for o in Site.q.all() if o not in kids)
	if request.method == 'POST' and form.validate():
		obj.name = form.name.data
		obj.domain = form.domain.data
		obj.app = Object.by_oid(form.app.data)
		obj.parent = Object.by_oid(form.parent.data)
		return redirect(url_for("pybble.views.view_oid", oid=obj.oid))
	
	elif request.method == 'GET':
		form.name.data = obj.name
		form.domain.data = obj.domain
		form.app.data = obj.app.oid
		form.parent.data = obj.parent.oid
	return render_template('edit/site.html', obj=obj, form=form, name=form.name.data, title_trace=["globale Einstellungen"])

def newer(parent, name=None):
	from pybble.core.models.site import App
	form = SiteEditForm(request.form, prefix="site", app=current_site.app.oid, parent=parent.oid if parent else current_site.oid)
	form.app.choices = tuple((o.oid,str(o)) for o in App.q.all())
	form.parent.choices = tuple((o.oid,str(o)) for o in Site.q.all())
	if request.method == 'POST' and form.validate():
		obj = Site.new(form.domain.data, form.name.data, parent=Object.by_oid(form.parent.data), app=Object.by_oid(form.app.data))
		return redirect(url_for("pybble.views.view_oid", oid=obj.oid))
	
	return render_template('edit/site.html', obj=None, form=form, title_trace=["neue Website"])

@expose("/")
def viewer(**args):
	return render_my_template(obj=current_site, detail=TM_DETAIL_PAGE, **args)

