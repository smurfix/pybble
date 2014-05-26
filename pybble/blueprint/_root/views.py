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
from pybble.core.models.tracking import Breadcrumb
from pybble.core.models.site import Site
from pybble.core.db import db,NoData
from pybble.globals import current_site
from ._base import expose
expose = expose.sub("views")

import logging
logger = logging.getLogger('pybble._root.views')

import inspect,sys

class NoRedir(BaseException):
	"""Dummy exception to signal that no add-on module is responsible"""
	pass

def tryAddOn(obj,req, **kw):
	try: hv = getattr(obj,"url_"+req)
	except AttributeError: pass
	else:
		try:
			hv = hv(**kw)
		except TypeError:
			pass
		else:
			if hv is not None:
				return redirect(hv)

	try: hv = getattr(obj,req)
	except AttributeError: pass
	else:
		return hv(**kw)
	
	raise NoRedir

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
	if obj is current_site:
		title_trace=["Objects"]
	else:
		title_trace=[unicode(obj),"Objects"]

	p,s,o,d = obj.pso
	return render_template('tree.html', obj=obj, obj_parent=p, obj_superparent=s, obj_owner=o, obj_deleted=d,
	                                    title_trace=title_trace)

@expose('/edit/<oid>', methods=('POST','GET'))
def edit_oid(oid):
	obj=Object.by_oid(oid)

	try: return tryAddOn(obj,"html_edit")
	except NoRedir: pass

	v = import_string("pybble.blueprint._root.part.%s.editor" % (obj.type.name.lower(),))
	if not getattr(v,"no_check_perm",None):
		request.user.will_write(obj)
	return v(obj)

@expose('/new/<oid>', methods=('POST','GET'))
@expose('/new/<oid>/<objtyp>', methods=('POST','GET'))
@expose('/new/<oid>/<objtyp>/<name>', methods=('POST','GET'))
def new_oid(oid, objtyp=None, name=None):
	obj=Object.by_oid(oid)
	if objtyp is None:
		objtyp = obj.objtyp
	request.user.will_add(obj,new_objtyp=objtyp)
	cls = ObjType.get(objtyp)
	if hasattr(cls,"html_new"):
		v = cls.html_new
		vc = v
	else:
		v = import_string("pybble.blueprint._root.part.%s.newer" % (cls.name.lower(),))
		def vc(**args):
			return v(**args)

	args = {}
	fn = inspect.getargspec(v)[0]
	if "name" in fn: args["name"]=name
	if "parent" in fn: args["parent"]=obj
	return vc(**args)

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
		obj.record_deletion(form.comment.data)

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

	try: return tryAddOn(obj,"html_view", **args)
	except NoRedir: pass

	try:
		name = getattr(obj,"name",None)
		v = import_string("pybble.blueprint._root.part.%s.viewer" % (obj.classname.lower(),))
	except Exception as e:
		return render_my_template(obj=obj, detail=TM_DETAIL_PAGE, **args);
	else:
		try:
			if not args and (not isinstance(obj,Site) or obj == current_site):
				return redirect(url_for('.part.%s.viewer' % (obj.classname.lower(),),**args))
		except BuildError:
			pass
		fn = inspect.getargspec(v)[0]
		if "obj" in fn: args["obj"]=obj
		if "oid" in fn: args["oid"]=oid
		if "name" in fn: args["name"]=name
		if "details" in fn: args["details"]=details
		if "aux" in fn: args["aux"]=aux
		return v(**args)

@expose('/detail/<oid>')
def detail_oid(oid):
	obj = Object.by_oid(oid)
	request.user.will_read(obj)
	p,s,o,d = obj.pso
	title_trace=[unicode(obj),"Info"]
	return render_template("detail.html", obj=obj, obj_parent=p, obj_superparent=s, obj_owner=o, obj_deleted=d, title_trace=title_trace)

@expose('/last_visited')
def last_visited():
	return render_template("last_visited.html", q=request.user.all_visited(), title_trace=[u"zuletzt besucht"])
	

@expose('/snippet/<t>',methods=("GET","POST"))
def view_snippet(t):
	oid = request.values["dir"]
	if '/' in oid:
		oid,objtyp = oid.split('/',1)
	else:
		objtyp = request.values.get("objtyp",None)
	try:
		t = int(t)
	except ValueError:
		if objtyp:
			return view_snippet2(t, oid, int(objtyp))
		else:
			return view_snippet1(t, oid)
	else:
		c = obj_class(t)
		obj = Object.by_oid(oid)
		if objtyp:
			res = []
			objtyp = int(objtyp)
			for o in obj.all_children(objtyp):
				sub = o.has_children(objtyp)
				res.append(render_my_template(o, detail=TM_DETAIL_SNIPPET, objtyp=t, sub=sub, mimetype=None))
			return Response("\n".join(res), mimetype="text/html")
		else:
			sub = db.filter_by(c, parent=obj)
			return render_my_template(obj, detail=TM_DETAIL_SNIPPET, objtyp=t, sub=sub)

@expose('/snippet/<t>/<oid>',methods=("GET","POST"))
def view_snippet1(t, oid):
	obj = Object.by_oid(oid)
	if t == "parent":
		sub = obj.objtyp_children
	elif t == "superparent":
		sub = obj.objtyp_superchildren
	elif t == "owner":
		sub = obj.objtyp_owned
	elif t == "hierarchy":
		return render_my_template(obj, detail=TM_DETAIL_HIERARCHY)
		
	else:
		raise NotFound()

	return render_template("snippet1.html", obj=obj, t=t, sub=list(sub))

@expose('/snippet/<t>/<oid>/<objtyp>',methods=("GET","POST"))
def view_snippet2(t, oid, objtyp):
	c = obj_class(objtyp)
	obj = Object.by_oid(oid)
	if t == "parent":
		sub = c.q.filter_by(parent=obj)
		what = "has_children"
	elif t == "superparent":
		sub = c.q.filter_by(superparent=obj)
		what = "has_superchildren"
	elif t == "owner":
		sub = c.q.filter_by(owner=obj)
		what = "has_owned"
	else:
		raise NotFound()
	return render_template("snippet2.html", obj=obj, t=t, objtyp=objtyp, sub=sub, what=what, cls=c, count=sub.count())

def not_found(url=None):
    return render_template('not_found.html', title_trace=[u"Seite nicht gefunden"])

def not_allowed(obj, perm=None):
    return render_template('not_allowed.html', title_trace=[u"Keine Berechtigung"], obj=obj, perm=perm)

def not_able(obj, perm=None):
    return render_template('not_able.html', title_trace=[u"Das geht nicht"], obj=obj, perm=perm)

