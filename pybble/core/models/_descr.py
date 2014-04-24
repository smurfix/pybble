##BP

"""\
Initial Descriptor list.
"""

class D(dict):
	_doc = {}
	def __call__(self,i,n, doc=None):
		self[i]=n
		setattr(self,n.rsplit(".")[-1],i)
		if doc:
			self._doc[i] = doc
D=D()

D(2,"user.User", "A user on this site")
D(4,"user.Group", "A group of users")
D(5,"site.Site", "A web site: domain plus content")
D(6,"template.Template", "How to display an onject")
D(8,"verifier.Verifier", "Holds a marker that the user needs to enter in order to proceed")
D(10,"user.Permission", "Describes access rights of a user to an object (tree)")
D(11,"user.GroupRef")
D(12,"template.TemplateMatch", "Describes a place to display a template at.")
D(13,"user.Member", "Generic association of objects to something they belong to")
D(14,"tracking.Breadcrumb", "indicates that a site visitor has accessed something")
D(15,"tracking.Change", "Record of a changed entry, including old contents / diff")
D(16,"tracking.Delete", "Records object deletion and old contents")
D(17,"tracking.Tracker", "Records any kind of change, for RSS / notification mails")
D(19,"tracking.WantTracking", "Record indicating a user's interest in change notifications to an object (tree)")
D(18,"tracking.UserTracker", "An entry to be accumulated for RSS / converted to a notification mail")
D(21,"storage.Storage", "A place to store files")
D(22,"storage.BinData", "Describes a single stored file")
D(20,"storage.StaticFile", "Attaches a BinData object to a site's path")
D(23,"x.Comment", "User comment on an arbitrary object")
D(25,"site.App", "Code which drives a domain")
D(26,"site.Blueprint", "Code which displays a domain's content")
D(24,"site.SiteBlueprint", "Attaches a blueprint to a site")
D(27,"site.ConfigVar", "System-wide (default) configuration")
D(28,"site.SiteConfigVar", "Site-or-whatever-specific configuration")

D(9,"x.WikiPage")
