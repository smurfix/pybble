# -*- coding: utf-8 -*-

from werkzeug import redirect
from werkzeug.exceptions import NotFound
from pybble.utils import Pagination, render_template, expose, \
     validate_url, url_for, render_my_template, send_mail
from pybble.models import User, Verifier, VerifierBase
from pybble.database import db,NoResult
from pybble.flashing import flash
from wtforms import Form, BooleanField, TextField, PasswordField, HiddenField, validators

###
### Login
###

class LoginForm(Form):
	username = TextField('Username', [validators.length(min=3, max=30)])
	password = PasswordField('Passwort', [validators.length(min=5, max=30)])
	remember = BooleanField('Eingeloggt bleiben?')
	next = HiddenField("next URL")

@expose("/admin/login")
def do_login(request):
	form = LoginForm(request.form, prefix='login')
	error = ""

	user = getattr(request,"user",None)
	if user and not user.anon:
		flash("Du bist bereits eingeloggt!")
		return redirect((request.form or request.args or {}).get("next",None) or url_for("mainpage"))

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
			request.session['uid'] = u.id
			request.user = u

			if form.next.data:
				return redirect(next)
			else:
				return redirect(url_for("mainpage"))
		else:
			flash("Benutzer oder Passwort waren falsch.",False)
	return render_template('login.html', form=form, error=error)

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
		db.session.add(u)

		v = verifier.new(u)
		db.session.add(v)
		v.send()

		flash(u"Wir haben soeben eine Email an dich geschickt. <br />" + \
			u"Klicke auf den darin enhaltenen Link oder tippe den Bestätigungscode hier ein.")
		return redirect(url_for("confirm"))

	form.password.data = form.password2.data = ""
	return render_template('register.html', form=form)

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
		          link=url_for("confirm", code=verifier.code), page=url_for("confirm"))
	
	@staticmethod
	def entered(verifier):
		u = verifier.parent
		u.verified = True
		flash(u"Du bist jetzt verifiziert.")
		return redirect(url_for("mainpage"))
