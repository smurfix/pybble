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

import os
import sys
import logging
from mongoengine.errors import DoesNotExist

from . import Manager,Command,Option
from ..core.models.doc import ContentType

logger = logging.getLogger('pybble.manager.populate')

content_types = [
	('page','Web page',"A complete HTML-rendered web page"),
	('text','Plain text',"raw text, no formatting"),
	('html','HTML content',"one HTML element"),
	('haml','HAML template',"HTML template (HAML syntax)"),
]
class PopulateCommand(Command):
#	def __init__(self):
#		super(PopulateCommand,self).__init__()
#		#self.add_option(Option("-?","--help", dest="help",action="store_true",help="Display this help text and exit"))
#		self.add_option(Option("name", nargs='?', action="store",help="The blueprint's internal name"))
#		self.add_option(Option("bp", nargs='?', action="store",help="The Pybble blueprint to install"))
#		self.add_option(Option("path", nargs='?', action="store",help="The path prefix to attach it to"))
	def __call__(self,app):
		from ..core.models import Site
		from ..core.models.doc import ContentType
		from .. import ROOT_NAME
		try:
			root = Site.objects.get(name=ROOT_NAME)
		except DoesNotExist:
			raise RuntimeError("Duh? The root site should have been auto-created.")
		else:
			logger.debug("The root site exists. Good.")

		for type,name,doc in content_types:
			try:
				ContentType.get(type)
			except DoesNotExist:
				ContentType(type=type, name=name, doc=doc).save()
				logger.info("Content type '%s' (%s) created." % (type,name))
			else:
				logger.debug("Content type '%s' (%s) exists." % (type,name))
		
