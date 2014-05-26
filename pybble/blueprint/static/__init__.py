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

_doc="""
This module contains a few dummy URLs for testing.
"""

from flask import render_template, abort, request, Response, current_app
from jinja2 import TemplateNotFound
from werkzeug.http import parse_etags, remove_entity_headers, http_date

from pybble.core.route import Exposer
from pybble.blueprint import BaseBlueprint
from pybble.core.db import NoData
from pybble.core.models.files import StaticFile
from pybble.core.models.object import Object
from pybble.globals import current_site

from datetime import datetime,timedelta

expose = Exposer()

class Blueprint(BaseBlueprint):
	PARAMS = (
		## TODO: able to change prefixes
		## TODO: serve, and generate redirects to, OIDified static filenames
	)
	def setup(self):
		super(Blueprint,self).setup()
		expose.add_to(self)

@expose("/static/<path:file>", endpoint="static")
def serve_path(file):
	site = current_site
	while site:
		try:
			sf = StaticFile.q.get_by(site=site, path=file)
		except NoData:
			site = site.parent
			if not site:
				raise
		else:
			break

	if parse_etags(request.environ.get('HTTP_IF_NONE_MATCH')).contains(sf.hash):
		r = Response("", mimetype=str(sf.mimetype))
		r.status_code = 304
		remove_entity_headers(r.headers)
	else:
		r = Response(sf.content, mimetype=str(sf.mimetype))
	r.set_etag(sf.hash)
	r.headers[b'Cache-Control']='public'
	r.headers[b'Expiry']=http_date(datetime.utcnow()+timedelta(0,current_app.config.STATIC_EXPIRE))
	r.headers[b'Last-Modified']=http_date(sf.modified)
	return r

@expose("/download/<oid>")
@expose("/download/<oid>/<name>")
def download(request,oid,name=None):
	obj = Object.by_oid(oid)
	r = Response(obj.content, mimetype=obj.mimetype)
	if name:
		n = obj.name
		if obj.mime.ext:
			n += "."+obj.mime.ext
		assert n == name

	if parse_etags(request.environ.get('HTTP_IF_NONE_MATCH')).contains(obj.hash):
		r = Response("", mimetype=obj.mimetype)
		r.status_code = 304
		remove_entity_headers(r.headers)
	else:
		r = Response(obj.content, mimetype=obj.mimetype)

	r.set_etag(obj.hash)
	r.headers['Cache-Control']='public'
	r.headers['Expiry']=http_date(datetime.utcnow()+timedelta(999))
	r.headers['Last-Modified']=http_date(obj.timestamp)
	return r

