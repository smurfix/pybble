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

from flask import request, flash, current_app, url_for, session, render_template
from werkzeug import redirect
from werkzeug.exceptions import NotFound

from pybble.core.db import db,NoData
from pybble.core.models.user import User
from pybble.core.models.verifier import Verifier, VerifierBase
from pybble.core.session import logged_in
from pybble.globals import current_site
from wtforms import Form, BooleanField, TextField, PasswordField, HiddenField, validators
from wtforms.validators import ValidationError
from jinja2 import Markup
from datetime import datetime,timedelta
import sys
from ._base import expose
expose = expose.sub("login")

import logging
logger = logging.getLogger('pybble._root.login')

###
### Login
###

class LoginForm(Form):
	username = TextField('Username', [validators.required(u"Deinen Usernamen brauche ich schon …"), validators.length(min=3, max=30)])
	password = PasswordField('Passwort', [validators.required(u"Ohne (korrektes) Passwort geht es nicht weiter."), validators.length(min=5, max=30)])
	remember = BooleanField('Eingeloggt bleiben')
	next = HiddenField("next URL")

@expose("/admin/login", methods=['GET','POST'])
def do_login():
	form = LoginForm(request.form, prefix='login')
	error = ""

	user = getattr(request,"user",None)
	if user and not user.anon:
		flash(u"Du bist bereits eingeloggt!")
		return redirect((request.form or request.args or {}).get("next",None) or url_for("pybble.views.mainpage"))

	if request.method == 'POST' and form.validate():
		# create new user and show the confirmation page
		try:
			u = User.q.get_by(username=form.username.data)
		except NoData:
			logger.warn("No user {} in {}".format(form.username.data,current_site))
			u = None
		else:
			if not u.check_password(form.password.data):
				logger.warn("Wrong password of {} in {}".format(u,current_site))
				u = None
			else:
				if not u.member_of(current_site) and not u.anon:
					logger.warn("Wrong user {} in {}".format(u,current_site))
					u = None
		if u:
			logged_in(u)

			now = datetime.utcnow()
			if u.cur_login is None or u.cur_login < now-timedelta(0,600):
				u.last_login = u.cur_login or now
			u.cur_login = now

			if u.verified:
				flash(u"Du bist jetzt eingeloggt.",True)
			else:
				flash(u"Benutzer noch nicht verifiziert. Bitte gib den Code aus der Email an!",False)
				return redirect(url_for("pybble.confirm.confirm"))

			if form.next.data:
				return redirect(form.next.data)
			else:
				return redirect(url_for("pybble.views.mainpage"))
		else:
			flash(u"Username oder Passwort sind falsch.",False)
	elif request.method == 'GET':
		form.next.data = request.args.get("next","")
	return render_template('login.html', form=form, error=error, title_trace=["Login"])

###
### register
###

def no_such_user(form, field):
	try:
		u = User.q.get_by(username=field.data)
	except NoData:
		return
	else:
		raise ValidationError(u"Einen Benutzer '%s' gibt es bereits" % (field.data,))

def no_such_email(form, field):
	try:
		u = User.q.get_by(email=field.data)
	except NoData:
		return
	else:
		raise ValidationError(u"Einen Benutzer mit Mailadresse '%s' gibt es bereits" % (field.data,))

class RegisterForm(Form):
	username = TextField('Username', [validators.required(u"Ohne Usernamen habe ich ein Problem."), validators.length(min=3, max=30), no_such_user])
	email = TextField('Email', [validators.required(u"Ohne Email-Adresse geht es nicht, sorry."), validators.email(u"Dies ist keine gültige Mailadresse."), no_such_email])
	password = PasswordField('Passwort', [validators.required(u"Leere Kennwörter sind mir zu unsicher!"), validators.length(min=5, max=30)])
	password2 = PasswordField('nochmal', [validators.equal_to('password',u"Die Paßwörter stimmen nicht überein.")])

@expose('/admin/lostpw')
def lostpw():
	pass

@expose('/admin/register', methods=['GET','POST'])
def register():
	form = RegisterForm(request.form, prefix='register')
	if request.method == 'POST' and form.validate():
		u = User.new(form.username.data, form.password.data, anon=True) ## needs verification
		u.email = form.email.data
		u.parent = current_site
		u.record_creation()

		verifier = VerifierBase.q.get_by(name="register")
		v = verifier.new(obj=current_site, user=u)
		v.send()

		flash(Markup(u"Wir haben soeben eine Email an dich geschickt. <br />" + \
			u"Klicke auf den darin enhaltenen Link oder tippe den Bestätigungscode hier ein."))
		return redirect(url_for("pybble.confirm.confirm"))

	form.password.data = form.password2.data = ""
	return render_template('register.html', form=form, title_trace=[u"Neuer Benutzer"])

@expose("/admin/logout")
def do_logout():
	if request.user.anon:
		flash(u'Du warst nicht eingeloggt', False)
		return redirect(request.args.get("next",None) or url_for("pybble.views.mainpage"))
	else:
		request.user = u = current_site.anon_user
		session['uid'] = u.id
		flash(u'Du hast dich erfolgreich abgemeldet.', True)
		return redirect(url_for("pybble.views.mainpage"))

