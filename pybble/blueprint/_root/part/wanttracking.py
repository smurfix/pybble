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

from flask import request, url_for, flash

from werkzeug import redirect
from werkzeug.exceptions import NotFound
from wtforms import Form, BooleanField, TextField, SelectField, validators

from pybble.render import valid_obj, valid_read, valid_admin_self
from pybble.core.models.object import Object
from pybble.core.models._const import PERM, PERM_READ
from pybble.core.models.tracking import WantTracking
from pybble.core.db import db
from pybble.render import render_template

from .._base import expose
expose = expose.sub("part.wanttracking")

from datetime import datetime

@expose("/admin/wanttracking")
def list_wanttracking():
	"""Complete list"""
	return render_template('wanttrackinglist.html', data=db.filter_by(WantTracking, user=request.user), title_trace=["Beobachtungsliste"])

@expose("/admin/wanttracking/<oid>")
def edit_wanttracking(oid=None):
	"""Sub-list below the current object"""
	obj = Object.by_oid(oid)
	if isinstance(obj,WantTracking):
		return editor(obj)
	else:
		# show list of tracks for that object
		return render_template('wanttrackinglist.html', obj=obj, title_trace=["Beobachtungsliste"])

plc = PERM.items()
plc.sort()

class WantTrackingForm(Form):
	user = TextField('User', [valid_obj, valid_admin_self])
	object = TextField('Object', [valid_obj, valid_read])

	objtyp = SelectField('Object type') ###TODO , choices=(("-","any object"),)+tuple((str(q.id),q.name) for q in D))
	email = BooleanField(u'Mail schicken')
	track_new = BooleanField(u'Meldung bei neuen Einträgen')
	track_mod = BooleanField(u'Meldung bei Änderungen')
	track_del = BooleanField(u'Meldung bei Löschung')

def newer(parent, name=None):
	return editor(parent=parent)

def editor(obj=None, parent=None):
	form = WantTrackingForm(request.form, prefix="perm")
	if request.method == 'POST' and form.validate():
		user = Object.by_oid(form.user.data)
		dest = Object.by_oid(form.object.data)
		objtyp = None if form.objtyp.data == "-" else int(form.objtyp.data)
		email = bool(form.email.data)
		track_new = bool(form.track_new.data)
		track_mod = bool(form.track_mod.data)
		track_del = bool(form.track_del.data)

		if parent:
			obj = WantTracking.new(user, dest, objtyp)
		else:
			obj.record_change()
			obj.owner = user
			obj.parent = dest
			obj.objtyp = objtyp

		obj.track_new=track_new
		obj.track_mod=track_mod
		obj.track_del=track_del
		obj.email=email

		flash(u"Gespeichert.",True)

		return redirect(url_for("pybble.views.view_oid", oid=(parent or dest).oid))

	elif request.method == 'GET':
		if obj: # bearbeiten / kopieren
			form.object.data = parent.oid if parent else obj.parent.oid
			form.user.data = obj.owner.oid
			form.objtyp.data = str(obj.objtyp)
			form.track_new.data = obj.track_new
			form.track_mod.data = obj.track_mod
			form.track_del.data = obj.track_del
			form.email.data = obj.email
		else:
			form.object.data = parent.oid
			form.user.data = request.user.oid
			form.objtyp.data = "-"
			form.track_new.data = True
			form.track_mod.data = False
			form.track_del.data = False
			form.email.data = False

	return render_template('edit/wanttracking.html', obj=obj, parent=parent or obj.parent, form=form, title_trace=["Beobachten"])

