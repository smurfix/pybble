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

"""
This module contains the verifier which checks that a user's email is
valid.

It is tied too tightly to the Pybble root for comfort.
"""

from flask import render_template, abort, request, redirect, url_for, flash
from jinja2 import TemplateNotFound

from pybble.verifier import BaseVerifier
from pybble.core.route import Exposer
from pybble.render import send_mail
from pybble.core.models.verifier import Verifier as DBVerifier
expose = Exposer()

class Verifier(BaseVerifier):
	"""Verify an email."""

	@classmethod
	def new(cls, user,obj, *a,**k):
		## verify this user's email
		return None

	@classmethod
	def send(cls,verifier):
		user=verifier.user
		send_mail(user.email, 'verify_email.txt',
			  user=user, code=verifier.code,
			  link=url_for("pybble.confirm.confirm", code=verifier.code, _external=1),
				  page=url_for("pybble.confirm.confirm", _external=1))
	
	@classmethod
	def entered(cls,verifier):
		u = verifier.user
		if not u.is_verified(verifier.parent):
			u.add_verified(True,verifier.parent)
			return redirect(url_for("pybble.confirm.confirmed",oid=verifier.oid))

		if request.user == u:
			flash(u"Du bist bereits verifiziert.")
			return redirect(url_for("pybble.views.mainpage"))
		elif not request.user.anon:
			flash(u"Der User ist bereits verifiziert.")
			return redirect(url_for("pybble.views.mainpage"))
		else:
			flash(u"Du bist bereits verifiziert, musst dich aber einloggen.")
			return redirect(url_for("pybble.login.do_login"))
	
	@classmethod
	def confirmed(cls,verifier):
		u = verifier.user

		if request.user == u:
			flash(u"Du bist jetzt verifiziert.", True)
			return redirect(url_for("pybble.views.mainpage"))
		elif not request.user.verified:
			request.user.verified = True
			flash(u"Der User ist jetzt verifiziert.", True)
			return redirect(url_for("pybble.views.mainpage"))
		else:
			flash(u"Du bist jetzt verifiziert, musst dich aber noch einloggen.", True)
			return redirect(url_for("pybble.login.do_login"))

