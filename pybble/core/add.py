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
import re
from traceback import print_exc,format_exc

from sqlalchemy import or_

from flask import request,current_app,g, _app_ctx_stack
from flask._compat import text_type,string_types
from werkzeug import import_string

from .. import TEMPLATE_PATH, STATIC_PATH
from ..utils import random_string, NotGiven
from ..globals import current_site, root_site
from . import config
from .utils import attrdict
from .db import db, NoData, engine
from .models.types import MIMEtype,MIMEtranslator,MIMEadapter
from .models.config import ConfigVar
from .models.site import Site
from .models.site import App,Blueprint
from .models.verifier import VerifierBase
from .models.objtyp import ObjType
from .models.template import Template,TemplateMatch

logger = logging.getLogger('pybble.core.add')

_metadata = re.compile('##:?(\S+) *[ :] *(.*)\n') # re.U ?

def _upd(obj,attrdata, force=False):
	"""\
		Set attribute `attr` of `obj` to `data`.

		If already set, overwrite if `force` is True.
		"""
	chg = {}
	for attr,data in attrdata:
		if data is NotGiven:
			continue
		odata = getattr(obj,attr,None)
		if data is None:
			if odata is None or not force:
				continue
			logger.info("{}: cleared {}.".format(obj,attr))
		elif odata is None:
			logger.info("{}: set {}.".format(obj,attr))
		else:
			if odata == data or not force:
				continue
			logger.info("{}: updated {}.".format(obj,attr))
		chg[attr] = (odata,data)
	if chg:
		Change.new(obj,chg)
		for k,v in chg.items():
			setattr(obj,k,v[1])

def _load(Obj,lister, force=False):
	for obj in lister:
		name = NotGiven
		doc = NotGiven
		if isinstance(obj,(list,tuple)):
			if len(obj) > 2:
				doc = obj[2]
			name = obj[1]
			obj = obj[0]
		if isinstance(obj,string_types):
			obj = import_string(obj)
		
		path = obj.__module__+'.'+obj.__name__
		try:
			obj = Obj.q.get_by(path=path)
		except NoData:
			if name is NotGiven:
				name = path
			obj = Obj.new(name=name, path=path)
		else:
			_upd(obj,(('name',name),('doc',doc)), force=force)

		add_vars(getattr(obj.mod,'VAR',()),obj, force=force)
		add_templates(getattr(obj.mod,'TEMPLATE',()), parent=obj, force=force)

def modpath(obj,dir=None):
	mod = getattr(obj,"mod",obj)
	mod = sys.modules[mod.__module__]
	try:
		mp = os.path.dirname(mod.__file__)
	except AttributeError:
		mp = mod.__path__[0]
	if dir and dir != ".":
		mp = os.path.join(mp, dir)
	return mp

def add_mime(typ,subtyp,ext=NotGiven,name=NotGiven,doc=NotGiven, force=False):
	"""Add a single MIME type."""

	try:
		mt = MIMEtype.q.get_by(typ=typ,subtyp=subtyp)
	except NoData:
		if ext is NotGiven: ext = None
		if doc is NotGiven: doc = None
		if name is NotGiven: name = None
		mt = MIMEtype.new(typ=typ, subtyp=subtyp, ext=ext, name=name, doc=doc)
		logger.debug("MIME type ‘{}’ created.".format(mt))
	else:
		_upd(mt,(('doc',doc), ('ext',ext), ('name',name)),force)

def add_mimes(content_types, force=False):
	"""Add a list of MIME types."""
	for args in content_types:
		add_mime(force=force, *args)

def add_vars(gen,parent=None, force=False):
	"""Add variables. The generator yields (name,value,docstring) triples."""

	if parent is None: # default to the system root
		parent = Site.q.get_by(parent=None)

	parent = parent.config
	added=[]
	for var in gen:
		default = None
		doc = None
		if isinstance(var,(list,tuple)):
			if len(var) > 2:
				doc = var[2]
			default = var[1]
			var = var[0]

		try:
			cf = ConfigVar.q.get_by(name=var, parent=parent)
		except NoData:
			cf = ConfigVar.new(parent=parent, name=var, value=default, doc=doc)
		else:
			_upd(cf,(('doc',doc), ('value',default)), force)
			if not cf.doc or force:
				cf.doc = d
	if added:
		logger.debug("New variables for {}: ".format(parent) + ",".join(added))
	db.commit()

def add_objtypes(objects, force=False):
	"""Add a list of MIME types."""

	objs = []
	for obj in objects:
		name = None
		doc = None
		if isinstance(obj,(list,tuple)):
			if len(obj) > 2:
				doc = obj[2]
			name = obj[1]
			obj = obj[0]
		if isinstance(obj,string_types):
			obj = import_string(obj)
		objs.append(obj)

	ObjType.metadata.create_all(engine)

	for obj in objs:
		ObjType.get(obj)

