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

__ALL__ = ("Bookstore","Book","BookWant")

TEMPLATES = ("edit.html","new.html","editstore.html","newstore.html", \
	"newwant.html","delwant.html")

## System init code
def initsite(replace_templates):
	pass
	
class StoreForm(Form):
	name = TextField('Name', [validators.required(msg=u"Der Name fehlt"), validators.length(min=3, max=250)])
	info = TextField('Info', [validators.required(msg=u"Der Infotext fehlt"), validators.length(min=3, max=250)])


## Database mods
class Bookstore(Object):
	"""\
		This represents a place where books are kept.
		Owner: Whoever created the thing.
		"""
	__storm_table__ = "bookstore"
	_discriminator = 105

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
		form = StoreForm(current_request.form)
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

		return render_template('books/editstore.html', obj=self, form=form, name=form.name.data, title_trace=[self.name,"Bookstore"])

	@classmethod
	def html_new(cls,parent,name=None):
		current_request.user.will_add(parent,new_discr=cls)

		form = StoreForm(current_request.form)
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

		return render_template('books/newstore.html', parent=parent, form=form, name=form.name.data, title_trace=["new","Bookstore"])


class BookForm(Form):
	title = TextField('Titel', [validators.required(msg=u"Kein Buch ohne Titel!"), validators.length(min=3, max=250)])
	author = TextField('Autor', [validators.required(msg=u"Kein Buch ohne Autor(en)!"), validators.length(min=3, max=250)])
	upc = TextField('UPC', [validators.optional(), validators.length(min=10, max=15)])
	info = TextAreaField('Info', [validators.required(msg=u"Eine kurze Info zu diesem Buch muss sein."), validators.length(min=30)])

class Book(Object):
	"""\
		This represents a book.
		Owner: The person who owns the book.
		Parent: The bookstore.
		Superparent: Whoever currently has the book physically.
		"""
	__storm_table__ = "books"
	_discriminator = 106

	title = Unicode()
	author = Unicode()
	upc = RawStr()
	info = Unicode()

	def __init__(self,parent):
		self.owner = current_request.user
		self.parent = parent
		self.superparent = current_request.user
		
	@property
	def wanted(self):
		b = self.superparent
		while True:
			try:
				b = db.get_by(BookWant, parent=self,superparent=b)
			except NoResult:
				return
			else:
				yield b

	@property
	def data(self):
		return """\
UPC: %s
Titel: %s
Autor: %s

%s
""" % (self.upc,self.title,self.author,self.info)

	def html_edit(self):
		form = BookForm(current_request.form)
		form.id = self.id
		if current_request.method == 'POST' and form.validate():
			form.info.data = form.info.data.replace("\r","")
			d = self.data
			self.upc = str(form.upc.data)
			self.title = form.title.data
			self.author = form.author.data
			self.info = form.info.data
			if self.data != d:
				flash(u"Änderung gespeichert.", True)
				self.record_change(d)
			else:
				flash(u"Daten sind unverändert.")

			return redirect(url_for("pybble.views.view_oid", oid=self.oid()))
		
		elif current_request.method == 'GET':
			form.upc.data = self.upc
			form.title.data = self.title
			form.author.data = self.author
			form.info.data = self.info

		return render_template('books/edit.html', obj=self, form=form, name=form.title.data, title_trace=[self.title,"Edit Book"])

	def html_view(obj, **args):
		try:
			n = obj.parent.name
		except AttributeError:
			n = None
		return render_my_template(current_request, obj=obj, detail=TM_DETAIL_PAGE, title_trace=([obj.title, obj.parent.name] if n else [obj.title]), **args);

	@classmethod
	def html_new(cls,parent,name=None):
		current_request.user.will_add(parent,new_discr=cls)

		form = BookForm(current_request.form)
		if current_request.method == 'POST' and form.validate():
			form.info.data = form.info.data.replace("\r","")
			obj = cls(parent)
			obj.upc = str(form.upc.data)
			obj.title = form.title.data
			obj.author = form.author.data
			obj.info = form.info.data

			flash(u"Daten gespeichert.", True)
			obj.record_creation()
			return redirect(url_for("pybble.views.view_oid", oid=obj.oid()))
		
		elif current_request.method == 'GET':
			form.title.data = name

		return render_template('books/new.html', parent=parent, form=form, name=form.title.data, title_trace=["new","Bookstore"])


class BookWant(Object):
	"""\
		This represents a wish to get a book.
		Owner: The person who wants the book.
		Parent: The book.
		Superparent: The previous owner, who should send the book onwards.
		"""
	__storm_table__ = "bookwant"
	_discriminator = 107

	requested = DateTime(default_factory=datetime.utcnow)

	def __init__(self, book):
		self.owner = current_request.user
		self.parent = book
		self.superparent = book.superparent
		while True:
			try:
				b = db.get_by(BookWant, parent=book,superparent=self.superparent)
			except NoResult:
				break
			else:
				self.superparent = b
		
	def html_delete(self):
		book=self.parent
		if current_request.method == 'POST':
			try:
				b = db.get_by(BookWant, parent=book,superparent=self.superparent)
			except NoResult:
				pass
			else:
				b.superparent = self.superparent
			self.record_deletion()
			flash("Der Ausleihwunsch wurde gelöscht.")
			return redirect(url_for("pybble.views.view_oid", oid=parent.oid()))
		return render_template('books/delwant.html', book=self.parent, title_trace=[self.parent.title,"Not Wanted"])
		
	@classmethod
	def html_new(cls,parent,name=None):
		current_request.user.will_add(parent,new_discr=cls)

		if parent.superparent == current_request.user:
			flash("Du hast das Buch doch gerade!",False)
			return redirect(url_for("pybble.views.view_oid", oid=parent.oid()))
		try:
			b = db.get_by(BookWant, parent=parent, superparent=current_request.user)
		except NoResult:
			pass
		else:
			flash("Du hast das Buch am "+str(b.requested)+" vorbestellt.",False)
			return redirect(url_for("pybble.views.view_oid", oid=parent.oid()))

		if current_request.method == 'POST':
			obj = cls(parent)
			obj.record_creation()
			if self.superparent != parent.superparent:
				flash("Dein Ausleihwunsch wurde weitergeleitet.",True)
			else:
				flash("Dein Ausleihwunsch ist vorgemerkt.")
			return redirect(url_for("pybble.views.view_oid", oid=parent.oid()))
		
		b = parent.superparent
		n = 0
		while True:
			try:
				b = db.get_by(BookWant, parent=parent, superparent=b.superparent)
			except NoResult:
				break
			else:
				n += 1

		return render_template('books/newwant.html', book=parent, owner=b.superparent, n=n, title_trace=[parent.title,"Wanted"])


