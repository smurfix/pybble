# -*- coding: utf-8 -*-

from werkzeug import redirect
from pybble.database import db, NoResult
from pybble.models import Object,User,obj_get, VerifierBase, Verifier
from sqlalchemy import Column, Unicode, Integer, ForeignKey, String, Boolean
from wtforms import Form,TextField,validators
from wtforms.validators import ValidationError
from pybble.utils import current_request
from pybble.render import url_for, render_template, valid_obj, valid_admin, send_mail
from pybble.flashing import flash
from jinja2 import Markup
from pybble import _settings as settings

import re,sys

__ALL__ = ("action_verein", "Verein", "Mitglied")

TEMPLATES = ("edit.html","new.html","newuser.html","verify_email.txt")

## preload code
def action_verein():
	"""Verein extension loaded."""
	print "Test"

## System init code
def initsite(replace_templates):
	VerifierBase.register("jverein","pybble.addon.jverein.verifier")
	
if settings.DATABASE_TYPE == "sqlite":
	dbname_re = re.compile(r"^[a-zA-Z][_a-zA-Z0-9]+$")
else:
	dbname_re = re.compile(r"^[a-zA-Z][_a-zA-Z0-9]+\.[a-zA-Z][_a-zA-Z0-9]+$")
def sel_ok(form, field):
	if not dbname_re.match(field.data):
		raise ValidationError("Dies ist kein Datenbankname")
	try:
		r = db.session.execute("select count(id) from %s where email is not null and austritt is null and kuendigung is null" % (field.data,))
	except NoResult:
		raise ValidationError("Diese Tabelle ist leer")
	except Exception,e:
		print >>sys.stderr,repr(e)
		raise ValidationError("Problem beim Validieren des Datenbankzugriffs")
	else:
		pass

## Verein: the base
class VereinForm(Form):
	name = TextField('Name', [validators.length(min=3, max=250)])
	database = TextField('Database', [validators.length(min=3, max=30), sel_ok])

class Verein(Object):
	"""\
		parent: site
		Owner: Whoever created the thing.
		"""
	__tablename__ = "verein"
	__table_args__ = ({'useexisting': True})
	__mapper_args__ = {'polymorphic_identity': 102}
	q = db.session.query_property(db.Query)
	id = Column(Integer, ForeignKey('obj.id',name="verein_id"), primary_key=True,autoincrement=False)

	name = Column(Unicode(250))
	database = Column(String(30))

	def __init__(self,parent, name,database):
		self.owner = current_request.user
		self.parent = current_request.site
		self.name = name
		self.database = database
		
	@property
	def data(self):
		return """\
Name: %s
database: %s
""" % (self.name,self.database)

	def html_edit(self):
		form = VereinForm(current_request.form)
		form.id = self.id
		if current_request.method == 'POST' and form.validate():
			if self.name != form.name.data or self.database != form.database.data:
				self.record_change()
				self.name = form.name.data
				self.database = form.database.data

			return redirect(url_for("pybble.views.view_oid", oid=self.oid()))
		
		elif current_request.method == 'GET':
			form.name.data = self.name

		return render_template('jverein/edit.html', obj=self, form=form, name=form.name.data, title_trace=[self.name,"Verein"])

	class _mitglied_data(object):
		def __init__(self,parent, k,v):
			if isinstance(v,unicode):
				v = repr(v.encode("utf-8"))
			elif isinstance(v,(int,long)):
				v = str(v)
				v = v.rstrip("L")
			else:
				v = repr(v)
			print "R",k,v
			sel="id,email,vorname,name"
			r = db.session.execute("select %s from %s where `%s` = %s" % (sel,parent.database, k,v)).fetchone()
			if r is None:
				raise NoResult
			for s,t in zip(sel.split(","),r):
				setattr(self,s,t)

	def mitglied_data(self, k,v):
		return self._mitglied_data(self, k,v)
	
	@property
	def num_mitglieder(self):
		return db.session.execute("select count(id) from %s where email is not null and austritt is null and kuendigung is null" % (self.database,)).fetchone()[0]

	@property
	def num_reg_mitglieder(self):
		return Mitglied.q.filter_by(parent=self, aktiv=True).count()

	@classmethod
	def html_new(cls,parent,name=None):
		current_request.user.will_add(parent,new_discr=cls)

		form = VereinForm(current_request.form)
		if current_request.method == 'POST' and form.validate():
			obj = cls(parent, form.name.data,form.database.data)

			obj.record_creation()
			return redirect(url_for("pybble.views.view_oid", oid=obj.oid()))
		
		elif current_request.method == 'GET':
			form.name.data = name

		return render_template('jverein/new.html', parent=parent, form=form, name=form.name.data, title_trace=["neu","Verein"])

