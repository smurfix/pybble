#!/usr/bin/env python
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

# This module contains basic setup code for Pybble.
# Do not import random stuff from here
__all__ = ['ROOT_SITE_NAME','ROOT_USER_NAME','ANON_USER_NAME','TEMPLATE_PATH','STATIC_PATH','FROM_SCRIPT']

## change the default encoding to UTF-8
## this is a no-op in PY3
## PY2 defaults to ASCII, but that's way beyond obsolete
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

# Warnings are bad, except for some which are not
from warnings import filterwarnings
filterwarnings("error")
filterwarnings("ignore",category=DeprecationWarning)
filterwarnings("ignore",category=ImportWarning)
filterwarnings("ignore",message="^Converting column '.*' from VARCHAR to TEXT") # mysql special

## Use gevent.
if True:
	## You get spurious errors if the core threading module is imported
	## before monkeypatching.
	if 'threading' in sys.modules:
		raise Exception('threading module loaded before patching!')

	## All OK, so now go ahead.
	import gevent.monkey
	gevent.monkey.patch_all()

## This is the default name for the site root.
## There should be only one.
ROOT_SITE_NAME = '_root'
ROOT_USER_NAME = 'root'
ANON_USER_NAME = ''

# used for initial import only
from os import path
TEMPLATE_PATH = path.join(path.dirname(__file__), 'templates')
STATIC_PATH = path.join(path.dirname(__file__), 'static')

# if you start something from the script, the default user is the site root.
# This is set in manager.py and checked in pybble.app.BaseApp._setup_user().
FROM_SCRIPT = False

