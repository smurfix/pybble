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
from datetime import datetime
from pybble import _settings as settings
try: from hashlib import md5
except ImportError: from md5 import md5


###
### Wiki page editor
###

def newpage(form, field):
	filter = [ WikiPage.name == field.data ]
	obj = getattr(form,"obj", None)
	if obj:
		filter.append(WikiPage.id != obj.id)
	if getattr(obj,"mainpage",None) or form.mainpage.data:
		filter.append(WikiPage.superparent_id == current_request.site.id)
	else:
		parent = getattr(form,"parent",None)
		if isinstance(parent,WikiPage):
			filter.append(WikiPage.parent_id == parent.id)
	obj = db.store.find(WikiPage,*filter).one()
	if obj:
		raise ValidationError(u"Eine Wiki-Seite namens „%s“ gibt es hier bereits" % (field.data,))

def wikiparent(form,field):
	if hasattr(form,"obj"):
		return
	if not isinstance(getattr(form,"parent",None),WikiPage) and not field.data:
		raise ValidationError(u"Diese Seite muss als Hauptseite angelegt werden")

class WikiEditForm(Form):
	name = TextField('Name', [validators.length(min=3, max=30), newpage])
	page = TextAreaField('Page')
	hash = HiddenField('Hash')
	comment = TextField('Kommentar', [validators.length(min=3, max=200)])
	mainpage = BooleanField(u'übergeordnete Seite', [wikiparent])
	minor = BooleanField(u'nur Kleinigkeiten geändert')

def newer(request, parent, name=None):
	if parent is None:
		parent = request.site

	form = WikiEditForm(request.form, prefix="wiki")
	form.parent = parent
	if request.method == 'POST' and form.validate():
		obj = WikiPage(form.name.data,form.page.data.replace("\r",""))
		if isinstance(parent,WikiPage) and not parent.mainpage:
			parent = parent.parent
		obj.parent = parent
		obj.superparent = request.site
		obj.owner = request.user
		obj.mainpage = form.mainpage.data
		obj.record_creation()
		flash(u"Wiki-Seite '%s' gespeichert." % (obj.name), True)
		return redirect(url_for("pybble.views.view_oid", oid=obj.oid()))

	elif request.method == 'GET':
		form.name.data = name
		form.page.data = ""
		if not isinstance(parent,WikiPage):
			form.mainpage.data = True

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
def viewer(request, name, parent=None, obj=None, **args):
	if not args and (obj and request.site == obj.superparent):
		if not obj.mainpage and isinstance(obj.parent,WikiPage):
			return redirect(url_for("pybble.part.wikipage.viewer", name=name, parent=obj.parent.name))
		else:
			return redirect(url_for("pybble.part.wikipage.viewer", name=obj.name))

	try:
		if obj:
			if isinstance(obj.parent,WikiPage):
				parent = obj.parent
		elif parent:
			if not args and parent == name:
				return redirect(url_for("pybble.part.wikipage.viewer", name=name))
			parent = db.get_by(WikiPage, name=parent, superparent=request.site, mainpage=True)
			obj = db.get_by(WikiPage, name=name, parent=parent, mainpage=False)
		else:
			obj = db.get_by(WikiPage, name=name, superparent=request.site, mainpage=True)
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
			title_trace=([obj.name, parent.name] if parent else [obj.name]), **args)

