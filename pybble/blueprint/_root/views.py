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

from flask import request, url_for, flash, current_app, Response, render_template

from werkzeug import redirect, import_string
from werkzeug.routing import BuildError
from werkzeug.exceptions import NotFound

from wtforms import Form, HiddenField, TextField, validators

from pybble.render import render_my_template
from pybble.core.models._const import TM_DETAIL_PAGE, TM_DETAIL_SNIPPET, TM_DETAIL_HIERARCHY
from pybble.core.models.object import Object
from pybble.core.models.objtyp import ObjType
from pybble.core.models.template import TemplateMatch
from pybble.core.models.tracking import Breadcrumb,Delete
from pybble.core.models.site import Site
from pybble.core.db import db,NoData
from pybble.globals import current_site
from ._base import expose
from .part import ObjEditor
expose = expose.sub("views")

import logging
logger = logging.getLogger('pybble._root.views')

import inspect,sys

@expose("/")
def mainpage():
	return render_my_template(current_site)

@expose('/tree')
@expose('/tree/<oid>')
def view_tree(oid=None):
	if oid is None:
		obj = current_site
	else:
		obj = Object.by_oid(oid)

	request.user.will_admin(obj)
	if obj == current_site:
		title_trace=["Objects"]
	else:
		title_trace=[unicode(obj),"Objects"]

	return render_template('tree.html', obj=obj, title_trace=title_trace)

@expose('/edit/<oid>', methods=('POST','GET'))
def edit_oid(oid):
	from .part import ObjEditor
	obj=Object.by_oid(oid)
	if not getattr(v,"no_check_perm",None):
		request.user.will_write(obj)
	ed = ObjEditor(obj)
	return ed.editor()

@expose('/new/<oid>', methods=('POST','GET'))
@expose('/new/<oid>/<objtyp>', methods=('POST','GET'))
@expose('/new/<oid>/<objtyp>/<name>', methods=('POST','GET'))
def new_oid(oid, objtyp=None, name=None):
	obj=Object.by_oid(oid)
	if objtyp is None:
		objtyp = obj.type
	else:
		try: objtyp = int(objtyp)
		except ValueError: pass
		objtyp = ObjType.get(objtyp)
	request.user.will_add(obj,new_objtyp=objtyp)

	ed = ObjEditor(objtyp)
	args = {}
	if name is not None: args["name"]=name
	args["parent"]=obj
	return ed.editor(**args)

@expose('/copy/<oid>/<parent>')
def copy_oid(oid, parent):
	"""Create a copy of <oid> which lives beyond / controls / whatever <parent>."""
	obj=Object.by_oid(oid)
	parent=Object.by_oid(parent)

	try: return tryAddOn(obj,"html_copy", parent=parent)
	except NoRedir: pass

	request.user.will_add(parent,new_objtyp=obj.objtyp)
	if hasattr(obj,"html_edit"):
		return cls.html_edit(parent=parent)
	else:
		v = import_string("pybble.blueprint._root.part.%s.editor" % (obj.type.name.lower(),))
		return v(obj=obj,parent=parent)

class DeleteForm(Form):
	next = HiddenField("next URL")
	comment = TextField('Grund', [validators.required(u"Grund der Löschung?"), validators.length(min=3, max=200)])

@expose('/delete/<oid>', methods=('POST','GET'))
def delete_oid(oid):
	obj=Object.by_oid(oid)
	request.user.will_delete(obj)

	try: return tryAddOn(obj,"html_delete")
	except NoRedir: pass

	form = DeleteForm(request.form, prefix='delete')
	if request.method == 'POST' and form.validate():
		Delete.new(form.comment.data)

		flash(u"%s (%s) wurde gelöscht" % (unicode(obj),obj.oid), True)
		if form.next.data:
			return redirect(form.next.data)
		elif obj.parent:
			return redirect(url_for("pybble.views.view_oid", oid=obj.parent.oid))
		else:
			return redirect(url_for("pybble.views.mainpage"))

	return render_template('delete.html', form=form, title_trace=[u"Löschen"], obj=obj)

def split_details(obj, details):
	if details == "all":
		for o in db.filter_by(Comment, superparent_id = obj.id):
			yield o

	for d in details.split("-"):
		try:
			o = db.get(BaseObject, int(d))
			if o != obj.superparent:
				pass
			request.user.will_read(o)
			yield o
		except Exception as e:
			logger.err("ERROR",e)
			pass

def split_details_aux(obj,details):
	det = set()
	aux = set()

	if isinstance(details,basestring):
		details = split_details(obj,details)

	for o in details:
		if o in det:
			continue
		aux.add(o.id)
		det.add(o.id)
		o = o.parent
		while o and o != obj and o not in aux:
			aux.add(o.id)
			o = o.parent
	logger.debug("DET",det,"AUX",aux)
	return det,aux

@expose('/view/<oid>/<details>')
def view_oid_exp(oid, details):
	obj = Object.by_oid(oid)
	d,a = split_details_aux(obj,details)
	logger.debug("D A",obj,details,d,a)
	return view_oid(oid, details=d, aux=a)

@expose('/view/<oid>')
def view_oid(oid, **args):
	obj = Object.by_oid(oid)
	request.user.will_read(obj)

	if "details" not in args:
		## The purpose of this code is to get any comments added since the
		## last visit on this page. Does not work well, and comments are
		## not yet ported anyway.
		#dv = [ Comment.superparent_id == obj.id ]
		#try:
		#	bc = Breadcrumb.q.get_by(parent=obj, owner=request.user)
		#except NoData:
		#	pass
		#else:
		#	if bc.last_visited:
		#		dv.append(Comment.added > bc.last_visited)
		#d = Comment.q.get(*dv)
		#d,a = split_details_aux(obj,d)
		#args["details"] = d
		#args["aux"] = a
		args["details"] = ()
		args["aux"] = ()

	return render_my_template(obj=obj, detail=TM_DETAIL_PAGE, **args);

@expose('/detail/<oid>')
def detail_oid(oid):
	obj = Object.by_oid(oid)
	request.user.will_read(obj)
	title_trace=[unicode(obj),"Info"]
	return render_template("detail.html", obj=obj, title_trace=title_trace)

@expose('/last_visited')
def last_visited():
	return render_template("last_visited.html", q=request.user.all_visited(), title_trace=[u"zuletzt besucht"])
	
@expose('/snippet/<oid>',methods=("GET","POST"))
@expose('/snippet/<oid>/<k>',methods=("GET","POST"))
def view_snippet(oid,k=None):
	"""Return a list of fields in this object, and references to it"""
	obj = Object.by_oid(oid)
	return render_template("snippet1.html", obj=obj, key=k, sub=list(obj.count_refs()))

@expose('/snippet/<oid>/<int:objtyp>/<k>',methods=("GET","POST"))
def view_snippet2(oid, objtyp,k):
	obj = Object.by_oid(oid)
	objtyp = ObjType.get(objtyp)
	
	sub=list(obj.get_refs(objtyp,k))
	return render_template("snippet2.html", cls=objtyp, obj=obj, sub=sub, k=k, count=len(sub))

def not_found(url=None):
	return render_template('not_found.html', title_trace=[u"Seite nicht gefunden"])

def not_allowed(obj, perm=None):
	return render_template('not_allowed.html', title_trace=[u"Keine Berechtigung"], obj=obj, perm=perm)

def not_able(obj, perm=None):
	return render_template('not_able.html', title_trace=[u"Das geht nicht"], obj=obj, perm=perm)

