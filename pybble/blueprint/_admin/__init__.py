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

from flask import Module, request, redirect, url_for, render_template, abort
from formalchemy import FieldSet

from pybble.blueprint import BaseBlueprint
from pybble.core.models.objtyp import ObjType
from pybble.core.route import Exposer
from pybble.core.db import NoData
expose = Exposer()

models = {}

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
	opts = [fs.id.readonly(),fs.objtyp.readonly()]
	hide = [fs.children,fs.superchildren,fs.owned]
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
	if model_key:
		try: data = model.q.get_by(id=model_key)
		except NoData: abort(404)
	else:
		data = model

	if model_key:
		obj = model.q.get_by(id=int(model_key))
		fields = FieldSet(obj)
	else:
		obj = None
		fields = FieldSet(model)

	fields = FieldSet(data)
	_fixup_fs(fields,int(model_key),attrs)

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

