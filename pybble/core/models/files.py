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

def add_mime(name,typ,subtyp,ext):
	ext = unicode(ext)

	try:
		t = db.get_by(MIMEtype,typ=typ,subtyp=subtyp)
	except NoResult:
		t=MIMEtype()
		t.name = unicode(name)
		t.typ = typ
		t.subtyp = subtyp
		t.ext = ext
		db.store.add(t)
		db.store.flush()
		return t
	else:
		assert name == t.name
		if ext != t.ext:
			try:
				tt = db.get_by(MIMEext,ext=ext)
			except NoResult:
				tt = MIMEext()
				tt.mime = t
				tt.ext = ext
				db.store.add(tt)
				db.store.flush()
		return t

def mime_ext(ext):
	try:
		return db.get_by(MIMEtype,ext=ext)
	except NoResult:
		return db.get_by(MIMEext,ext=ext).mime

@py2_unicode
class MIMEtype(Base):
	"""Known MIME Types"""
	__tablename__ = "mimetype"
	id = Column(Integer, primary_key=True)
	name = Column(Unicode, nullable=False)
	typ = Column(Unicode, nullable=False)
	subtyp = Column(Unicode, nullable=False)
	ext = Column(Unicode, nullable=False) # primary extension
	exts = ReferenceSet(id,"MIMEext.mime_id")
	
	@property
	def mimetype(self):
		return "%s/%s" % (self.typ,self.subtyp)

	def __str__(self):
		return u"‹%s %s: .%s %s›" % (self.__class__.__name__, self.id,self.ext,self.mimetype)
	__repr__ = __str__

def find_mimetype(typ,subtyp=None):
	if subtyp is None:
		typ,subtyp = typ.split("/")
	return db.get_by(MIMEtype,typ=typ, subtyp=subtyp)

@py2_unicode
class MIMEext(Base):
	"""Extensions for MIME types"""
	__tablename__ = "mimeext"
	id = Column(Integer, primary_key=True)
	mime_id = Column(Integer)
	mime = Reference(mime_id,MIMEtype.id)
	ext = Column(Unicode, nullable=False)

	def __str__(self):
		return u"‹%s %s: %s %s›" % (self.__class__.__name__, self.id,self.ext,unicode(self.mime))
	__repr__ = __str__

def hash_data(content):
	from base64 import b64encode
	try:
		from hashlib import sha1
	except ImportError:
		from sha import sha as sha1
	return b64encode(sha1(content).digest(),altchars="-_").rstrip("=")

