#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, division
##
## This is part of Pybble, a WMS (Whatever Management System) based on
## Jinja2/Haml, Werkzeug, Flask, and Optimism.
##
## Pybble is Copyright © 2014 by Matthias Urlichs <matthias@urlichs.de>,
## it is licensed under the GPLv3. See the file `README.md` for details
## as well as hopeful statements by the author.
##
## This paragraph is auto-generated and may self-destruct at any time.
## Please do not remove the next line, or insert any blank lines before it.
##BP

## Use gevent.
if True:
	## You get spurious errors if the core threading module is imported
	## before monkeypatching.
	import sys
	if 'threading' in sys.modules:
		raise Exception('threading module loaded before patching!')
	del sys

	## All OK, so now go ahead.
	import gevent.monkey
	gevent.monkey.patch_all()
	del gevent

## This is the default name for the site root.
## There should be only one.
ROOT_SITE_NAME = '_root'
ROOT_USER_NAME = 'root'

