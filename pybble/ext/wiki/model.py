##BP

from flask import url_for

from sqlalchemy import Column,Unicode,Boolean,DateTime

from pybble.core.models import ObjectRef
from pybble.core.models._descr import D

class WikiPage(ObjectRef):
	"""\
		A wiki (or similar) page.
		Parent: The "main" wikipage we're a parent of, or whatever parent there is
		Superparent: Our site (main page) or empty (subpage)
		Owner: Whoever created the page

		Wiki pages are not (yet?) nested.
		"""
	_descr = D.WikiPage

	name = Column(Unicode, nullable=False)
	data = Column(Unicode)
	mainpage = Column(Boolean, default=True, nullable=False) # main-linked page?
	modified = Column(DateTime, default=datetime.utcnow)

	def __init__(self, name, data):
		super(WikiPage,self).__init__()
		self.name = name
		self.data = data
	
	def url_html_view(self):
		if self.mainpage:
			return url_for("root.wikipage.viewer", name=self.name)
		if isinstance(self.parent,WikiPage) and self.parent.mainpage:
			return url_for("root.wikipage.viewer", name=self.name, parent=self.parent.name)