@py2_unicode
class BinData(Base):
	"""
		Stores one data file
		owner: whoever uploaded the thing
		parent: some object this is attached to
		superparent: the storage
		"""
	__tablename__ = "bindata"
	__mapper_args__ = {'polymorphic_identity': 22}
	_no_crumbs = True
	_proxy = { "storage":"superparent" }

	storage_seq = Column(Integer)
	mime_id = Column(Integer, nullable=False)
	mime = Reference(mime_id,MIMEtype.id)
	name = Column(Unicode, nullable=False)
	hash = Column(Unicode, nullable=False)
	timestamp = DateTime(default_factory=datetime.utcnow)
	size = Column(Integer)

	static_files = ReferenceSet(id, BaseObject.parent_id)

	@staticmethod
	def lookup(content):
		res = db.store.find(BinData, And(BinData.hash == hash_data(content)), BinData.superparent_id != None).one()
		if not res:
			raise NoResult
		return res
			
	def __init__(self,name, ext=None,mimetype=None, content=None, parent=None, storage=None):
		super(BinData,self).__init__()
		if not parent: parent = current_request.site
		if not storage: storage = parent.default_storage
		if mimetype:
			self.mime = mimetype
			if ext:
				assert mimetype == mime_ext(ext),"Extension doesn't match MIME type"
		elif ext:
			self.mime = mime_ext(ext)
		else:
			raise RuntimeError("You need to specify MIME type or extension")
		self.name = name
		self._content = content
		self.hash = hash_data(content)
		self.size = len(content)
		self.owner = current_request.user
		self.parent = parent
		self.superparent = storage
		self._save_content()

	def __str__(self):
		return u"‹%s %s: %s %s›" % (self.__class__.__name__, self.id,self.name+"."+self.ext,self.mimetype)
	__repr__ = __str__

	@property
	def content(self):
		if not hasattr(self,"_content"):
			try:
				self._content = open(self.path).read()
			except IOError:
				self._content = open(self.old_path).read()
		return self._content

	@property
	def mimetype(self):
		try:
			return self.mime.mimetype
		except Exception:
			return "???/???"
	@property
	def ext(self):
		try:
			return self.mime.ext
		except Exception:
			return "???"

	def _old_get_chars(self):
		if self.id is None:
			db.store.flush()
			if self.id is None:
				return "???"
		id = self.id-1
		chars = "23456789abcdefghjkmnopqrstuvwxyz"
		midchars = "abcdefghjkmnopq"
		fc = []
		flast = chars[id % len(chars)]
		id = id // len(chars)
		while id:
			c = chars[id % len(midchars)]
			id = id // len(midchars)
			c = chars[id % len(midchars)] + c
			id = id // len(midchars)
			fc.insert(0,c)
		fc.append("_")
		fc.append(self.name+"_"+self.hash[0:10]+flast)
		if self.mime.ext:
			fc[-1] += "."+self.mime.ext
		return fc

	def _get_chars(self):
		if self.storage_seq is None:
			db.store.flush()
			self.storage_seq = AutoReload
			if self.storage_seq is None:
				return "???"
		id = self.storage_seq-1
		chars = "23456789abcdefghjkmnopqrstuvwxyz"
		midchars = "abcdefghjkmnopq"
		fc = []
		flast = chars[id % len(chars)]
		id = id // len(chars)
		while id:
			c = chars[id % len(midchars)]
			id = id // len(midchars)
			c = chars[id % len(midchars)] + c
			id = id // len(midchars)
			fc.insert(0,c)
		fc.append("_")
		fc.append(self.name+"_"+self.hash[0:10]+flast)
		if self.mime.ext:
			fc[-1] += "."+self.mime.ext
		return fc

	def _move_old(self):
		op = self.old_path
		np = self.path
		if op != np:
			try:
				os.rename(op,np)
			except OSError:
				pass

	@property
	def path(self):
		fn = self.superparent.path
		fc = self._get_chars()
		dir = os.path.join(fn,*fc[:-1])
		if not os.path.isdir(dir):
			os.makedirs(dir)
		fn = os.path.join(dir,fc[-1])
		return fn

	@property
	def old_path(self):
		fn = self.superparent.path
		fc = self._old_get_chars()
		return os.path.join(fn,*fc)

	def get_absolute_url(self):
		fc = self._get_chars()
		fn = self.superparent.url + "/".join(fc)
		return fn
	
	def delete(self):
		p = self.path
		if os.path.exists(p):
			os.remove(p)
		super(BinData,self).delete()

#	def __storm_pre_flush__(self):
#		super(BinData,self).__storm_pre_flush__()
#		if self._content is None:
#			raise RuntimeError("Need to set content before saving")
#		self._save_content()

	def _save_content(self):
		p = self.path
		if os.path.exists(p):
			raise RuntimeError("File exists")
		try:
			open(p,"w").write(self.content)
		except BaseException:
			if os.path.exists(p):
				os.remove(p)
			raise

@py2_unicode
class StaticFile(Object):
	"""\
		Record that a static file belongs to a specific site.
		Superparent: The site.
		Parent: The storage.
		"""
	__tablename__ = "staticfile"
	__mapper_args__ = {'polymorphic_identity': 20}
	_no_crumbs = True
	_proxy = { "bindata":"parent" }

	path = Column(Unicode, nullable=False)
	modified = DateTime(default_factory=datetime.utcnow)

	def __storm_pre_flush__(self):
		self.modified = datetime.utcnow()
		super(StaticFile,self).__storm_pre_flush__()

	def __init__(self, path, bin):
		super(StaticFile,self).__init__()
		self.path = path
		self.superparent = current_request.site
		self.parent = bin
		
	def __str__(self):
		if self._rec_str or not self.superparent or not self.parent: return super(StaticFile,self).__str__()
		try:
			self._rec_str = True
			return u'‹%s %s: %s in %s›' % (self.__class__.__name__, self.id, self.path, unicode(self.superparent))
		finally:
			self._rec_str = False
	__repr__ = __str__

	@property
	def hash(self):
		return self.bindata.hash
	@property
	def content(self):
		return self.bindata.content
	@property
	def mimetype(self):
		return self.bindata.mimetype

