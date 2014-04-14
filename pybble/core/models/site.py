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

class DummySite(DummyObject):
	"""A site without content."""
	def __init__(self,domain,name=None):
		if name is None:
			name=u"Here be "+domain
		self.domain=unicode(domain)
		self.name=name
		try:
			self.parent = db.get_by(Site,domain=u"")
		except NoResult:
			pass
		else:
			self.parent_id = self.parent.id
	def oid(self): return "DummySite"
	def get_template(self, detail=TM_DETAIL_PAGE):
		if isinstance(self,DummySite) and detail == TM_DETAIL_SUBPAGE:
			raise MissingDummy
		if not self.parent:
			raise NoResult
		return self.parent.get_template(detail)

@py2_unicode
class App(Base):
	"""An App known to pybble"""
	__tablename__ = "apps"

	path = Column(Unicode, nullable=False)
	name = Column(Unicode, nullable=False)
	doc = Column(Unicode, nullable=True)

	def __str__(self):
		return u"‹App ‚%s‘ @ %s›" % (self.name, self.path)
	__repr__ = __str__

@py2_unicode
class Blueprint(Base):
	"""A Flask blueprint known to pybble"""
	__tablename__ = "blueprints"

	path = Column(Unicode, nullable=False)
	name = Column(Unicode, nullable=False)
	doc = Column(Unicode, nullable=True)

	def __str__(self):
		return u"‹Blueprint ‚%s‘ @ %s›" % (self.name, self.path)
	__repr__ = __str__

@py2_unicode
class Site(Object):
	"""A web domain. 'owner' is set to the domain's superuser."""
	__tablename__ = "sites"
	__mapper_args__ = {'polymorphic_identity': 5}

	domain = Column(Unicode, nullable=False)
	name = Column(Unicode, nullable=False)
	tracked = DateTime(nullable=False, default_factory=datetime.utcnow)
	## Datestamp of newest fully-processed Tracker object

	storage_id = Column(Integer, nullable=True)
	storage = Reference(storage_id,Storage.id)

	app_id = Column(Integer, nullable=True)
	app = Reference(app_id,App.id)

	def __storm_pre_flush__(self):
		self.tracked = datetime.utcnow()
		super(Site,self).__storm_pre_flush__()

	def __init__(self,domain,name=None):
		super(Site,self).__init__()
		if name is None:
			name=u"Here be "+domain
		self.domain=unicode(domain)
		self.name=name

		try:
			s = db.get_by(Site,domain=u"")
		except NoResult:
			if domain == "":
				s = None
			else:
				s = Site(name=u"Main default site",domain=u"")
				db.store.add(s)
		self.parent = s

		try:
			self.owner = current_request.user
		except (AttributeError,RuntimeError):
			self.owner = None
		db.store.add(self)
		u = User(u"",u"")
		u.superparent = self
		db.store.add(u)

	@property
	def anon_user(self):
		while True:
			try:
				return db.get_by(User, superparent_id=self.id, username=u"", password=u"")
			except NoResult:
				if site.parent:
					site = site.parent
				else:
					raise

		
	def __str__(self):
		return u"‹Site ‚%s‘ @ %s›" % (self.name, self.domain)
	__repr__ = __str__

	@property
	def data(self):
		return u"""\
name: %s
domain: %s
""" % (self.name,self.domain)

@py2_unicode
class SiteBlueprint(Base):
	"""A blueprint attached to a site's path"""
	__tablename__ = "site_blueprint"

	path = db.StringField(required=True, verbose_name="where to
			attach")

	## Datestamp of newest fully-processed Tracker object

	storage_id = Column(Integer, nullable=True)
	storage = Reference(storage_id,Storage.id)

	app_id = Column(Integer, nullable=True)
	app = Reference(app_id,App.id)

class Template(Object):
	"""
		A template for rendering.
		parent: Site the template applies to.
		owner: user who created the template.
		"""
	__tablename__ = "templates"
	__mapper_args__ = {'polymorphic_identity': 6}

	name = Column(Unicode, nullable=False)
	data = Column(Unicode)
	modified = DateTime(default_factory=datetime.utcnow)

	def __storm_pre_flush__(self):
		self.modified = datetime.utcnow()
		super(Template,self).__storm_pre_flush__()

	def __init__(self, name, data, parent=None):
		super(Template,self).__init__()
		self.name = name
		self.data = data
		self.owner = current_request.user
		self.parent = parent or current_request.site
		self.superparent = getattr(parent,"site",None) or current_request.site

	def __repr__(self):
		return "'<%s:%d>'" % (self.__class__.__name__,self.id)
