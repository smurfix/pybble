# -*- coding: utf-8 -*-

from werkzeug import redirect
from werkzeug.exceptions import NotFound
from pybble.utils import current_request, make_permanent, session
from pybble.render import url_for, expose, render_template, send_mail
from pybble.models import User, Verifier, VerifierBase
from pybble.database import db,NoResult
from pybble.flashing import flash
from pybble.session import logged_in
from wtforms import Form, BooleanField, TextField, PasswordField, HiddenField, validators
from wtforms.validators import ValidationError
from jinja2 import Markup
from datetime import datetime,timedelta

###
### Login
###

class LoginForm(Form):
	username = TextField('Username', [validators.length(min=3, max=30)])
	password = PasswordField('Passwort', [validators.length(min=5, max=30)])
	remember = BooleanField('Eingeloggt bleiben')
	next = HiddenField("next URL")

@expose("/admin/login")
def do_login(request):
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
		except NoResult:
			u = None
		else:
			if u.password != form.password.data:
				u = None
		if u:
			logged_in(request,u)

			now = datetime.utcnow()
			if u.last_login is None or u.last_login < now-timedelta(0,500):
				u.last_login = now

			if form.remember.data:
				make_permanent(request)

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
	except NoResult:
		return
	else:
		raise ValidationError(u"Einen Benutzer '%s' gibt es bereits" % (field.data,))

def no_such_email(form, field):
	try:
		u = User.q.get_by(email=field.data)
	except NoResult:
		return
	else:
		raise ValidationError(u"Einen Benutzer mit Mailadresse '%s' gibt es bereits" % (field.data,))

class RegisterForm(Form):
	username = TextField('Username', [validators.length(min=3, max=30), no_such_user])
	email = TextField('Email', [validators.email(u"Dies ist keine gültige Mailadresse."), no_such_email])
	password = PasswordField('Passwort', [validators.length(min=5, max=30)])
	password2 = PasswordField('nochmal', [validators.equal_to('password',u"Die Paßwörter stimmen nicht überein.")])

@expose('/admin/lostpw')
def lostpw(request):
	pass

@expose('/admin/register')
def register(request):
	form = RegisterForm(request.form, prefix='register')
	if request.method == 'POST' and form.validate():
		u = User(form.username.data, form.password.data)
		u.email = form.email.data
		u.parent = request.site
		u.record_creation()

		v = verifier.new(u)
		session.add(v)
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
		u.verified = True
		flash(u"Du bist jetzt verifiziert.")

		if current_request.user == u:
			return redirect(url_for("pybble.views.mainpage"))
		else:
			return redirect(url_for("pybble.login.do_login"))


@expose("/admin/logout")
def do_logout(request):
	if request.user.anon:
		flash(u'Du warst nicht eingeloggt', False)
		return redirect(request.args.get("next",None) or url_for("pybble.views.mainpage"))
	else:
		request.session.pop('uid', None)
		request.user = User.q.get_anonymous_user(request.site)
		flash(u'Du hast dich erfolgreich abgemeldet.', True)
		return redirect(url_for("pybble.views.mainpage"))

