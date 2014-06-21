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

regions = None
from dogpile.cache.api import NO_VALUE

def keystr(args):
	# Take care to keep this idempotent: keystr(x) == keystr(keystr(x))
    return '|'.join(str(x) for x in args)

## TODO: add keyword-only region param

def delete(*args):
	global regions
	if regions is None:
		from .config import regions
	if not regions:
		return

	# TODO: this only works with redis
	r = regions['default'].backend.client
	n = 0
	if "*" in args:
		for k in r.keys(keystr(args)):
			r.delete(k)
			n += 1
	else:
		r.delete(keystr(args))
		n = 1
	return n

def get(*args):
	global regions
	if regions is None:
		from .config import regions
	if not regions:
		return NO_VALUE
	r = regions['default']

	return r.get(keystr(args))

def set(val, *args):
	global regions
	if regions is None:
		from .config import regions
	if not regions:
		return
	r = regions['default']
	r.set(keystr(args),val)

def cached(func, *args):
	global regions
	if regions is None:
		from .config import regions
	if not regions:
		return func()
	r = regions['default']

	return r.get_or_create(keystr(args), func)

