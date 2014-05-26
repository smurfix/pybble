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

# Template detail levels

class TM_DETAIL(dict):
	_mime = {}
	_name = {}
	def _add(self,id,name, mime=None):
		self[id] = name
		globals()["TM_DETAIL_"+name.upper()] = id
		if mime is None:
			mime="html/"+name.lower()
		self._mime[id]=mime
		self._name[name.lower()]=id
def TM_DETAIL_name(id):
	return TM_DETAIL[int(id)]
def TM_DETAIL_id(name):
	return TM_DETAIL._name[name.lower()]
def TM_MIME(id):
	return TM_DETAIL._mime[int(id)]
TM_DETAIL=TM_DETAIL()

for _x,_y,_z in (
		(1,"Page","text/html"),
		(2,"Subpage",None),
		(3,"String",None),
		(4,"Detail",None),
		(5,"Snippet",None),
		(6,"Hierarchy",None),
		(7,"RSS",None),
		(8,"email","text/plain"),
		(9,"preview",None),
		):
	TM_DETAIL._add(_x,_y,_z)

class MissingDummy(Exception):
	pass

# Permission levels
## Negative values need to match exactly.
## Positive one accumulate, i.e. somebody who can write is obviously able to read
## Special handling: An objtype's default of ADD (or indeed anything <0) implies SUB_ADMIN

PERM = {0:"None", 1:"List", 2:"Read", -3:"Add", 4:"Write", 5:"Delete", 8:"Sub_Admin", 9:"Admin"}
PERM_NAME = {}
for _x,_y in PERM.items():
	globals()["PERM_"+_y.upper()] = _x
	PERM_NAME[_y] = _x

def PERM_name(id):
	return PERM[int(id)]