## Mitglied: membership

def verein_mail(form, field):
	try:
		m = form.parent.mitglied_data("email",field.data)
	except NoResult:
		raise ValidationError("Diese Adresse ist nicht bekannt")
	form.vid = m.id
	
def verein_unassoc(form, field):
	try:
		m = Mitglied.q.get_by(parent=form.parent, owner=obj_get(field.data))
	except NoResult:
		pass
	else:
		if m.aktiv:
			raise ValidationError("Du bist schon Mitglied!")
		else:
			raise ValidationError("Du musst dich nur noch freischalten!")

class MitgliedForm(Form):
	user = TextField('User', [valid_obj,valid_admin, verein_unassoc])
	email = TextField('Email', [validators.length(min=3, max=150), verein_mail])

class Mitglied(Object):
	"""\
		parent: Verein
		Owner: associated user
		"""
	__tablename__ = "verein_member"
	__table_args__ = ({'useexisting': True})
	__mapper_args__ = {'polymorphic_identity': 103}
	q = db.session.query_property(db.Query)
	id = Column(Integer, ForeignKey(Object.id,name="vereinmember_id"), primary_key=True,autoincrement=False)

	mitglied_id = Column(Integer)
	aktiv = Column(Boolean, default=False)

	@property
	def group(self):
		return self.parent

	@property
	def record(self):
		assert self.mitglied_id
		return self.parent.mitglied_data("id",self.mitglied_id)

	@classmethod
	def html_new(cls,parent,name=None):
		current_request.user.will_add(parent,new_discr=cls)

		form = MitgliedForm(current_request.form)
		form.parent = parent
		if not current_request.user.can_admin(parent):
			del form.user

		if current_request.method == 'POST' and form.validate():
			obj = cls()
			obj.mitglied_id = form.vid
			obj.parent = parent
			obj.owner = obj_get(form.user.data) if hasattr(form,"user") else current_request.user

			obj.record_creation()
			if obj.record.email == current_request.user.email:
				obj.aktiv = True
				flash(u"Du bist jetzt als Mitglied aktiviert.", True)
				return redirect(url_for("pybble.views.mainpage"))
			else:
				flash(Markup(u"Wir haben soeben eine Bestätigungs-Email an dich geschickt. <br />" + \
					u"Klicke auf den darin enhaltenen Link oder tippe den Bestätigungscode hier ein."))

				v = verifier.new(obj)
				db.session.add(v)
				v.send()
				return redirect(url_for("pybble.confirm.confirm"))
		
		elif current_request.method == 'GET':
			u = current_request.user.last_visited(User) or current_request.user
			if hasattr(form,"user"): form.user.data = u.oid()
			form.email.data = u.email

		return render_template('jverein/newuser.html', parent=parent, form=form, title_trace=["Neumitglied","Verein"])

Object.new_member_rule(Mitglied.q.filter_by(aktiv=True), "owner","parent")

###
### Confirm email 
###

class verifier(object):
	@staticmethod
	def new(obj):
		v=Verifier("jverein",obj)
		return v

	@staticmethod
	def send(verifier):
		from pybble.confirm import confirm
		m=verifier.parent
		send_mail(m.record.email, 'jverein/verify_email.txt', m=m.record,
		          user=m.owner, code=verifier.code, parent=m.parent,
		          link=url_for("pybble.confirm.confirm", code=verifier.code, _external=1),
				  page=url_for("pybble.confirm.confirm", _external=1))
	
	@staticmethod
	def entered(verifier):
		obj = verifier.parent
		if not obj.aktiv:
			obj.aktiv = True
			return redirect(url_for("pybble.confirm.confirmed",oid=verifier.oid()))
		flash(u"Du bist bereits als Mitglied aktiviert.")
		return redirect(url_for("pybble.views.mainpage"))

	@staticmethod
	def confirmed(verifier):
		flash(u"Du bist jetzt als Mitglied aktiviert.", True)

		return redirect(url_for("pybble.views.mainpage"))

