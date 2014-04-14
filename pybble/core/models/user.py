#!/usr/bin/env python
# -*- coding: utf-8 -*-

frm . import Site
from ..db import db
from flask import current_app,g
from flask.ext.security import UserMixin, RoleMixin
from flask.ext.security.utils import encrypt_password
from mongoengine.queryset import queryset_manager

# Auth
class Role(db.Document, RoleMixin):
	name = db.StringField(max_length=80, unique_with=('site',))
	description = db.StringField(max_length=255)

	@classmethod
	def createrole(cls, name,site=None, description=None):
		if site is None:
			site = g.site
		return cls.objects.create(
			name=name,
			site=site,
			description=description
		)

	def __unicode__(self):
		return u"{0} ({1})".format(self.name, self.description or 'Role')


class User(db.DynamicDocument, UserMixin):
	name = db.StringField(max_length=255, unique=True)
	email = db.EmailField(max_length=255, unique=True)
	password = db.StringField(max_length=255)
	active = db.BooleanField(default=True)
	changed_at = db.DateTimeField()
	roles = db.ListField(
		db.ReferenceField(Role, reverse_delete_rule=db.DENY), default=[]
	)

	@queryset_manager
	def objects(cls, q):
		return q(roles__site__in=g.site.parents)

	last_login_at = db.DateTimeField()
	current_login_at = db.DateTimeField()
	last_login_ip = db.StringField(max_length=255)
	current_login_ip = db.StringField(max_length=255)
	login_count = db.IntField()

	username = db.StringField(max_length=50, required=False, unique=True)

	remember_token = db.StringField(max_length=255)
	authentication_token = db.StringField(max_length=255)

	def clean(self, *args, **kwargs):
		if not self.username:
			self.username = User.generate_username(self.email)

		 super(User, self).clean(*args, **kwargs)
#		try:
#			super(User, self).clean(*args, **kwargs)
#		except Exception:
#			pass

	@classmethod
	def generate_username(cls, email):
		username = email.lower()
		for item in ['@', '.', '-', '+']:
			username = username.replace(item, '_')
		return username

	def set_password(self, password, save=False):
		self.password = encrypt_password(password)
		if save:
			self.save()

	@classmethod
	def createuser(cls, name, email, password,
				   site=None, active=True, roles=None, username=None):

		username = username or cls.generate_username(email)
		if site is None:
			site = current_app.site
		return cls.objects.create(
			name=name,
			email=email,
			password=encrypt_password(password),
			active=active,
			roles=roles,
			username=username
		)

	@property
	def display_name(self):
		return self.name or self.email

	def __unicode__(self):
		return u"{0} <{1}>".format(self.name or '', self.email)

	@property
	def connections(self):
		return Connection.objects(user_id=str(self.id))


class Connection(db.Document):
	user_id = db.ObjectIdField()
	provider_id = db.StringField(max_length=255)
	provider_user_id = db.StringField(max_length=255)
	access_token = db.StringField(max_length=255)
	secret = db.StringField(max_length=255)
	display_name = db.StringField(max_length=255)
	full_name = db.StringField(max_length=255)
	profile_url = db.StringField(max_length=512)
	image_url = db.StringField(max_length=512)
	rank = db.IntField(default=1)

	@property
	def user(self):
		return User.objects(id=self.user_id).first()
