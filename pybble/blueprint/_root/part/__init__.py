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

# object parts editor

from flask import Module, request, redirect, url_for, abort
from formalchemy import FieldSet, helpers as fa_h
from formalchemy.fields import FieldRenderer

from pybble.blueprint import BaseBlueprint
from pybble.globals import current_site
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

class ObjEditor(object):
	def __init__(self, obj, parent=None):
		self.obj = obj
		self.parent = parent

	def editor(self, template=None, done=None, **kw):
		fields = self.obj.fieldset(parent=self.parent)

		if request.method == 'POST':
			fields.rebind(data=request.form)
			if fields.validate():
				fields.sync()
				db.session.flush()
				if done is not None:
					return done()
				next_url = url_for('pybble.views.view_oid', oid=fields.model.oid)
				return redirect(next_url)

		if template is None:
			template = 'admin/new.html' if isinstance(self.obj,ObjType) else 'admin/edit.html'
		return render_template(template, fields=fields, obj=self.obj, _root=current_site, **kw)

