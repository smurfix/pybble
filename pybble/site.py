# -*- coding: utf-8 -*-

from werkzeug import redirect
from werkzeug.exceptions import NotFound
from pybble.utils import send_mail, current_request, make_permanent
from pybble.render import url_for, render_template, expose, render_my_template
from pybble.models import Site, TM_DETAIL_PAGE
from pybble.views import view_oid

from pybble.database import db,NoResult
from pybble.flashing import flash
from pybble.session import logged_in
from wtforms import Form, BooleanField, TextField, TextAreaField, \
	SelectField, PasswordField, HiddenField, validators
from wtforms.validators import ValidationError
from sqlalchemy.sql import and_, or_, not_
from datetime import datetime


###
### Site page editor
###

class SiteEditForm(Form):
	name = TextField('Name', [validators.length(min=3, max=30)])
	domain = TextField('Domain', [validators.length(min=3, max=100)])

def editor(request, obj=None, name=None, parent=None):
	assert parent is None
	assert obj is not None
	assert obj is request.site

	form = SiteEditForm(request.form, prefix="site")
	error = ""
	if request.method == 'POST' and form.validate():

		try:
			obj = Site.q.filter(Site.id != obj.id).get_by(name=form.name.data)
		except NoResult:
			pass
		else:
			error = "Seiten dieses Namens gibt es bereits!"

		try:
			obj = Site.q.filter(Site.id != obj.id).get_by(domain=form.domain.data)
		except NoResult:
			pass
		else:
			error = "Seiten unter dieser Domain gibt es bereits!"

		if not error:
			obj.name = form.name.data
			obj.domain = form.domain.data
			return redirect(url_for("pybble.views.view_oid", oid=obj.oid()))
	
	elif request.method == 'GET':
		form.name.data = obj.name if obj else name
		form.domain.data = obj.domain
	return render_template('edit/site.html', obj=obj, form=form, error=error, name=form.name.data, title_trace=["globale Einstellungen"])


@expose("/")
def viewer(request):
	return render_my_template(request, obj=request.site, detail=TM_DETAIL_PAGE)


