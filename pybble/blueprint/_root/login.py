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

from flask import request, flash, current_app, url_for
from werkzeug import redirect
from werkzeug.exceptions import NotFound

from pybble.utils import make_permanent
from pybble.render import render_template, send_mail
from pybble.core.db import db,NoData
from pybble.core.models.user import User
from pybble.core.models.verifier import Verifier, VerifierBase
from pybble.core.session import logged_in
from wtforms import Form, BooleanField, TextField, PasswordField, HiddenField, validators
from wtforms.validators import ValidationError
from jinja2 import Markup
from datetime import datetime,timedelta
import sys
from ._base import expose
expose = expose.sub("login")

###
### Login
###

class LoginForm(Form):
	username = TextField('Username', [validators.required(u"Deinen Usernamen brauche ich schon …"), validators.length(min=3, max=30)])
	password = PasswordField('Passwort', [validators.required(u"Ohne (korrektes) Passwort geht es nicht weiter."), validators.length(min=5, max=30)])
	remember = BooleanField('Eingeloggt bleiben')
	next = HiddenField("next URL")

@expose("/admin/login")
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
			u = User.q.get_by(username=form.username.data, password=form.password.data)
		except NoData:
			print >>sys.stderr,"No user",form.username.data,form.password.data,request.site
			u = None
		else:
			if not u.member_of(request.site):
				print >>sys.stderr,u,"wrong site"
				u = None
		if u:
			logged_in(u)

			now = datetime.utcnow()
			if u.cur_login is None or u.cur_login < now-timedelta(0,600):
				u.last_login = u.cur_login or now
			u.cur_login = now

			if form.remember.data:
				make_permanent()

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

@expose('/admin/register')
def register():
	form = RegisterForm(request.form, prefix='register')
	if request.method == 'POST' and form.validate():
		u = User(form.username.data, form.password.data)
		u.email = form.email.data
		u.parent = request.site
		u.record_creation()

		v = verifier.new(u)
		v.send()

		flash(Markup(u"Wir haben soeben eine Email an dich geschickt. <br />" + \
			u"Klicke auf den darin enhaltenen Link oder tippe den Bestätigungscode hier ein."))
		return redirect(url_for("pybble.confirm.confirm"))

	form.password.data = form.password2.data = ""
	return render_template('register.html', form=form, title_trace=[u"Neuer Benutzer"])

###
### Confirm email 
###

class verifier(object):
	@staticmethod
	def new(user):
		v=Verifier("register",user)
		v.superparent = request.site
		return v

	@staticmethod
	def send(verifier):
		from pybble.confirm import confirm
		user=verifier.parent
		send_mail(user.email, 'verify_email.txt',
		          user=user, code=verifier.code,
		          link=url_for("pybble.confirm.confirm", code=verifier.code, _external=1),
				  page=url_for("pybble.confirm.confirm", _external=1))
	
	@staticmethod
	def entered(verifier):
		u = verifier.parent
		if not u.is_verified(verifier.superparent):
			u.add_verified(True,verifier.superparent)
			return redirect(url_for("pybble.confirm.confirmed",oid=verifier.oid()))

		if current_app.user == u:
			flash(u"Du bist bereits verifiziert.")
			return redirect(url_for("pybble.views.mainpage"))
		elif not request.user.anon:
			flash(u"Der User ist bereits verifiziert.")
			return redirect(url_for("pybble.views.mainpage"))
		else:
			flash(u"Du bist bereits verifiziert, musst dich aber einloggen.")
			return redirect(url_for("pybble.login.do_login"))
	
	@staticmethod
	def confirmed(verifier):
		u = verifier.parent

		if request.user == u:
			flash(u"Du bist jetzt verifiziert.", True)
			return redirect(url_for("pybble.views.mainpage"))
		elif not request.user.anon:
			flash(u"Der User ist jetzt verifiziert.", True)
			return redirect(url_for("pybble.views.mainpage"))
		else:
			flash(u"Du bist jetzt verifiziert, musst dich aber noch einloggen.", True)
			return redirect(url_for("pybble.login.do_login"))

@expose("/admin/logout")
def do_logout():
	if request.user.anon:
		flash(u'Du warst nicht eingeloggt', False)
		return redirect(request.args.get("next",None) or url_for("pybble.views.mainpage"))
	else:
		request.session.pop('uid', None)
		request.user = request.site.anon_user
		flash(u'Du hast dich erfolgreich abgemeldet.', True)
		return redirect(url_for("pybble.views.mainpage"))