def add_translator(obj,name,doc=NotGiven, force=False):
	## Templating and whatnot

	def get_types(types, add=False):
		if isinstance(types,string_types):
			types = (types,)
		for s in types:
			mt = MIMEtype.get(s, add=add)
			if mt.subtyp == "*":
				yield mt,10
				for r in MIMEtype.q.filter_by(typ=mt.typ):
					if r.subtyp == '*' or r.subtyp.startswith('_'):
						continue
					yield mt,50
			else:
				yield mt,0

	name = text_type(name)
	mpath = obj.__module__+'.'+obj.__name__
	try:
		E=obj.SOURCE
		src = list(get_types(obj.SOURCE, add=True))
		E=obj.DEST
		dst = list(get_types(obj.DEST, add=True))
		E=obj.CONTENT
		mt = MIMEtype.get(obj.CONTENT, add=True)
		E="??"
		w = obj.WEIGHT
	except NoData as e:
		logger.warn("{} is not usable ({}): {}\n{}".format(obj,E,str(e), format_exc()))
		return

	try:
		trans = MIMEtranslator.q.get_by(path=mpath)
	except NoData:
		trans = MIMEtranslator.new(path=mpath,mime=mt,weight=w,name=mpath)
	else:
		_upd(trans,(("mime",mt),("weight",w)),force=force)

	for s,sw in src:
		for d,dw in dst:
			n = "{} to {} with {}".format(src,dst,mt)
			w=sw+dw

			try:
				obj = MIMEadapter.q.get_by(from_mime=s,to_mime=d,translator=trans)
			except NoData:
				obj = MIMEadapter.new(from_mime=s,to_mime=d,translator=trans,name=n,weight=w)
			else:
				_upd(obj,(("weight",w),("name",n)),force=force)

	db.commit()

def add_translators(lister, force=False):
	for obj in lister:
		name = NotGiven
		doc = NotGiven
		if isinstance(obj,(list,tuple)):
			if len(obj) > 2:
				doc = obj[2]
			name = obj[1]
			obj = obj[0]
		if isinstance(obj,string_types):
			obj = import_string(obj)
		
		add_translator(obj,name,doc, force=force)

## static files (recursive)
def add_static(filepath,path, force=False):
	if os.path.isdir(filepath):
		for f in os.listdir(filepath):
			if f.startswith("."):
				continue
			f = f.decode("utf-8")
			fp = os.path.join(filepath,f)
			wp = path+'/'+f if path else f
			add_files(fp,wp)
		return

	dot = f.rindex(".")
	mime = MIMEtype.get(f[dot+1:])

	# TODO: don't read the whole file
	with open(filepath,"rb") as fd:
		content = fd.read()

	try:
		sb = BinData.lookup(content)
	except NoData:
		sb = BinData.new(f[:dot],ext=f[dot+1:],content=content, storage=st)

	try:
		try:
			sf = StaticFile.q.get_by(path=webpath,site=root)
		except NoData:
			sf = StaticFile.q.get_by(path='/'+webpath,site=root)
	except NoData:
		sf = StaticFile.new(webpath,sb)
	else:
		if sf.path.startswith('/'):
			sf.path = sf.path[1:] # silently fix this

		try:
			c = sf.content
		except EnvironmentError as e:
			import errno
			if e.errno != errno.ENOENT:
				raise
			logger.error("File ‘{}’ vanished".format(filepath))
			sf.file.hash = None
			Delete.new(sf.file, comment="file vanished")
			db.flush()

			try:
				sb = BinData.lookup(content)
			except NoData:
				sb = BinData.new(f[:dot],ext=f[dot+1:],content=content, storage=st)
			osb = sf.bindata
			sf.file = sb
			sf.record_change({"file":(osb,sb)},comment="file vanished")
			c = sf.content

		if content != sf.content:
			logger.warning("StaticFile %d:‘%s’ differs." % (sf.id,webpath))
			if force:
				try:
					sb = BinData.lookup(content)
				except NoData:
					sb = BinData.new(f[:dot],ext=f[dot+1:],content=content, storage=st)
				try:
					Delete.new(sf.file, comment="replaced by update")
					Change.new(sf,data={'file':(sf.file,sb)})
				except:
					pdb.post_mortem()
					raise
				sf.file = sb
	db.commit()

def add_statics(data, force=False):
	for filepath,webpath in data:
		add_static(filepath,webpath, force=force)


