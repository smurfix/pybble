# -*- coding: utf-8 -*-

from werkzeug import redirect
from werkzeug.exceptions import NotFound
from pybble.utils import current_request, make_permanent, random_string
from pybble.render import url_for, expose, render_template, valid_obj, \
	discr_list
from pybble.models import Template, TemplateMatch, Discriminator, \
	Permission, obj_get, TM_DETAIL, PERM, TM_DETAIL_PAGE, User

from pybble.database import db,NoResult
from pybble.flashing import flash
from pybble.session import logged_in
from wtforms import Form, BooleanField, TextField, TextAreaField, \
	SelectField, PasswordField, HiddenField, validators, IntegerField
from wtforms.validators import ValidationError
from sqlalchemy.sql import and_, or_, not_
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
	new_id = IntegerField('Neue ID generieren')

@expose("/rss/<feed_pass>")
def do_rss(request, feed_pass):
	assert len(feed_pass)>10
	user = User.q.get_by(feed_pass=feed_pass)
	return render_template('rss.xml', user=user, mimetype="application/rss+xml")

@expose("/rss")
def config_rss(request):
	user = request.user
	if user.anon:
		flash("Du musst dich erst einloggen.")
		return redirect(url_for("pybble.login.do_login", next=url_for("pybble.rss.config_rss")))
		
	form = RSSForm(request.form, prefix="rss")
	if request.method == 'POST' and form.validate():
		user.feed_age = int(form.age.data)
		if form.new_id.data or not user.feed_pass:
			user.feed_pass = random_string(30)
		flash(u"Gespeichert.",True)
		return redirect(url_for("pybble.views.mainpage"))

	elif request.method == 'GET':
		form.age.data = str(user.feed_age)

	new_feed = not user.has_trackers

	return render_template('rssconfig.html', form=form, title_trace=["RSS-Einstellungen"], new_feed=new_feed)


tmc = TM_DETAIL.items()
tmc.sort()

class TemplateForm(Form):
	oid = TextField('OID', [valid_obj])
	detail = SelectField('Detail', choices=tuple((str(x),y) for x,y in tmc))
	discr = SelectField('Object type', choices=tuple((str(q.id),q.name) for q in discr_list))
	inherit = SelectField('Applies to', choices=(('Yes','All sub-pages'), ('No','this page only'),('*','This page and all sub-pages')))
	page = TextAreaField('Template')
	clone = SelectField('Copy', choices=(('Yes','Store new template'),('Link','Add new assoc'),('No','Replace old assoc')))

def edit_assoc_template(request, match, template, obj):
	form = TemplateForm(request.form, prefix="template")
	error = ""
	if request.method == 'POST' and form.validate():
		if form.clone.data == "Yes":
			template = Template(None, form.page.data)
			db.session.add(template)
		elif template.data != form.page.data:
			template.data = form.page.data
			template.modified = datetime.utcnow()

		if form.inherit.data == "Yes": inherit = True
		elif form.inherit.data == "No": inherit = False
		elif form.inherit.data == "*": inherit = None
		else: assert False

		obj = obj_get(form.oid.data)

		if match and form.clone.data == "No":
			match.discr = int(form.discr.data)
			match.detail = int(form.detail.data)
			match.inherit = inherit
			match.template = template
			match.obj = obj
		else:
			try:
				match = TemplateMatch.q.get_by(discr = int(form.discr.data), detail=int(form.detail.data), obj=obj, inherit=inherit)
			except NoResult:
				match = TemplateMatch(obj,int(form.discr.data),int(form.detail.data),template)
				match.inherit = inherit
				db.session.add(match)
			else:
				match.discr = int(form.discr.data)
				match.detail = int(form.detail.data)
				match.inherit = inherit
				match.template = template

		flash(u"Gespeichert.",True)

		if match.inherit is None:
			m = TemplateMatch.q.filter(TemplateMatch.inherit != None)
		else:
			m = TemplateMatch.q.filter(TemplateMatch.inherit == None)
		m = m.filter_by(discr=match.discr, detail=match.detail, obj=obj)
		if match.inherit is None:
			if m.count():
				flash(u"Vorherige Assoziation(en) entfernt.")
				for mm in m:
					db.session.delete(mm)
		else:
			if m.count():
				flash(u"Bestehende Assoziation eingeschränkt.")
				for mm in m:
					mm.inherit = not match.inherit

		return redirect(url_for("pybble.admin.edit_template", template=obj.oid()))

	
	elif request.method == 'GET':
		form.page.data = template.data
		if obj:
			form.oid.data = obj.oid()
			form.discr.data = str(obj.discriminator)
		form.detail.data = str(TM_DETAIL_PAGE)
		if match:
			form.discr.data = str(match.discr)
			form.detail.data = str(match.detail)
			form.inherit.data = "*" if match.inherit is None else "Yes" if match.inherit else "No"
		else:
			form.inherit.data = "*"

	return render_template('itemplate.html', obj=obj, templ=template, form=form, error=error, title_trace=[template.name])


