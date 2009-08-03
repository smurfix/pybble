# -*- coding: utf-8 -*-

from werkzeug import redirect, import_string, Response
from werkzeug.routing import BuildError
from werkzeug.exceptions import NotFound
from pybble.render import render_template, render_my_template, \
	expose, url_for
from pybble.models import TemplateMatch, TM_DETAIL_PAGE, obj_get, obj_class, MAX_BUILTIN, TM_DETAIL_SNIPPET, TM_DETAIL_HIERARCHY, Site, Object, \
	Comment,Breadcrumb
from pybble.database import db,NoResult
from wtforms import Form, HiddenField, TextField, validators
from pybble.flashing import flash
from storm.locals import And
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
def mainpage(request):
	return render_my_template(request, request.site)

@expose('/tree')
@expose('/tree/<oid>')
def view_tree(request, oid=None):
	if oid is None:
		obj = request.site
	else:
		obj = obj_get(oid)

	request.user.will_admin(obj)
	if obj is request.site:
		title_trace=["Objects"]
	else:
		title_trace=[unicode(obj),"Objects"]

	p,s,o,d = obj.pso
	return render_template('tree.html', obj=obj, obj_parent=p, obj_superparent=s, obj_owner=o, obj_deleted=d,
	                                    title_trace=title_trace)

@expose('/edit/<oid>')
def edit_oid(request, oid):
	obj=obj_get(oid)

	try: return tryAddOn(obj,"html_edit")
	except NoRedir: pass

	v = import_string("pybble.part.%s.editor" % (obj.classname.lower(),))
	if not getattr(v,"no_check_perm",None):
		request.user.will_write(obj)
	return v(request, obj)

@expose('/new/<oid>')
@expose('/new/<oid>/<discr>')
@expose('/new/<oid>/<discr>/<name>')
def new_oid(request, oid, discr=None, name=None):
	obj=obj_get(oid)
	if discr is None:
		discr = obj.discriminator
	request.user.will_add(obj,new_discr=discr)
	cls = obj_class(discr)
	if hasattr(cls,"html_new"):
		v = cls.html_new
		vc = v
	else:
		v = import_string("pybble.part.%s.newer" % (cls.__name__.lower(),))
		def vc(**args):
			return v(request, **args)

	args = {}
	fn = inspect.getargspec(v)[0]
	if "name" in fn: args["name"]=name
	if "parent" in fn: args["parent"]=obj
	return vc(**args)

@expose('/copy/<oid>/<parent>')
def copy_oid(request, oid, parent):
	"""Create a copy of <oid> which lives beyond / controls / whatever <parent>."""
	obj=obj_get(oid)
	parent=obj_get(parent)

	try: return tryAddOn(obj,"html_copy", parent=parent)
	except NoRedir: pass

	request.user.will_add(parent,new_discr=obj.discriminator)
	if hasattr(obj,"html_edit"):
		return cls.html_edit(parent=parent)
	else:
		v = import_string("pybble.part.%s.editor" % (obj.classname.lower(),))
		return v(request, obj=obj,parent=parent)


class DeleteForm(Form):
	next = HiddenField("next URL")
	comment = TextField('Grund', [validators.length(min=3, max=200)])

@expose('/delete/<oid>')
def delete_oid(request, oid):
	obj=obj_get(oid)
	request.user.will_delete(obj)

	try: return tryAddOn(obj,"html_delete")
	except NoRedir: pass

	form = DeleteForm(request.form, prefix='delete')
	if request.method == 'POST' and form.validate():
		obj.record_deletion(form.comment.data)

		flash(u"%s (%s) wurde gelöscht" % (unicode(obj),obj.oid()), True)
		if form.next.data:
			return redirect(form.next.data)
		elif obj.parent:
			return redirect(url_for("pybble.views.view_oid", oid=obj.parent.oid()))
		else:
			return redirect(url_for("pybble.views.mainpage"))

	return render_template('delete.html', form=form, title_trace=[u"Löschen"], obj=obj)

def split_details(request,obj, details):
	for d in details.split("-"):
		try:
			o = db.get(BaseObject, int(d))
			if o != obj.superparent:
				pass
			request.user.will_read(o)
			yield o
		except Exception,e:
			print >>sys.stderr,e
			pass

def split_details_aux(request,obj,details):
	det = set()
	aux = set()

	if isinstance(details,basestring):
		details = split_details(request,obj,details)

	for o in details:
		if o in det:
			continue
		aux.add(o.id)
		det.add(o.id)
		o = o.parent
		while o and o != obj and o not in aux:
			aux.add(o)
			o = o.parent
	return det,aux


