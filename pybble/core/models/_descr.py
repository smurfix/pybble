##BP

"""\
Initial Descriptor list.
"""

class D(dict):
	_doc = {}
	def __call__(self,i,n, doc=None):
		self[i]=n
		setattr(self,n,i)
		if doc:
			self._doc[i] = doc
D=D()

D(2,"User", "A user on this site")
D(4,"Group", "A group of users")
D(5,"Site", "A web site: domain plus content")
D(6,"Template", "How to display an onject")
D(8,"Verifier", "Holds a marker that the user needs to enter in order to proceed")
D(10,"Permission", "Describes access rights of a user to an object (tree)")
D(11,"GroupRef")
D(12,"TemplateMatch", "Describes a place to display a template at.")
D(13,"Member", "Generic association of objects to something they belong to")
D(14,"Breadcrumb", "indicates that a site visitor has accessed something")
D(15,"Change", "Record of a changed entry, including old contents / diff")
D(16,"Delete", "Records object deletion and old contents")
D(17,"Tracker", "Records any kind of change, for RSS / notification mails")
D(19,"WantTracking", "Record indicating a user's interest in change notifications to an object (tree)")
D(18,"UserTracker", "An entry to be accumulated for RSS / converted to a notification mail")
D(21,"Storage", "A place to store files")
D(22,"BinData", "Describes a single stored file")
D(20,"StaticFile", "Attaches a BinData object to a site's path")
D(23,"Comment", "User comment on an arbitrary object")
D(25,"App", "Code which drives a domain")
D(26,"Blueprint", "Code which displays a domain's content")
D(24,"SiteBlueprint", "Attaches a blueprint to a site")
D(27,"ConfigVar", "System-wide (default) configuration")
D(28,"SiteConfigVar", "Site-or-whatever-specific configuration")

D(9,"WikiPage")
