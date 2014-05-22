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

from flask import _app_ctx_stack, g, current_app
from werkzeug.local import LocalProxy

from .core.db import refresh
from .core.models.site import Site

class _NotThere: pass

def _get_site():
	ctx = _app_ctx_stack.top
	site = getattr(ctx,'site',_NotThere)
	if site is _NotThere:
		ctx.site = site = None if current_app.site is None else refresh(current_app.site)
	return site
current_site = LocalProxy(_get_site)

def _root_site():
	return Site.q.get(Site.owner != None, Site.parent == None)
root_site = LocalProxy(_root_site)