@expose('/view/<oid>/<details>')
def view_oid_exp(request, oid, details):
	obj = obj_get(oid)
	d,a = split_details_aux(request,obj,details)
	print >>sys.stderr,"D A",obj,details,d,a
	return view_oid(request, oid, details=d, aux=a)

@expose('/view/<oid>')
def view_oid(request, oid, **args):
	obj = obj_get(oid)
	request.user.will_read(obj)

	if "details" not in args:
		dv = [ Comment.superparent_id == obj.id ]
		try:
			bc = db.get_by(Breadcrumb, parent=obj, owner=request.user)
		except NoResult:
			pass
		else:
			if bc.last_visited:
				dv.append(Comment.added > bc.last_visited)
		d = db.store.find(Comment, And(*dv))
		d,a = split_details_aux(request,obj,d)
		args["details"] = d
		args["aux"] = a

	try: return tryAddOn(obj,"html_view", **args)
	except NoRedir: pass

	try:
		name = getattr(obj,"name",None)
		v = import_string("pybble.part.%s.viewer" % (obj.classname.lower(),))
	except Exception,e:
		return render_my_template(request, obj=obj, detail=TM_DETAIL_PAGE, **args);
	else:
		try:
			if not args and (not isinstance(obj,Site) or obj == request.site):
				return redirect(url_for('pybble.part.%s.viewer' % (obj.classname.lower(),),**args))
		except BuildError:
			pass
		fn = inspect.getargspec(v)[0]
		if "obj" in fn: args["obj"]=obj
		if "oid" in fn: args["oid"]=oid
		if "name" in fn: args["name"]=name
		if "details" in fn: args["details"]=details
		if "aux" in fn: args["aux"]=aux
		return v(request, **args)

@expose('/detail/<oid>')
def detail_oid(request, oid):
	obj = obj_get(oid)
	request.user.will_read(obj)
	p,s,o,d = obj.pso
	title_trace=[unicode(obj),"Info"]
	return render_template("detail.html", obj=obj, obj_parent=p, obj_superparent=s, obj_owner=o, obj_deleted=d, title_trace=title_trace)

@expose('/last_visited')
def last_visited(request):
	return render_template("last_visited.html", q=request.user.all_visited(), title_trace=[u"zuletzt besucht"])
	

@expose('/snippet/<t>')
def view_snippet(request, t):
	oid = request.values["dir"]
	if '/' in oid:
		oid,discr = oid.split('/',1)
	else:
		discr = request.values.get("discr",None)
	try:
		t = int(t)
	except ValueError:
		if discr:
			return view_snippet2(request, t, oid, int(discr))
		else:
			return view_snippet1(request, t, oid)
	else:
		c = obj_class(t)
		obj = obj_get(oid)
		if discr:
			res = []
			discr = int(discr)
			for o in obj.all_children(discr):
				sub = o.has_children(discr)
				res.append(render_my_template(request, o, detail=TM_DETAIL_SNIPPET, discr=t, sub=sub, mimetype=None))
			return Response("\n".join(res), mimetype="text/html")
		else:
			sub = db.filter_by(c, parent=obj)
			return render_my_template(request, obj, detail=TM_DETAIL_SNIPPET, discr=t, sub=sub)

@expose('/snippet/<t>/<oid>')
def view_snippet1(request, t, oid):
	obj = obj_get(oid)
	if t == "parent":
		sub = obj.discr_children
	elif t == "superparent":
		sub = obj.discr_superchildren
	elif t == "owner":
		sub = obj.discr_slaves
	elif t == "hierarchy":
		return render_my_template(request, obj, detail=TM_DETAIL_HIERARCHY)
		
	else:
		raise NotFound()

	return render_template("snippet1.html", obj=obj, t=t, sub=list(sub))

@expose('/snippet/<t>/<oid>/<discr>')
def view_snippet2(request, t, oid, discr):
	c = obj_class(discr)
	obj = obj_get(oid)
	if t == "parent":
		sub = db.filter_by(c, parent=obj)
		what = "has_children"
	elif t == "superparent":
		sub = db.filter_by(c, superparent=obj)
		what = "has_superchildren"
	elif t == "owner":
		sub = db.filter_by(c, owner=obj)
		what = "has_slaves"
	else:
		raise NotFound()
	return render_template("snippet2.html", obj=obj, t=t, discr=discr, sub=sub, what=what, cls=c, count=sub.count())

def not_found(request, url=None):
    return render_template('not_found.html', title_trace=[u"Seite nicht gefunden"])

def not_allowed(request, obj, perm=None):
    return render_template('not_allowed.html', title_trace=[u"Keine Berechtigung"], obj=obj, perm=perm)

def not_able(request, obj, perm=None):
    return render_template('not_able.html', title_trace=[u"Das geht nicht"], obj=obj, perm=perm)

