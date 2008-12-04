# -*- coding: utf-8 -*-

from werkzeug import redirect, import_string
from werkzeug.exceptions import NotFound
from pybble.render import render_template, render_my_template, \
	expose, url_for
from pybble.models import TemplateMatch, TM_DETAIL_PAGE, obj_get, obj_class
from pybble.database import db,NoResult
from wtforms import Form, HiddenField
from pybble.flashing import flash

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
	request.user.will_write(obj)
	try:
		return import_string("pybble.%s.editor" % (obj.classname.lower(),))(request, obj)
	except ImportError:
		raise 

@expose('/new/<oid>')
@expose('/new/<oid>/<descr>')
def new_oid(request, oid, descr=None):
	obj=obj_get(oid)
	if descr is None:
		descr = obj.descriptor
	request.user.will_add(obj,descr)
	cls = obj_class(descr)
	return import_string("pybble.%s.newer" % (cls.__name__.lower(),))(request, obj, descr)


class DeleteForm(Form):
	next = HiddenField("next URL")

@expose('/delete/<oid>')
def delete_oid(request, oid):
	obj=obj_get(oid)
	request.user.will_delete(obj)
	form = DeleteForm(request.form, prefix='delete')
	if request.method == 'POST' and form.validate():
		db.session.delete(obj)
		flash(u"%s (%s) wurde gelöscht" % (unicode(obj),obj.oid()), True)

		if form.next.data:
			return redirect(form.next.data)
		elif obj.parent:
			return redirect(url_for("pybble.views.view_oid", oid=obj.oarent.oid()))
		else:
			return redirect(url_for("pybble.views.mainpage"))

	return render_template('delete.html', form=form, title_trace=[u"Löschen"], obj=obj)

@expose('/view/<oid>')
def view_oid(request, oid):
	obj = obj_get(oid)
	request.user.will_read(obj)
	request.user.visited(obj)
	try:
		name = obj.name
		v = import_string("pybble.%s.viewer" % (obj.classname.lower(),))
	except Exception:
		return render_my_template(request, obj=obj_get(oid), detail=TM_DETAIL_PAGE)
	else:
		args = {}
		if "name" in v.func_code.co_varnames: args["name"]=name
		if "oid"  in v.func_code.co_varnames: args["oid" ]=oid
		return redirect(url_for('pybble.%s.viewer' % (obj.classname.lower(),), **args))


@expose('/snippet/<t>')
def view_snippet(request, t):
	oid = request.values["dir"]
	if '/' in oid:
		oid,discr = oid.split('/',1)
	else:
		discr = request.values.get("discr",None)
	if discr:
		return view_snippet2(request, t, oid,discr)
	else:
		return view_snippet1(request, t, oid)

@expose('/last_visited')
def last_visited(request):
	return render_template("last_visited.html", q=request.user.all_visited(), title_trace=[u"zuletzt besucht"])
	

@expose('/snippet/<t>/<oid>')
def view_snippet1(request, t, oid):
	obj = obj_get(oid)
	if t == "parent":
		sub = obj.discr_children
	elif t == "superparent":
		sub = obj.discr_superchildren
	elif t == "owner":
		sub = obj.discr_slaves
	else:
		raise NotFound()

	return render_template("snippet1.html", obj=obj_get(oid), t=t, sub=list(sub))

@expose('/snippet/<t>/<oid>/<discr>')
def view_snippet2(request, t, oid, discr):
	c = obj_class(discr)
	obj=obj_get(oid)
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

