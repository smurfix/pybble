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

from werkzeug import import_string

from ..core.db import db
from ..core.add import process_module
from . import Command,Option

logger = logging.getLogger('pybble.manager.add')

class AddCommand(Command):
	"""Add a module to the database"""
	def __init__(self):
		super(AddCommand,self).__init__()
		self.add_option(Option("-f","--force", dest="force",action="store_true",help="Override all database changes"))
		self.add_option(Option("module", action="store",help="Add this module to Pybble"))

	def __call__(self,app, force=False):
		with app.test_request_context('/'):
			self.main(app,force)

	def main(self,app, module=None,help=False,force=False):
		if help or not path:
			self.parser.print_help()
			sys.exit(not help)

		try:
			mod = import_string(module)
		except Exception as e:
			logger.error(e)
			
		process_module(mod)

		db.commit()

		## All done!
		logger.debug("Setup finished.")

