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

from flask import flash, request
from werkzeug.exceptions import NotFound
from wtforms import Form, TextField, validators
from wtforms.validators import ValidationError

from pybble.render import render_template
from pybble.core.db import db,NoData
from pybble.core.models import obj_get
from pybble.core.models.verifier import Verifier, VerifierBase
from ._base import expose

###
### Confirm
###

def code_exists(form, field):
	try:
		v = Verifier.q.get_by(code=str(field.data))
	except NoData:
		raise ValidationError(u"Diesen Code kenne ich nicht.")
	else:
		if v.expired:
			raise ValidationError(u"Dieser Code ist zu alt.")

class ConfirmForm(Form):
	code = TextField('Code', [validators.required(u"Den Code solltest du schon angeben …"), validators.length(min=10, max=30), code_exists])

@expose('/admin/confirm')
@expose('/admin/confirm/<code>')
def confirm(code=None):
	if code is None:
		form = ConfirmForm(request.values, prefix='confirm')

		if request.method != 'POST' or not form.validate():
			return render_template('confirm.html', form=form, title_trace=[u"Bestätigung"])
		code=form.code.data.lower()

	v=Verifier.q.get_by(code=str(code))
	if v.expired:
		flash(u"Die Anfrage ist schon zu alt. Bitte schicke sie nochmal ab!")
		return v.retry()
	return v.entered()
	
	
@expose('/admin/confirmed/<oid>')
def confirmed(oid):
	obj = obj_get(oid)
	if isinstance(obj,Verifier):
		return obj.confirmed()
	raise NotFound()

@expose('/admin/do_confirm/<oid>')
def do_confirm(oid):
	if request.method == 'POST':
		obj = obj_get(oid)
		if isinstance(obj,Verifier) and request.user.can_admin(obj.parent):
			return obj.entered()
	raise NotFound()
