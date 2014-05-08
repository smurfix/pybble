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

from flask import request, url_for

from werkzeug import redirect
from werkzeug.exceptions import NotFound
from wtforms import Form, BooleanField, TextField, TextAreaField, \
	SelectField, PasswordField, HiddenField, validators, IntegerField
from wtforms.validators import ValidationError

from pybble.core.db import db,NoData
from pybble.core.session import logged_in
from pybble.utils import random_string
from pybble.render import render_template, valid_obj
from pybble.core.models.template import Template, TemplateMatch
from pybble.core.models import Discriminator, obj_get, TM_DETAIL, PERM, TM_DETAIL_PAGE
from pybble.core.models.user import Permission, User
from ._base import expose

from flask import flash
from datetime import datetime

###
### Template editor
###

def small_age(form, field):
	i = int(field.data)
	if i < 2:
		raise ValidationError("min. 2 Tage")
	elif i > 99:
		raise ValidationError("max. 3 Monate")

class RSSForm(Form):
	age = IntegerField('Age', [small_age])
	new_id = BooleanField('Neue ID generieren')

@expose("/rss/<feed_pass>")
def do_rss(feed_pass):
	assert len(feed_pass)>10
	user = User.q.get_by(feed_pass=feed_pass)
	request.user = user
	return render_template('rss.xml', mimetype="application/rss+xml")

@expose("/rss")
def config_rss():
	user = request.user
	if user.anon:
		flash("Du musst dich erst einloggen.")
		return redirect(url_for("pybble.login.do_login", next=url_for("pybble.rss.config_rss")))
		
	form = RSSForm(request.form, prefix="rss")
	if request.method == 'POST' and form.validate():
		user.feed_age = int(form.age.data)
		if form.new_id.data or not user.feed_pass:
			user.feed_pass = unicode(random_string(30))
		flash(u"Gespeichert.",True)
		return redirect(url_for("pybble.views.mainpage"))

	elif request.method == 'GET':
		form.age.data = str(user.feed_age)

	new_feed = not user.has_trackers

	return render_template('rssconfig.html', form=form, title_trace=["RSS-Einstellungen"], new_feed=new_feed)

