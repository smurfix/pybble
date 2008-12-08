# -*- coding: utf-8 -*-

from werkzeug import redirect
from werkzeug.exceptions import NotFound
from pybble.utils import current_request, make_permanent
from pybble.render import url_for, expose, render_template, valid_obj, \
	discr_list, name_discr
from pybble.models import Discriminator, Tracker,Change,\
	WantTracking, obj_get, TM_DETAIL, PERM, TM_DETAIL_PAGE, PERM_READ

from pybble.database import db,NoResult
from pybble.flashing import flash
from wtforms import Form, BooleanField, TextField, TextAreaField, \
	SelectField, PasswordField, HiddenField, validators
from wtforms.validators import ValidationError
from sqlalchemy.sql import and_, or_, not_
from datetime import datetime


@expose("/admin/wanttracking")
def list_wanttracking(request):
	"""Complete list"""
	return render_template('wanttrackinglist.html', data=WantTracking.q.filter_by(user=request.user), title_trace=["Beobachtungsliste"])

@expose("/admin/wanttracking/<oid>")
def edit_wanttracking(request, oid=None):
	"""Sub-list below the current object"""
	obj = obj_get(oid)
	if isinstance(obj,WantTracking):
		return editor(request,obj)
	else:
		# show list of tracks for that object
		return render_template('wanttrackinglist.html', obj=obj, title_trace=["Beobachtungsliste"])

plc = PERM.items()
plc.sort()

class WantTrackingForm(Form):
	user = TextField('User', [valid_obj])
	object = TextField('Object', [valid_obj])

	discr = SelectField('Existing Object type?', choices=(("-","any object"),)+tuple((str(q.id),q.name) for q in discr_list))
	inherit = SelectField('Applies to?', choices=(('Yes','All sub-pages'), ('No','this page only'),('*','This page and all sub-pages')))
	clone = SelectField('Copy?', choices=(('Yes','Store new entry'),('No','Modify existing entry')))
	email = BooleanField(u'Mail schicken?')
	track_new = BooleanField(u'Meldung bei neuen Einträgen')
	track_mod = BooleanField(u'Meldung bei Änderungen')
	track_del = BooleanField(u'Meldung bei Löschung')

def newer(request, parent, name=None):
	return editor(request, parent=parent)

def editor(request, obj=None, parent=None):
	form = WantTrackingForm(request.form, prefix="perm")
	if parent:
		del form.clone
	if request.method == 'POST' and form.validate():
		user = obj_get(form.user.data)
		dest = obj_get(form.object.data)
		discr = None if form.discr.data == "-" else int(form.discr.data)
		email = bool(form.email.data)
		track_new = bool(form.track_new.data)
		track_mod = bool(form.track_mod.data)
		track_del = bool(form.track_del.data)

		if form.inherit.data == "Yes": inherit = True
		elif form.inherit.data == "No": inherit = False
		elif form.inherit.data == "*": inherit = None
		else: assert False

		if parent:
			obj = WantTracking(user, dest, discr)
			obj.track_new=track_new
			obj.track_mod=track_mod
			obj.track_del=track_del
			obj.email=email
			obj.inherit=inherit

			db.session.add(obj)
			db.session.flush()
			Tracker(request.user,obj)
		else:
			chg = ""
			if obj.owner != user:
				chg += u"Owner: %s (%s) ⇒ %s (%s)\n" % (obj.owner,obj.owner.oid(), user,user.oid())
				obj.owner = user
			if obj.parent != dest:
				chg += u"Tracked: %s (%s) ⇒ %s (%s)\n" % (obj.parent,obj.parent.oid(), parent,parent.oid())
				obj.parent = obj
			if obj.discr != discr:
				chg += u"Type: %s (%s) ⇒ %s (%s)\n" % (name_discr(obj.discr),obj.discr, name_discr(discr),discr)
				obj.discr = discr
			if obj.inherit != inherit:
				chg += u"Inherit: %s ⇒ %s\n" % ("*" if obj.inherit is None else "NY"[obj.inherit], 
				                                "*" if inherit is None else "NY"[inherit])
				obj.inherit = inherit
			if chg:
				Change(request.user,obj,chg)

		flash(u"Gespeichert.",True)

		return redirect(url_for("pybble.views.view_oid", oid=(parent or dest).oid()))

	
	elif request.method == 'GET':
		if obj: # bearbeiten / kopieren
			form.object.data = parent.oid() if parent else obj.parent.oid()
			form.user.data = obj.owner.oid()
			form.discr.data = str(obj.discr)
			form.inherit.data = "*" if obj.inherit is None else "Yes" if obj.inherit else "No"
			form.track_new.data = obj.track_new
			form.track_mod.data = obj.track_mod
			form.track_del.data = obj.track_del
			form.email.data = obj.email
		else:
			form.object.data = parent.oid()
			form.user.data = request.user.oid()
			form.discr.data = "-"
			form.inherit.data = "*"
			form.track_new.data = True
			form.track_mod.data = False
			form.track_del.data = False
			form.email.data = False

	return render_template('edit/wanttracking.html', obj=obj, parent=parent or obj.parent, form=form, title_trace=["Beobachten"])


