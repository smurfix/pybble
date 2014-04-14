
class WikiPage(Object):
	"""\
		A wiki (or similar) page.
		Parent: The "main" wikipage we're a parent of, or whatever parent there is
		Superparent: Our site (main page) or empty (subpage)
		Owner: Whoever created the page

		Wiki pages are not (yet?) nested.
		"""
	__tablename__ = "wikipage"
	__mapper_args__ = {'polymorphic_identity': 9}

	name = Column(Unicode, nullable=False)
	data = Column(Unicode)
	mainpage = Column(Boolean, default=True, nullable=False) # main-linked page?
	modified = DateTime(default_factory=datetime.utcnow)

	def __storm_pre_flush__(self):
		self.modified = datetime.utcnow()
		super(WikiPage,self).__storm_pre_flush__()

	def __init__(self, name, data):
		super(WikiPage,self).__init__()
		self.name = name
		self.data = data
	
	def url_html_view(self):
		from pybble.render import url_for
		if self.mainpage:
			return url_for("pybble.part.wikipage.viewer", name=self.name)
		if isinstance(self.parent,WikiPage) and self.parent.mainpage:
			return url_for("pybble.part.wikipage.viewer", name=self.name, parent=self.parent.name)

