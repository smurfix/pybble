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

logger = logging.getLogger('pybble.manager.populate')

content_types = [
	('text','html','html','Web page',"A complete HTML-rendered web page"),
	('text','plain','txt','Plain text',"raw text, no formatting"),
	('text','html+obj',None,'HTML content',"one HTML element"),
	('text','html+haml','haml','HAML template',"HTML template (HAML syntax)"),
]
class PopulateCommand(Command):
#	def __init__(self):
#		super(PopulateCommand,self).__init__()
#		#self.add_option(Option("-?","--help", dest="help",action="store_true",help="Display this help text and exit"))
#		self.add_option(Option("name", nargs='?', action="store",help="The blueprint's internal name"))
#		self.add_option(Option("bp", nargs='?', action="store",help="The Pybble blueprint to install"))
#		self.add_option(Option("path", nargs='?', action="store",help="The path prefix to attach it to"))
	def __call__(self,app):
		from ..core.models.site import Site
		from ..core.models.types import MIMEtype
		from .. import ROOT_NAME
		try:
			root = Site.q.get_by(name=ROOT_NAME)
		except DoesNotExist:
			db.add(Site(name=ROOT_NAME))
			logger.debug("The root site has been created.")
		else:
			logger.debug("The root site exists. Good.")
		db.commit()

		for type,subtype,ext,name,doc in content_types:
			try:
				MIMEtype.get_by(typ=type,subtyp=subtype)
			except DoesNotExist:
				db.add(MIMEtype(typ=type, subtyp=subtype, ext=ext, name=name, doc=doc))
				logger.info("MIME type '%s/%s' (%s) created." % (type,subtype,name))
		db.commit()
		
