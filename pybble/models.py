from datetime import datetime
from sqlalchemy import Table, Column, String, Boolean, DateTime, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from pybble.utils import Session, metadata, url_for, get_random_uid
from pybble.database import db

Base = declarative_base()

class Object(Base):
	__tablename__ = "obj"
	__table_args__ = {'useexisting': True}
	query = db.session.query_property()

	id = Column(Integer(20), primary_key=True)
	discriminator = Column(Integer)
	__mapper_args__ = {'polymorphic_on': discriminator}


class URL(Object):
	__tablename__ = "urls"
	__table_args__ = {'useexisting': True}
	__mapper_args__ = {'polymorphic_identity': 1}

	query = db.session.query_property()

	id = Column(Integer, ForeignKey('obj.id'), primary_key=True)
	        
	uid = Column(String(140))
	target = Column(String(500))
	added = Column(DateTime)
	public = Column(Boolean)

	def __init__(self, target, public=True, uid=None, added=None):
		self.target = target
		self.public = public
		self.added = added or datetime.utcnow()
		if not uid:
			while 1:
				uid = get_random_uid()
				if not URL.query.get(uid):
					break
		self.uid = uid

	@property
	def short_url(self):
		return url_for('link', uid=self.uid, _external=True)

	def __repr__(self):
		return '<URL %r>' % self.uid

#Session.mapper(URL, url_table)