## templates
def add_template(parent, filepath,webpath, inferred="", force=False):
	extmap = { 'haml':'template/haml', 'html':'template/jinja' }

	with file(filepath) as f:
		try:
			data = inferred + f.read().decode("utf-8")
		except Exception:
			print("While reading",filepath,file=sys.stderr)
			raise

	hdr = attrdict(match=[],inherit=None)

	if isinstance(inferred,(list,tuple)):
		gen1 = list(inferred)
	elif isinstance(inferred,string_types):
		gen1 = []
		m = _metadata.match(inferred)
		while m:
			k,v = m.groups()
			gen1.append((k,v),)
			inferred = inferred[m.end():]
			m = _metadata.match(inferred)
	m = _metadata.match(data)
	while m:
		k,v = m.groups()
		gen1.append((k,v),)
		data = data[m.end():]
		m = _metadata.match(data)

	for k,v in gen1:
		ov = hdr.get(k,None)
		if ov is None:
			if v == "-":
				v = None
			elif '/' in v:
				v = MIMEtype.get(v, add=True)
			elif v in ("True False 0 1 None".split()):
				v = eval(v)
			elif k == "weight":
				v = int(v)
			hdr[k] = v
		elif k == "match":
			hdr[k].append((v,hdr.inherit))
		else:
			raise ValueError("Template ‘{}’: duplicate metadata key ‘{}’".format(filepath,k))

	if "src" not in hdr: hdr.src = "pybble/_empty"
	if "dst" not in hdr: hdr.dst = "html/*"
	if "named" not in hdr: hdr.named = True
	if "dsc" not in hdr: hdr.dsc = None
	if "weight" not in hdr: hdr.weight = 0
	if "typ" not in hdr:
		try:
			dot = filepath.rindex(".")
			hdr.typ = MIMEtype.get(extmap[filepath[dot+1:]], add=True)
		except (ValueError,KeyError,NoData):
			logger.error("Template ‘{}’ not loaded: unknown MIME type".format(filepath))
			return

	hdr_src = MIMEtype.get(hdr.src)
	hdr_dst = MIMEtype.get(hdr.dst)
	hdr_typ = MIMEtype.get(hdr.typ)
	hdr_dsc = TM_DETAIL_id(hdr.dsc) if hdr.dsc is not None else None
	n="{} from {} to {}".format(hdr_typ,hdr_src,hdr_dst)

	try:
		tr = MIMEtranslator.q.get_by(mime=hdr_typ)
	except NoData:
		logger.error("Template ‘{}’ not loaded: no translator which understands {}".format(filepath,hdr_typ))
		return
	try:
		a = MIMEadapter.q.get_by(from_mime=hdr_src, to_mime=hdr_dst, translator=tr)
	except NoData:
		a = MIMEadapter.new(from_mime=hdr_src, to_mime=hdr_dst, translator=tr, name=n)
		logger.debug("Adapter ‘{}’ created.".format(a))

	try:
		t = Template.q.get_by(source=filepath)
	except NoData:
		t = Template.new(source=filepath, data=data, target=parent, adapter=a, weight=hdr.weight or 0)
		if hdr.named: t.name = webpath
		logger.debug("Template ‘{}’ created.".format(t))
	else:
		if hdr.named: n=(('name',webpath),)
		else: n = ()
		_upd(t,n+(('target',parent),('adapter',a),('content',data)),force=force)

	root = Site.q.get_by(parent=None)
	for m,inherit in hdr.match:
		if m == "root":
			m = root
		elif m == "superuser":
			m = superuser
		else:
			logger.warn("Template {} ‘{}’: I don't know how to attach to {}".format(t.id, filepath, m))

		try:
			tm = TemplateMatch.q.filter_by(template=t,target=m,for_objtyp=hdr_dsc).filter(or_(TemplateMatch.inherit == None,TemplateMatch.inherit==inherit)).one()
		except NoData:
			tm = TemplateMatch.new(template=t,target=m,for_objtyp=hdr_dsc,inherit=inherit)
			logger.debug("TemplateMatch ‘{}’ created.".format(tm))

	db.commit()

def add_templates(data, parent=None, force=False):
	if parent is None: # default to the system root
		parent = Site.q.get_by(parent=None)

	for d in data:
		if isinstance(d,(tuple,list)):
			filepath = d[0]
			webpath = d[1]
			inferred = d[2] if len(d) > 2 else ""
		else:
			assert isinstance(d,string_types)
			filepath = text_type(d)
			webpath = inferred = ""
		filepath = modpath(parent,filepath)

		find_templates(parent, filepath,webpath, inferred=inferred, force=force)

def find_templates(parent, path,webpath="", inferred="",force=False):
	if not os.path.exists(path):
		return
	if os.path.isdir(path):
		for fn in os.listdir(path):
			if fn.startswith("."):
				continue
			newpath = os.path.join(path,fn)
			newwebpath = "{}/{}".format(webpath,fn) if webpath else fn
			find_templates(parent, newpath,newwebpath, force=force)
		return
	add_template(parent, path,webpath, inferred="",force=force)

def process_module(mod, force=False):
	targets = (
		('MODEL',add_objtypes),
		('MIME',add_mimes),
		('TRANSLATOR',add_translators),
		('APP',lambda x,force: _load(App,x,force)),
		('BLUEPRINT',lambda x,force: _load(Blueprint,x,force)),
		('VAR',add_vars),
		('VERIFIER',lambda x,force: _load(VerifierBase,x,force)),
		('FILE',add_statics),
		('TEMPLATE',add_templates),
	)

	for k,proc in targets:
		try:
			try:
				data = getattr(mod,k)
			except AttributeError:
				data = mod.get(k)
		except (KeyError,AttributeError):
			pass
		else:
			if data is not None:
				proc(data, force=force)
