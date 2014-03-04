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

import datetime

## You absolutely _must_ implement these in your local_settings.py file.

#MONGODB_SETTINGS={'DB': 'pybble'}
#SECRET_KEY="If you do not change this to something random, you deserve to get hacked."

## These are our default settings.

APPLICATION_ROOT=None
DEBUG=False
JSON_AS_ASCII=True
JSONIFY_PRETTYPRINT_REGULAR=False
JSON_SORT_KEYS=False
MAX_CONTENT_LENGTH=None
PERMANENT_SESSION_LIFETIME=datetime.timedelta(31)
PREFERRED_URL_SCHEME='http'
PRESERVE_CONTEXT_ON_EXCEPTION=None
PROPAGATE_EXCEPTIONS=None
SEND_FILE_MAX_AGE_DEFAULT=43200
SERVER_NAME=None
SESSION_COOKIE_DOMAIN=None
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_NAME='session'
SESSION_COOKIE_PATH=None
SESSION_COOKIE_SECURE=False
SESSION_REFRESH_EACH_REQUEST=True
TESTING=False
TRAP_BAD_REQUEST_ERRORS=False
TRAP_HTTP_EXCEPTIONS=False
USE_X_SENDFILE=False

## used when logging is on.
LOGGER_NAME='pybble'
LOGGER_LEVEL="DEBUG"
LOGGER_FORMAT='%(asctime)s %(name)-12s %%(levelname)-8s %%(message)s'
LOGGER_DATE_FORMAT='%Y-%m-%d %H:%M:%S'

