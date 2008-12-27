# -*- coding: utf-8 -*-

from werkzeug import redirect, import_string, Response
from werkzeug.routing import BuildError
from werkzeug.exceptions import NotFound
from pybble.render import render_template, render_my_template, \
	expose, url_for
from pybble.models import TemplateMatch, TM_DETAIL_PAGE, obj_get, obj_class, MAX_BUILTIN, TM_DETAIL_SNIPPET, TM_DETAIL_HIERARCHY
from pybble.database import db,NoResult
from wtforms import Form, HiddenField, TextField, validators
from pybble.flashing import flash

class NoRedir(BaseException):
	"""Dummy exception to signal that no add-on module is responsible"""
	pass

def tryAddOn(obj,req, **kw):
	try: hv = getattr(obj,"url_"+req)
	except AttributeError: pass
	else:
		hv = hv()
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
	return render_template('tree.html', obj=obj, title_trace=title_trace)

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
	if "name" in v.func_code.co_varnames: args["name"]=name
	if "parent"  in v.func_code.co_varnames: args["parent" ]=obj
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

@expose('/view/<oid>')
def view_oid(request, oid):
	obj = obj_get(oid)
	request.user.will_read(obj)
	request.user.visited(obj)

	try: return tryAddOn(obj,"html_view")
	except NoRedir: pass

	try:
		name = getattr(obj,"name",None)
		v = import_string("pybble.part.%s.viewer" % (obj.classname.lower(),))
	except Exception,e:
		return render_my_template(request, obj=obj, detail=TM_DETAIL_PAGE)
	else:
		args = {}
		if "name" in v.func_code.co_varnames: args["name"]=name
		if "oid"  in v.func_code.co_varnames: args["oid" ]=oid
		try:
			return redirect(url_for('pybble.part.%s.viewer' % (obj.classname.lower(),), **args))
		except BuildError:
			if "obj"  in v.func_code.co_varnames: args["obj" ]=obj
			return v(request, **args)

@expose('/detail/<oid>')
def detail_oid(request, oid):
	obj = obj_get(oid)
	request.user.will_read(obj)
	return render_template("detail.html", obj=obj)

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
			return view_snippet2(request, t, oid,discr)
		else:
			return view_snippet1(request, t, oid)
	else:
		c = obj_class(t)
		obj = obj_get(oid)
		if discr:
			res = []
			for o in obj.all_children(discr):
				sub = o.has_children(discr)
				res.append(render_my_template(request, o, detail=TM_DETAIL_SNIPPET, discr=t, sub=sub, mimetype=None))
			return Response("\n".join(res), mimetype="text/html")
		else:
			sub = c.q.filter_by(parent=obj).all()
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
		sub = c.q.filter_by(parent=obj)
		what = "has_children"
	elif t == "superparent":
		sub = c.q.filter_by(superparent=obj)
		what = "has_superchildren"
	elif t == "owner":
		sub = c.q.filter_by(owner=obj)
		what = "has_slaves"
	else:
		raise NotFound()
	return render_template("snippet2.html", obj=obj, t=t, discr=discr, sub=sub, what=what, cls=c, count=sub.count())

#@expose('/new')
#def new(request):
#    error = url = ''
#    if request.method == 'POST':
#        url = request.form.get('url')
#        alias = request.form.get('alias')
#        if not validate_url(url):
#            error = "I'm sorry but you cannot shorten this URL."
#        elif alias:
#            if len(alias) > 140:
#                error = 'Your alias is too long'
#            elif '/' in alias:
#                error = 'Your alias might not include a slash'
#            elif URL.q.filter(URL.uid==alias).count():
#				error = 'The alias you have requested exists already'
#        if not error:
#            uid = URL(url, 'private' not in request.form, alias)
#            db.session.add(uid)
#            return redirect(url_for('pybble.views.display', uid=uid.uid))
#    return render_template('new.html', error=error, url=url, title_trace=[u"neue URL"])
#
#@expose('/display/<uid>')
#def display(request, uid):
#	try: url = URL.q.get_by(uid=uid)
#	except NoResult: raise NotFound()
#	return render_template('display.html', url=url, title_trace=[u"URL anzeigen"])
#
#@expose('/u/<uid>')
#def link(request, uid):
#	try: url = URL.q.get_by(uid=uid)
#	except NoResult: raise NotFound()
#	return redirect(url.target, 301)
#
#@expose('/list/', defaults={'page': 1})
#@expose('/list/<int:page>')
#def list(request, page):
#    query = URL.q.filter(URL.public==True)
#    pagination = Pagination(query, 30, page, 'list')
#    if pagination.page > 1 and not pagination.entries:
#        raise NotFound()
#    return render_template('list.html', pagination=pagination, title_trace=[u"URL-Liste"])
#

def not_found(request, url=None):
    return render_template('not_found.html', title_trace=[u"Seite nicht gefunden"])

def not_allowed(request, obj, perm=None):
    return render_template('not_allowed.html', title_trace=[u"Keine Berechtigung"], obj=obj, perm=perm)

def not_able(request, obj, perm=None):
    return render_template('not_able.html', title_trace=[u"Das geht nicht"], obj=obj, perm=perm)

