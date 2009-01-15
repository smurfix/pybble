# -*- coding: utf-8 -*-

from pybble.render import render_template, expose
from pybble.flashing import flash
from pybble.models import Verifier, VerifierBase, obj_get
from pybble.database import db,NoResult
from wtforms import Form, TextField, validators
from werkzeug.exceptions import NotFound

###
### Confirm
###

def code_exists(form, field):
	try:
		v = Verifier.q.get_by(code=field.data)
	except NoResult:
		raise ValidationError(u"Diesen Code kenne ich nicht.")
	else:
		if v.expired:
			raise ValidationError(u"Dieser Code ist zu alt.")

class ConfirmForm(Form):
	code = TextField('Code', [validators.length(min=10, max=30), code_exists])

@expose('/admin/confirm')
@expose('/admin/confirm/<code>')
def confirm(request, code=None):
	if code is None:
		form = ConfirmForm(request.values, prefix='confirm')

		if request.method != 'POST' or not form.validate():
			return render_template('confirm.html', form=form, title_trace=[u"Bestätigung"])
		code=form.code.data.lower()

	v=Verifier.q.get_by(code=form.code.data.lower())
	if v.expired:
		flash(u"Die Anfrage ist schon zu alt. Bitte schicke sie nochmal ab!")
		return v.retry()
	return v.entered()
	
	
@expose('/admin/confirmed/<oid>')
def confirmed(request, oid):
	obj = obj_get(oid)
	if isinstance(obj,Verifier):
		return obj.confirmed()
	raise NotFound()


@expose('/admin/do_confirm/<oid>')
def do_confirm(request, oid):
	if request.method == 'POST':
		obj = obj_get(oid)
		if isinstance(obj,Verifier) and request.user.can_admin(obj.parent):
			return obj.entered()
	raise NotFound()
