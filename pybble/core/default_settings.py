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

## You need to implement these in your LOCAL.py file.
#SECRET_KEY="If you do not change this to something random, you deserve to get hacked."
#MEDIA_PATH="/var/lib/pybble/or/some/other/place/to/store/my/files"
# You also need to set the "PYBBLE" environment variable to "LOCAL".

## These are a bunch of "required" default settings. They can be documented …
import datetime

APPLICATION_ROOT=None
DEBUG=False
d_DEBUG="Emit debug information"
DEBUG_ACCESS=False
d_DEBUG_ACCESS="Trace access control tests"
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
SESSION_COOKIE_AGE=86400 # 1 day
SESSION_REFRESH_EACH_REQUEST=True
STATIC_EXPIRE=SEND_FILE_MAX_AGE_DEFAULT
d_STATIC_EXPIRE="How long in the future static files' Expire headers shall be set to"
TESTING=False
TRAP_BAD_REQUEST_ERRORS=False
TRAP_HTTP_EXCEPTIONS=False
USE_X_SENDFILE=False

## used when logging is on.
LOGGER_NAME='pybble'
LOGGER_LEVEL="DEBUG"
LOGGER_FORMAT='%(asctime)s %(name)-12s %%(levelname)-8s %%(message)s'
LOGGER_DATE_FORMAT='%Y-%m-%d %H:%M:%S'

MEDIA_PATH="/var/www/pybble"

MAILHOST="localhost"
d_MAILHOST="The system to send email through"

del datetime
