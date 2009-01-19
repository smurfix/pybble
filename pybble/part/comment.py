# -*- coding: utf-8 -*-

from werkzeug import redirect
from werkzeug.exceptions import NotFound
from pybble.utils import current_request, make_permanent
from pybble.render import url_for, render_template, expose, render_my_template
from pybble.models import WikiPage, Site, Comment, TM_DETAIL_PAGE
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
### Comment editor
###

def newpage(form, field):
	q = Comment.q
	if hasattr(form,"obj"):
		q = q.filter(Comment.id != form.obj.id)
	try:
		q.get_by(name=field.data, superparent=current_request.site)
	except NoResult:
		pass
	else:
		raise ValidationError(u"Eine Wiki-Seite namens „%s“ gibt es bereits" % (field.data,))

class CommentEditForm(Form):
	name = TextField('Name', [validators.length(min=3, max=30), newpage])
	page = TextAreaField('Page')

def newer(request, parent, name=None):
	if parent is None:
		parent = request.site

	form = CommentEditForm(request.form, prefix="comment")
	if request.method == 'POST' and form.validate():
		obj = Comment(parent, form.name.data,form.page.data.replace("\r",""))
		obj.record_creation()
		flash(u"Kommentar '%s' gespeichert." % (obj.name), True)
		return redirect(url_for("pybble.views.view_oid", oid=obj.oid()))

	elif request.method == 'GET':
		name = getattr(parent,"name",None)
		if name is None:
			name = ""
		elif not name.startswith("Re: "):
			name = "Re: "+name
		form.name.data = name
		data = getattr(parent,"data",None) or ""
		if data:
			data = "> "+data.rstrip().replace("\n","\n> ")+"\n"
		form.page.data = data

	return render_template('edit/comment.html', parent=parent, form=form, name=form.name.data, title_trace=["Kommentieren"])

	
def editor(request, obj=None):
	form = CommentEditForm(request.form, prefix="comment")
	form.obj = obj
	if request.method == 'POST' and form.validate():
		if obj.data != form.page.data:
			obj.record_change(comment=form.name.data)
			obj.data = form.page.data.replace("\r","")
			obj.modified = datetime.utcnow()

			flash(u"Kommentar '%s' geändert." % (obj.name), True)
		else:
			flash(u"Wiki-Seite '%s' unverändert." % (obj.name))

		return redirect(url_for("pybble.views.view_oid", oid=obj.oid()))

	
	elif request.method == 'GET':
		form.name.data = obj.name if obj else name
		form.page.data = obj.data if obj else ""
	return render_template('edit/comment.html', obj=obj, form=form, name=form.name.data, title_trace=["Kommentar editieren"])


