# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, division, unicode_literals
##
## This is part of Pybble, a WMS (Whatever Management System) based on
## Jinja2/Haml, Werkzeug, Flask, and Optimism.
##
## Pybble is Copyright © 2009-2014 by Matthias Urlichs <matthias@urlichs.de>,
## it is licensed under the GPLv3. See the file `README.md` for details
## as well as hopeful statements by the author.
##
## This paragraph is auto-generated and may self-destruct at any time.
## Please do not remove the next line, or insert any blank lines before it.
##BP

from flask._compat import PY2,reraise,StringIO, iteritems,iterkeys,itervalues, text_type, string_types,integer_types

if not PY2:
	def py2_unicode(cls):
		return cls

else:
	def py2_unicode(cls):
		cls.__unicode__ = cls.__str__
		replace_repr = cls.__repr__ is cls.__str__
		cls.__str__ = lambda x: x.__unicode__().encode('utf-8')

		if replace_repr:
			cls.__repr__ = cls.__str__
			
		return cls

