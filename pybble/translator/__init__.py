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

"""\
This is the basic support module for (type) translators

A translator is some code which transforms one MIME type to another.
Examples are HAML to HTML templates, or SASS to SCSS to CSS.

At most two conversion steps are considered.

Translators for natural languages are not considered here.
"""

import os
import sys
import logging
from time import time
from importlib import import_module

from ..core.db import db
from ..core.models.verifier import VerifierBase
from ..core.models.tracking import Delete
from ..core.models.types import MIMEtype,MIMEtranslator
from ..manager import Manager,Command

logger = logging.getLogger('pybble.translator')

class BaseTranslator(object):
	# Override with the MIME types you translate from/to
	## if you provide for more than one, register more classes
	SOURCE = ("application/binary",)
	DEST = ("application/binary",)
	WEIGHT = 10 # more is worse; used when Pybble needs to chain translators

	CONTENT = "template/jinja"

	def __call__(self, content,template, **params):
		"""\
			Translate something for me.

			content: the source; assumed to be a ContentData object.

			Template: The Template I'm translating. Read-only, except for
			the cache+version attributes.

			"""
		raise NotImplementedError("You need to override {}.__call__".format(cls.__name__))
	
class IdentityTranslator(object):
	"""A translator which does not actually do anything"""
	def __call__(self, obj,template, from_mine=None,to_mime=None, **params):
		return obj
	
def list_translators():
	path = os.path.dirname(os.path.abspath(__file__))
	dir_list = os.listdir(path)
	for fname in dir_list:
		if os.path.exists(os.path.join(path, fname, '__init__.py')) and \
				not os.path.exists(os.path.join(path, fname, 'DISABLED')):
			yield fname

