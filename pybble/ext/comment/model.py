
class Comment(renderObject):
	"""\
		A comment (or similar) page.
		Parent: The comment or page we're referring to.
		Superparent: The main page thus commented.
		Owner: Whoever created the comment
		"""
	__tablename__ = "comment"
	__mapper_args__ = {'polymorphic_identity': 23}
	
	name = Column(Unicode)
	data = Column(Unicode)
	added = DateTime(default_factory=datetime.utcnow)
	renderer_id = Column(Integer, nullable=True)
	renderer = Reference(renderer_id,Renderer)

	def __init__(self, obj, name, data, renderer = None):
		super(Comment,self).__init__()
		self.name = name
		self.data = data
		self.owner = request.user
		self.parent = obj
		if isinstance(obj,Comment):
			self.superparent = obj.superparent
		else:
			self.superparent = obj

		super(Comment,self).__init__(renderer)

