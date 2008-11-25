# -*- coding: utf-8 -*-

from werkzeug import redirect
from werkzeug.exceptions import NotFound
from pybble.utils import Pagination, render_template, expose, \
     validate_url, url_for, render_my_template
from pybble.models import URL, TemplateMatch, TM_TYPE_PAGE, TM_TYPE_LIST, obj_get
from pybble.database import db,NoResult

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
	return render_template('tree.html', obj=obj)

@expose('/snippet')
@expose('/snippet/<oid>')
def view_snippet(request, oid=None, level=TM_TYPE_PAGE):
	if oid is None:
		oid = request.values['dir'] # FileTree
		level = request.values.get(level,TM_TYPE_LIST)
	return render_my_template(request, obj_get(oid), type=level)

@expose('/new')
def new(request):
    error = url = ''
    if request.method == 'POST':
        url = request.form.get('url')
        alias = request.form.get('alias')
        if not validate_url(url):
            error = "I'm sorry but you cannot shorten this URL."
        elif alias:
            if len(alias) > 140:
                error = 'Your alias is too long'
            elif '/' in alias:
                error = 'Your alias might not include a slash'
            elif URL.q.filter(URL.uid==alias).count():
				error = 'The alias you have requested exists already'
        if not error:
            uid = URL(url, 'private' not in request.form, alias)
            db.session.add(uid)
            return redirect(url_for('pybble.views.display', uid=uid.uid))
    return render_template('new.html', error=error, url=url, title_trace=[u"neue URL"])

@expose('/display/<uid>')
def display(request, uid):
	try: url = URL.q.get_by(uid=uid)
	except NoResult: raise NotFound()
	return render_template('display.html', url=url, title_trace=[u"URL anzeigen"])

@expose('/u/<uid>')
def link(request, uid):
	try: url = URL.q.get_by(uid=uid)
	except NoResult: raise NotFound()
	return redirect(url.target, 301)

@expose('/list/', defaults={'page': 1})
@expose('/list/<int:page>')
def list(request, page):
    query = URL.q.filter(URL.public==True)
    pagination = Pagination(query, 30, page, 'list')
    if pagination.page > 1 and not pagination.entries:
        raise NotFound()
    return render_template('list.html', pagination=pagination, title_trace=[u"URL-Liste"])

def not_found(request):
    return render_template('not_found.html', title_trace=[u"Seite nicht gefunden"])
