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

@py2_unicode
class Storage(Object):
	"""A box for binary data files"""
	__tablename__ = "storage"
	__mapper_args__ = {'polymorphic_identity': 21}
	_no_crumbs = True

	name = Column(Unicode, nullable=False)
	path = Column(Unicode, nullable=False)
	url = Column(Unicode, nullable=False)

	def __init__(self, name,path,url):
		super(Storage,self).__init__()
		self.name = unicode(name)
		self.path = unicode(path)
		self.url = unicode(url)
		self.superparent = current_request.site
		try: os.makedirs(path)
		except OSError: pass

	def __str__(self):
		return u"‹%s %s: %s %s›" % (self.__class__.__name__, self.id,self.name,unicode(self.path))
	__repr__ = __str__

