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

@py2_unicode
class TemplateMatch(Object):
	"""
		Associate a template to an object.
		Parent: The object which the template is for.
		"""
	__tablename__ = "template_match"
	__mapper_args__ = {'polymorphic_identity': 12}
	_proxy = { "obj":"parent" }

	data = Column(Unicode)
	modified = DateTime(default_factory=datetime.utcnow)

	def __storm_pre_flush__(self):
		self.modified = datetime.utcnow()
		super(TemplateMatch,self).__storm_pre_flush__()

	discr = Column(Integer, nullable=False)
	detail = Column(Integer, nullable=False)
	inherit = Column(Boolean, nullable=True)

	def __init__(self, obj,discr,detail, data):
		discr = Discriminator.get(discr,obj).id
		super(TemplateMatch,self).__init__()
		self.discr = discr
		self.detail = detail
		self.data = data
		db.store.add(self)
		self.parent = obj
		db.store.flush()
	
	def __str__(self):
		p,s,o,d = self.pso
		if self._rec_str or not p: return super(TemplateMatch,self).__str__()
		try:
			self._rec_str = True
		finally:
			return u'‹%s%s %s: %s %s %s %s›' % (d,self.__class__.__name__, self.id, TM_DETAIL[self.detail],db.get_by(Discriminator, id=self.discr).name,unicode(p), "*" if self.inherit is None else "Y" if self.inherit else "N")
			self._rec_str = False
	def __repr__(self):
		if not self.parent: return "'"+super(TemplateMatch,self).__repr__()+"'"
		return "'"+self.__str__()+"'"

