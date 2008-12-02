# -*- coding: utf-8 -*-

from pybble.render import render_template, expose
from pybble.flashing import flash
from pybble.models import Verifier, VerifierBase
from pybble.database import db,NoResult
from wtforms import Form, TextField, validators

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
	form = ConfirmForm(request.values, prefix='confirm')
	if request.method == 'POST' and form.validate():
		v=Verifier.q.get_by(code=form.code.data.lower())
		if v.expired:
			flash(u"Die Anfrage ist schon zu alt. Bitte schicke sie nochmal ab!")
			return v.retry()
		return v.entered()
	return render_template('confirm.html', form=form, title_trace=[u"Bestätigung"])
	
	

