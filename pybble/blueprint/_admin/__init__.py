# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, division, unicode_literals
##
## This is part of Pybble, a WMS (Whatever Management System) based on
## Jinja2/Haml, Werkzeug, Flask, and Optimism.
##
## Pybble is Copyright © 2009-2014 by Matthias Urlichs <matthias@urlichs.de>,
## it is licensed under the GPLv3. See the file `README.md` for details,
## including an optimistic statements by the author.
##
## This paragraph is auto-generated and may self-destruct at any time,
## courtesy of "make update". The original is in ‘utils/_boilerplate.py’.
## Thus, please do not remove the next line, or insert any blank lines.
##BP

##
## This is the administrative front-end for your site.
## 
## You typically add it under /admin.
## 

from flask import Module, request, redirect, url_for, abort
from formalchemy import FieldSet, helpers as fa_h
from formalchemy.fields import FieldRenderer

from pybble.blueprint import BaseBlueprint
from pybble.core.utils import attrdict
from pybble.core.models.objtyp import ObjType
from pybble.core.models.object import Object,ObjRefComposer
from pybble.core.route import Exposer
from pybble.core.db import NoData, db
from pybble.render import render_template
expose = Exposer()

models = {}

class ObjRefRenderer(FieldRenderer):
	"""Render as a text field, for now."""
	def render(self, **kwargs):
		return fa_h.text_field(self.name, value=self.value, maxlength=20, **kwargs)
	def stringify_value(self,v,as_html=False):
		return v.oid
	def deserialize(self):
		obj = self.params.getone(self.name)
		if obj in ("","-"):
			return None
		return Object.by_oid(obj)
FieldSet.default_renderers[ObjRefComposer] = ObjRefRenderer

class Blueprint(BaseBlueprint):
	"""\
This is a simple admin blueprint for Pybble's object view.
"""
	_name = "admin"

	def setup(self):
		super(Blueprint,self).setup()
		expose.add_to(self)

		for d in ObjType.q.all():
			try:
				models[d.name] = d.mod
			except Exception as e:
				models[d.name] = str(e)

@expose('/')
def index():
	return render_template('_admin/index.html', models=models)

@expose('/<model_slug>')
def object_list(model_slug):
	if model_slug not in models:
		abort(404)
	model = models[model_slug]
	field_names = model.__table__.columns.keys()
	primary_key = model.__table__.primary_key.columns.keys()[0]
	objects = model.q.all()
	context = {
		'model_slug': model_slug,
		'field_names': field_names,
		'primary_key': primary_key,
		'objects': objects,
	}
	return render_template('_admin/list.html', **context)

def _fixup_fs(fs,id,attrs):
	"""Change all fields that have been passed in **attrs to read-only"""
	opts = [fs.id.readonly()]
	hide = [] #[fs.children,fs.superchildren,fs.owned]
	if hasattr(fs,'config'): hide.append(fs.config)
	if id:
		fs.configure(pk=True)
	for k in attrs:
		opts.append(getattr(fs,k).readonly())
	fs.configure(options=opts, exclude=hide)

@expose('/<model_slug>/edit/<int:model_key>', methods=['GET', 'POST'])
@expose('/<model_slug>/new', methods=['GET', 'POST'], endpoint='object_new')
def object_edit(model_slug, model_key=None, **attrs):
	if model_slug not in models:
		abort(404)
	model = models[model_slug]
	sk = attrdict()
	if model_key:
		try: data = model.q.get_by(id=model_key)
		except NoData: abort(404)
	else:
		data = model
		sk.session = db

	if model_key:
		obj = model.q.get_by(id=int(model_key))
	else:
		obj = None

	fields = FieldSet(data, **sk)
	_fixup_fs(fields,model_key,attrs)

	if request.method == 'POST':
		fields.rebind(data=request.form)
		if fields.validate():
			fields.sync()
			next_url = url_for('_admin.object_list', model_slug=model_slug)
			return redirect(next_url)
	context = {
		'model_slug': model_slug,
		'model': model,
		'fields': fields,
	}
	template_name = '_admin/edit.html' if model_key else '_admin/new.html'
	return render_template(template_name, **context)

