# -*- coding: utf-8 -*-

from werkzeug import redirect
from pybble.flashing import flash
from pybble.database import db, NoResult
from pybble.models import Object
from storm.locals import Unicode,Int,DateTime,RawStr
from wtforms import Form,TextField,TextAreaField,validators
from pybble.utils import current_request
from pybble.render import url_for, render_template, render_my_template
from pybble.models import TM_DETAIL_PAGE
from datetime import datetime

__ALL__ = ("Blog","BlogEntry")

TEMPLATES = ("edit.html","new.html","editentry.html","newentry.html")

## System init code
def initsite(replace_templates):
	pass
	
class BlogForm(Form):
	name = TextField('Name', [validators.required(u"Der Name fehlt"), validators.length(min=3, max=250)])
	info = TextField('Info', [validators.required(u"Der Infotext fehlt"), validators.length(min=3, max=250)])


## Database mods
class Blog(Object):
	"""\
		This represents a collection of blog entries.
		Owner: Whoever created the thing.
		"""
	__storm_table__ = "blog"
	_discriminator = 108

	name = Unicode()
	info = Unicode()

	def __init__(self,parent):
		self.owner = current_request.user
		self.parent = parent
		self.superparent = current_request.site
	
	@property
	def data(self):
		return """\
Name: %s
Info: %s
""" % (self.name,self.info)

	def html_view(obj, **args):
		try:
			n = obj.parent.name
		except AttributeError:
			n = None
		return render_my_template(current_request, obj=obj, detail=TM_DETAIL_PAGE, title_trace=[obj.name, n] if n else [obj.name], **args);

	def html_edit(self):
		form = BlogForm(current_request.form)
		form.id = self.id
		if current_request.method == 'POST' and form.validate():
			d = self.data
			self.name = form.name.data
			self.info = form.info.data
			if self.data != d:
				flash(u"Änderung gespeichert.", True)
				self.record_change(d)
			else:
				flash(u"Daten unverändert.")

			return redirect(url_for("pybble.views.view_oid", oid=self.oid()))
		
		elif current_request.method == 'GET':
			form.name.data = self.name
			form.info.data = self.info

		return render_template('blog/edit.html', obj=self, form=form, name=form.name.data, title_trace=[self.name,"Blog"])

	@classmethod
	def html_new(cls,parent,name=None):
		current_request.user.will_add(parent,new_discr=cls)

		form = BlogForm(current_request.form)
		if current_request.method == 'POST' and form.validate():
			obj = cls(parent)
			obj.name = form.name.data
			obj.info = form.info.data

			obj.record_creation()
			flash(u"Daten gespeichert.", True)
			return redirect(url_for("pybble.views.view_oid", oid=obj.oid()))
		
		elif current_request.method == 'GET':
			form.name.data = name
			form.info.data = ""

		return render_template('blog/new.html', parent=parent, form=form, name=form.name.data, title_trace=["new","Blog"])


class BlogEntryForm(Form):
	title = TextField('Titel', [validators.required(u"Kein Beitrag ohne Titel!"), validators.length(min=3, max=250)])
	text = TextAreaField('Text', [validators.required(u"Leere Beiträge sind nicht erlaubt."), validators.length(min=30)])

class BlogEntry(Object):
	"""\
		This represents a blog entry.
		Owner: The person who wrote the text.
		Parent: The blog (or tag, or ...).
		Superparent: The blog.
		"""
	__storm_table__ = "blogentry"
	_discriminator = 109

	title = Unicode()
	text = Unicode()

	def __init__(self,parent):
		self.owner = current_request.user
		self.parent = parent
		self.superparent = parent
		
	@property
	def data(self):
		return """\
Titel: %s

%s
""" % (self.title,self.text)

	def html_edit(self):
		form = BlogEntryForm(current_request.form)
		form.id = self.id
		if current_request.method == 'POST' and form.validate():
			form.text.data = form.text.data.replace("\r","")
			d = self.data
			self.title = form.title.data
			self.text = form.text.data
			if self.data != d:
				flash(u"Änderung gespeichert.", True)
				self.record_change(d)
			else:
				flash(u"Daten sind unverändert.")

			return redirect(url_for("pybble.views.view_oid", oid=self.oid()))
		
		elif current_request.method == 'GET':
			form.title.data = self.title
			form.text.data = self.text

		return render_template('blog/editentry.html', obj=self, form=form, name=form.title.data, title_trace=[self.title,"Edit Blog Entry"])

	def html_view(obj, **args):
		try:
			n = obj.parent.name
		except AttributeError:
			n = None
		return render_my_template(current_request, obj=obj, detail=TM_DETAIL_PAGE, title_trace=([obj.title, obj.parent.name] if n else [obj.title]), **args);

	@classmethod
	def html_new(cls,parent,name=None):
		current_request.user.will_add(parent,new_discr=cls)

		form = BlogEntryForm(current_request.form)
		if current_request.method == 'POST' and form.validate():
			form.text.data = form.text.data.replace("\r","")
			obj = cls(parent)
			obj.title = form.title.data
			obj.text = form.text.data

			flash(u"Daten gespeichert.", True)
			obj.record_creation()
			return redirect(url_for("pybble.views.view_oid", oid=obj.oid()))
		
		elif current_request.method == 'GET':
			form.title.data = name

		return render_template('blog/newentry.html', parent=parent, form=form, name=form.title.data, title_trace=["new","Blog Entry"])


