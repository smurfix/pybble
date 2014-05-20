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

import os
import sys
import logging
from time import time

from flask import Flask, request, g, session, Markup, Response, current_app
from flask.config import Config
from flask.templating import DispatchingJinjaLoader
from flask.ext.script import Server
from flask._compat import text_type

from hamlish_jinja import HamlishExtension

from .. import FROM_SCRIPT,ROOT_SITE_NAME,ROOT_USER_NAME
from .db import db, NoData
from .models.site import Site,App
from .models.config import ConfigVar
from .models.user import User
from .models.tracking import Delete
from ..globals import current_site
from ..manager import Manager,Command

logger = logging.getLogger('pybble.core.users')

###################################################
# User management

## everything in models.user, for now
