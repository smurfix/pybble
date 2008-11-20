from datetime import datetime
from sqlalchemy import Table, Column, String, Unicode, Boolean, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relation,backref
from pybble.utils import url_for, random_string
from pybble.database import db

class Object(db.Base):
	__tablename__ = "obj"
	__table_args__ = {'useexisting': True}
	query = db.session.query_property(db.Query)

	id = Column(Integer(20), primary_key=True)

	discriminator = Column(Integer)
	__mapper_args__ = {'polymorphic_on': discriminator}

	owner_id = Column(Integer(20),ForeignKey('obj.id'))        # creating object/user
	parent_id = Column(Integer(20),ForeignKey('obj.id'))       # direct ancestor (replied-to comment)
	superparent_id = Column(Integer(20),ForeignKey('obj.id'))  # indirect ancestor (replied-to wiki page)

	#all_children = relation('Object', backref=backref("superparent", remote_side="Object.id")) 

Object.owner = relation(Object, remote_side=Object.id, primaryjoin=(Object.owner_id==Object.id))
Object.parent = relation(Object, remote_side=Object.id, primaryjoin=(Object.parent_id==Object.id))
Object.superparent = relation(Object, remote_side=Object.id, primaryjoin=(Object.superparent_id==Object.id))

Object.children = relation(Object, remote_side=Object.parent_id, primaryjoin=(Object.id==Object.parent_id)) 

class URL(Object):
	__tablename__ = "urls"
	__table_args__ = {'useexisting': True}
	__mapper_args__ = {'polymorphic_identity': 1}
	query = db.session.query_property(db.Query)
	id = Column(Integer, ForeignKey('obj.id'), primary_key=True)
	        
	uid = Column(Unicode(140))
	target = Column(Unicode(500))
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

class User(Object):
	__tablename__ = "users"
	__table_args__ = {'useexisting': True}
	__mapper_args__ = {'polymorphic_identity': 2}
	query = db.session.query_property(db.Query)
	id = Column(Integer, ForeignKey('obj.id'), primary_key=True)
	        
	username = Column(Unicode(30))
	first_name = Column(Unicode(30))
	last_name = Column(Unicode(30))
	email = Column(String(100))
	password = Column(String(30))
	verified = Column(Boolean)
	first_login = Column(DateTime)
	last_login = Column(DateTime)

	def __init__(self, username, password=None):
		self.username=username
		if password is None:
			password = random_string(9)
		self.password=password

#class Group(Object):
#	"""A group of users. (Usually.)"""
#	__tablename__ = "groups"
#	__table_args__ = {'useexisting': True}
#	__mapper_args__ = {'polymorphic_identity': 4}
#	query = db.session.query_property(db.Query)
#	id = Column(Integer, ForeignKey('obj.id'), primary_key=True)
#	        
#	name = Column(Unicode(30))
#	
#class Member(db.Base):
#	__tablename__ = "groupmembers"
#	query = db.session.query_property(db.Query)
#	id = Column(Integer, primary_key=True)
#
#	user_id = Column(Integer(20),ForeignKey(Obj.id))    # one member
#	group_id = Column(Integer(20),ForeignKey(Obj.id))   # membership group
#	
PERM_LIST=1
PERM_READ=2
PERM_WRITE=3
PERM_ADMIN=4

class Permission(db.Base):
	__tablename__ = "users"
	__table_args__ = {'useexisting': True}
	query = db.session.query_property(db.Query)
	id = Column(Integer(20), primary_key=True)

	user_id = Column(Integer(20),ForeignKey(Object.id))        # acting user/group
	obj_id = Column(Integer(20),ForeignKey(Object.id))         # affected object
	right = Column(Integer(1))

site_users = Table('site_users', db.Metadata,
    Column('site_id', Integer, ForeignKey('obj.id')),
    Column('user_id', Integer, ForeignKey('obj.id')))

class Site(Object):
	"""A web domain."""
	__tablename__ = "sites"
	__table_args__ = {'useexisting': True}
	__mapper_args__ = {'polymorphic_identity': 5}
	query = db.session.query_property(db.Query)
	id = Column(Integer, ForeignKey('obj.id'), primary_key=True)

	domain = Column(Unicode(100))
	name = Column(Unicode(50))

	def __init__(self,domain,name=None):
		if name is None:
			name="Here be "+domain
		self.domain=domain
		self.name=name

Site.users = relation(User, secondary=site_users, backref='sites', primaryjoin=(Object.id==site_users.c.site_id),
	secondaryjoin=(site_users.c.user_id==Object.id))


