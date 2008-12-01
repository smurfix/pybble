# -*- coding: utf-8 -*-

from werkzeug import redirect
from werkzeug.exceptions import NotFound
from pybble.utils import render_template, expose, \
     url_for, send_mail, current_request, make_permanent, \
	 render_my_template
from pybble.models import WikiPage, TM_DETAIL_PAGE
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
### Wiki page editor
###

class WikiEditForm(Form):
	name = TextField('Name', [validators.length(min=3, max=30)])
	page = TextAreaField('Page')

def editor(request, obj=None, name=None):
	form = WikiEditForm(request.form, prefix="wiki")
	error = ""
	parent = None
	if request.method == 'POST' and form.validate():
		if obj:
			try:
				WikiPage.q.filter(WikiPage.id != obj.id).get_by(name=form.name.data, superparent=request.site)
			except NoResult:
				pass
			else:
				error = "Diese Wiki-Seite gibt es bereits!"
		if name:
			parent = obj
			try:
				obj = WikiPage.q.get_by(name=form.name.data, superparent=request.site)
			except NoResult:
				obj = None
			else:
				error = "Eine Wiki-Seite dieses Namens gibt es bereits!"

		if not error:
			if obj is None:
				obj = WikiPage(form.name.data,form.page.data)
				obj.superparent = request.site
				obj.parent = parent
				db.session.add(obj)
			elif obj.data != form.page.data:
				obj.data = form.page.data
				obj.modified = datetime.utcnow()
			flash("Wiki-Seite '%s' gespeichert." % (obj.name), True)
			return redirect(url_for("pybble.views.view_oid", oid=obj.oid()))

	
	elif request.method == 'GET':
		form.name.data = obj.name if obj else name
		form.page.data = obj.data if obj else ""
	return render_template('wikiedit.html', obj=obj, form=form, error=error, name=form.name.data, title_trace=[form.name.data])


@expose("/wiki/<name>")
def viewer(request, name):
	obj = WikiPage.q.get_by(name=name)
	return render_my_template(request, obj=obj, detail=TM_DETAIL_PAGE, \
		title_trace=[obj.name])

