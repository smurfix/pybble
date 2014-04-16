##BP

"""\
Initial Descriptor list.
"""

class D(dict):
	def __call__(self,i,n):
		self[i]=n
		setattr(self,n,i)
D=D()

D(2,"User")
D(4,"Group")
D(5,"Site")
D(6,"Template")
D(8,"Verifier")
D(9,"WikiPage")
D(10,"Permission")
D(11,"GroupRef")
D(12,"TemplateMatch")
D(13,"Member")
D(14,"Breadcrumb")
D(15,"Change")
D(16,"Delete")
D(17,"Tracker")
D(18,"UserTracker")
D(19,"WantTracking")
D(20,"StaticFile")
D(21,"Storage")
D(22,"BinData")
D(23,"Comment")
D(24,"SiteBlueprint")
D(25,"App")
D(26,"Blueprint")
D(27,"ConfigVar")
D(28,"SiteConfigVar")
