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
from time import time
from importlib import import_module

from mongoengine.errors import DoesNotExist

from .. import ROOT_NAME
from ..core.db import db
from ..core.models import Site,Blueprint
from ..manager import Manager,Command

logger = logging.getLogger('pybble.blueprint')

def create_contenttype(type,name,doc=None):
	"""\
		Attach a content type.

		:param type: The module responsible for this content type.
		:param name: A human-readable name for this content type.
		:param doc: A longer description.
		"""

	ct = get_contenttype_module(type)
	assert ct is not None, "content type '%s' does not exist"%(app,)
	if doc is None:
		doc = name
	ct = ContentType(type=type, name=name, doc=doc)
	ct.save()
	return ct

def get_contenttype_module(type):
	ct = import_module("pybble.content."+type)
	return ct.ContentType

def drop_contenttype(name):
	ct = ContentType.objects.get(name=name)
	ct.delete()

def list_contenttypes():
	path = os.path.dirname(os.path.abspath(__file__))
	import pdb;pdb.set_trace()
	dir_list = os.listdir(path)
	for fname in dir_list:
		if os.path.exists(os.path.join(path, fname, '__init__.py')) and \
				not os.path.exists(os.path.join(path, fname, 'DISABLED')):
			yield fname

class BaseContentDriver:
	pass
	
