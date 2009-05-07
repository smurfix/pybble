# -*- coding: utf-8 -*-

from werkzeug import redirect
from werkzeug.exceptions import NotFound
from pybble.utils import current_request, make_permanent
from pybble.render import url_for, render_template, expose, render_my_template
from pybble.models import Site, WikiPage, TM_DETAIL_PAGE
from pybble.views import view_oid

from pybble.database import db,NoResult
from pybble.flashing import flash
from pybble.session import logged_in
from wtforms import Form, BooleanField, TextField, TextAreaField, \
	SelectField, PasswordField, HiddenField, validators
from wtforms.validators import ValidationError
from sqlalchemy.sql import and_, or_, not_
from datetime import datetime
from pybble import _settings as settings
try: from hashlib import md5
except ImportError: from md5 import md5


###
### Wiki page editor
###

def newpage(form, field):
	q = WikiPage.q
	if hasattr(form,"obj"):
		q = q.filter(WikiPage.id != form.obj.id)
	try:
		q.get_by(name=field.data, superparent=current_request.site)
	except NoResult:
		pass
	else:
		raise ValidationError(u"Eine Wiki-Seite namens „%s“ gibt es bereits" % (field.data,))

class WikiEditForm(Form):
	name = TextField('Name', [validators.length(min=3, max=30), newpage])
	page = TextAreaField('Page')
	hash = HiddenField('Hash')
	comment = TextField('Kommentar', [validators.length(min=3, max=200)])

def newer(request, parent, name=None):
	if parent is None:
		parent = request.site
	elif isinstance(parent.parent,WikiPage):
		parent = parent.parent

	form = WikiEditForm(request.form, prefix="wiki")
	if request.method == 'POST' and form.validate():
		obj = WikiPage(form.name.data,form.page.data.replace("\r",""))
		if isinstance(parent,Site):
			obj.superparent = parent
		elif isinstance(parent,WikiPage):
			obj.superparent = None
		else:
			obj.superparent = parent.site
		obj.parent = parent
		obj.owner = request.user
		obj.record_creation()
		flash(u"Wiki-Seite '%s' gespeichert." % (obj.name), True)
		return redirect(url_for("pybble.views.view_oid", oid=obj.oid()))

	elif request.method == 'GET':
		form.name.data = name
		form.page.data = ""

	return render_template('edit/wikipage.html', parent=parent, form=form, name=form.name.data, title_trace=[form.name.data])

	
def editor(request, obj=None):
	form = WikiEditForm(request.form, prefix="wiki")
	form.obj = obj
	if request.method == 'POST' and form.validate():
		if form.hash.data != md5("%s.%s.%s" % (settings.SECRET_KEY, obj.id, obj.data)).digest().encode('base64').strip('\n ='):
			flash("Die Seite hat sich zwischenzeitlich geändert!",False)
			return redirect(url_for("pybble.views.view_oid", oid=obj.oid()))

		if obj.data != form.page.data or obj.name != form.name.data:
			obj.record_change(comment=form.comment.data)
			obj.name = form.name.data
			obj.data = form.page.data.replace("\r","")
			obj.modified = datetime.utcnow()

			flash(u"Wiki-Seite '%s' geändert." % (obj.name), True)
		else:
			flash(u"Wiki-Seite '%s' unverändert." % (obj.name))

		return redirect(url_for("pybble.views.view_oid", oid=obj.oid()))
	
	elif request.method == 'GET':
		form.name.data = obj.name
		form.page.data = obj.data
		form.hash.data = md5("%s.%s.%s" % (settings.SECRET_KEY, obj.id, obj.data)).digest().encode('base64').strip('\n =')

	return render_template('edit/wikipage.html', obj=obj, form=form, name=form.name.data, title_trace=[form.name.data])


@expose("/wiki/<name>")
@expose("/wiki/<parent>/<name>")
def viewer(request, name, parent=None, obj=None):
	if obj and request.site == obj.superparent:
		if isinstance(obj.parent,WikiPage):
			return redirect(url_for("pybble.part.wikipage.viewer", name=name, parent=obj.parent.name))
		else:
			return redirect(url_for("pybble.part.wikipage.viewer", name=obj.name))

	try:
		if obj:
			if isinstance(obj.parent,WikiPage):
				parent = obj.parent
		elif parent:
			if parent == name:
				return redirect(url_for("pybble.part.wikipage.viewer", name=name))
			parent = WikiPage.q.get_by(name=parent, superparent=request.site)
			obj = WikiPage.q.get_by(name=name, parent=parent)
		else:
			obj = WikiPage.q.get_by(name=name, superparent=request.site)
	except NoResult:
		if not parent:
			raise
		if not isinstance(parent,WikiPage):
			raise
		if request.user.can_add(parent):
			flash("Die Seite gibt es noch nicht. Du kannst sie jetzt anlegen.")
			return redirect(url_for("pybble.views.new_oid", oid=parent.oid(), name=name, discr=WikiPage.cls_discr()))
		else:
			flash("Die Seite gibt es noch nicht. Du darfst sie leider auch nicht anlegen.",False)
			return redirect(url_for("pybble.views.view_oid", oid=parent.oid()))
	else:
		return render_my_template(request, obj=obj, detail=TM_DETAIL_PAGE, \
			title_trace=([obj.name, parent.name] if parent else [obj.name]))

