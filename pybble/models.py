from datetime import datetime
from sqlalchemy import Table, Column, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from pybble.utils import Session, metadata, url_for, get_random_uid
from pybble.database import db

Base = declarative_base()

class URL(Base):
	__tablename__ = "urls"
	__table_args__ = {'useexisting': True}
	query = db.session.query_property()

	uid = Column(String(140), primary_key=True)
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
