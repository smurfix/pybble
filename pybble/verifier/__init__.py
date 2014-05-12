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
This is the basic support module for verifiers.

A verifier is an external code, sent in an email or an URL parameter (think
QR codes) which allow a user to do things they couldn't usually do.

Like, for instance, log in (need to check for valid email)
"""

import os
import sys
import logging
from time import time
from importlib import import_module

from ..core.db import db
from ..core.models.verifier import VerifierBase
from ..core.models.tracking import Delete
from ..manager import Manager,Command

logger = logging.getLogger('pybble.verifier')

class BaseVerifier(object):
	PARAMS = ()
	template = None

	@classmethod
	def new(cls,user):
		raise NotImplementedError("You need to override {}.new".format(cls.__name__))

	@classmethod
	def send(cls,verifier,template=None):
		"""Send this verifier to its user, usually via email."""
		if template is None:
			template = cls.template
			if template is None:
				raise NotImplementedError("You need to override at least the template name in {}.send".format(cls.__name__))
		from pybble.confirm import confirm
		user=verifier.parent
		send_mail(user.email, 'verify_email.txt',
			  user=user, code=verifier.code,
			  link=url_for("pybble.confirm.confirm", code=verifier.code, _external=1),
				  page=url_for("pybble.confirm.confirm", _external=1))
	
	@classmethod
	def entered(cls,verifier):
		raise NotImplementedError("You need to override {}.entered".format(cls.__name__))
	
	@classmethod
	def confirmed(cls,verifier):
		raise NotImplementedError("You need to override {}.confirmed".format(cls.__name__))

def list_verifiers():
	path = os.path.dirname(os.path.abspath(__file__))
	dir_list = os.listdir(path)
	for fname in dir_list:
		if os.path.exists(os.path.join(path, fname, '__init__.py')) and \
				not os.path.exists(os.path.join(path, fname, 'DISABLED')):
			yield fname

