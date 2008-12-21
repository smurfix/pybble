# -*- coding: utf-8 -*-

from werkzeug import redirect
from pybble.database import db
from pybble.models import Object
from sqlalchemy import Column, Unicode, Integer, ForeignKey
from wtforms import Form,TextField,validators
from pybble.utils import current_request
from pybble.render import url_for, render_template

__ALL__ = ("action_demo","Demo")

TEMPLATES = ("edit.html","new.html")

## preload code
def action_demo():
	"""Demo extension loaded."""
	print "This is a demo extension."
	print "It doesn't do anything. Much."

## System init code
def initsite(replace_templates):
	pass
	
class EditForm(Form):
	name = TextField('Name', [validators.length(min=3, max=250)])


## Database mods
class Demo(Object):
	"""\
		Demonstration extension object, not to be doing anything much.
		Owner: Whoever created the thing.
		"""
	__tablename__ = "demo"
	__table_args__ = ({'useexisting': True})
	__mapper_args__ = {'polymorphic_identity': 101}
	q = db.session.query_property(db.Query)
	id = Column(Integer, ForeignKey('obj.id',name="comment_id"), primary_key=True,autoincrement=False)

	name = Column(Unicode(250))

	def __init__(self,parent):
		self.owner = current_request.user
		self.parent = parent
		self.superparent = current_request.site
		
	@property
	def data(self):
		return "Name: "+self.name

	def html_edit(self):
		form = EditForm(current_request.form)
		form.id = self.id
		if current_request.method == 'POST' and form.validate():
			if self.name != form.name.data:
				self.record_change()
				self.name = form.name.data

			return redirect(url_for("pybble.views.view_oid", oid=self.oid()))
		
		elif current_request.method == 'GET':
			form.name.data = self.name

		return render_template('demo/edit.html', obj=self, form=form, name=form.name.data, title_trace=[self.name,"Demo"])

	@classmethod
	def html_new(cls,parent,name=None):
		current_request.user.will_add(parent,new_discr=cls)

		form = EditForm(current_request.form)
		if current_request.method == 'POST' and form.validate():
			obj = cls(parent)
			obj.name = form.name.data

			obj.record_creation()
			return redirect(url_for("pybble.views.view_oid", oid=obj.oid()))
		
		elif current_request.method == 'GET':
			form.name.data = name

		return render_template('demo/new.html', parent=parent, form=form, name=form.name.data, title_trace=["neu","Demo"])

