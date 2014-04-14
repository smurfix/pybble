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

import json
import logging
import datetime
import random
from flask import url_for, current_app
from flask.ext.misaka import markdown
from flask._compat import string_types
from flask._compat import implements_to_string as py2_unicode
from werkzeug import import_string
from werkzeug.utils import cached_property

from ..db import db
from . import BaseDocument

from quokka.utils.text import slugify

logger = logging.getLogger("pybble.models.docs")

@py2_unicode
class ContentType(db.Document):
	"""
	This collection lists the possible document classes.
	"""
	in_menu = db.ListField(db.ReferenceField('ContentType', reverse_delete_rule=db.DENY), verbose_name="Child content to include in menu")
	## TODO: add a mime type?

	meta = {
		'collection':'pybble_core_contenttype',
	}

	type = db.StringField(max_length=50, required=True, unique=True, verbose_name="Renderer's class path")
	#base = db.StringField(max_length=50, required=True, verbose_name="Content's base class")
	name = db.StringField(max_length=255, required=True)
	doc = db.StringField()

	@classmethod
	def get(cls, doc):
		"""
		Get the ContentType object corresponding to whatever we find.

		:param doc: can be
		            * a RenderedContent (sub)instance: return its type
		            * a ContentType instance: return it directly
		            * a Document: find the corresponding content type by class name
		"""
		if isinstance(doc,string_types):
			name = doc
		else:
			if isinstance(doc,RenderedContent):
				doc = doc.type
			if isinstance(doc,ContentType):
				return doc

			if isinstance(doc,Content):
				doc = doc.__class__
			elif not issubclass(doc,Content):
				raise RuntimeError("Don't know what to do with this",doc)

			name = doc.__module__+':'.doc.__name__
			doc = None
		#return cls.objects.get_or_create(type=name, defaults={'name':name, 'doc':(doc.__doc__ or '')})
		return cls.objects.get(type=name)
		# None.__doc__ is empty
	
	@cached_property
	def processor(self):
		return getattr(import_string(self.type),'render')

	def render(self,content, **aux):
		"""Translate this content to my output"""
		return self.processor(content=content, **aux)

	def __repr__(self):
		return "<%s: %s>" % (__class__.__name__, self.type)
	def __str__(self):
		return "%s:%s" % (__class__.__name__, self.type)

@py2_unicode
class RenderedContent(db.EmbeddedDocument):
	"""A rendered piece of content."""
	type = db.ReferenceField(ContentType, required=True)
	meta = {
		'allow_inheritance': True,
	}
	def __repr__(self):
		return "<%s: %s>" % (__class__.__name__, self.type.type)
	def __str__(self):
		return "%s:%s" % (__class__.__name__, self.type.type)

#	def aux_data(self, desttype):
#		return {}
	def render_as(self,desttype, **aux):
#		for k,v in self.aux_data(desttype):
#			aux.setdefault(k,v)
		return self.type.render(content=self, **aux)

class RenderedText(RenderedContent):
	"""Some text; the type determines how it's displayed"""
	text = db.StringField()

#class SiteTemplate(BaseDocument):
#	"""Site-specific Template data that's in the database"""
#	name = db.StringField(max_length=255, required=True, unique_with=('site',))
#	path = db.StringField(max_length=255, required=True, unique_with=('site',))
#	content = db.StringField()
#	type = db.ReferenceField(ContentType, required=True, reverse_delete_rule=db.DENY)
#	meta = {
#		'collection':'pybble_core_template',
#	}

@py2_unicode
class Content(BaseDocument):
	"""
	Anything that can have its own page and that can legitimately be described as 'content'.
	"""
	title = db.StringField(max_length=255, required=True)
	slug = db.StringField(max_length=255, required=True)
	summary = db.EmbeddedDocumentField(RenderedText)
	parent = db.ReferenceField('Content', required=False,reverse_delete_rule=db.DENY)

	order = db.IntField(default=0, verbose_name="Sort order in parent's content")
	in_menu = db.BooleanField(default=True, verbose_name="include in parent menu")
	main_content = db.BooleanField(default=True, verbose_name="include in parent body")

	created_at = db.DateTimeField(default=datetime.datetime.now)

	def __repr__(self):
		return "<%s.%s: %s>" % (self.__class__.__module__,self.__class__.__name__, self.slug or self.id)
	def __str__(self):
		return "%s.%s:%s" % (self.__class__.__module__,self.__class__.__name__, self.slug or self.id)

	meta = {
		'allow_inheritance': True,
		'indexes': [('order','-created_at'), 'slug'],
		'ordering': ['order','-created_at'],
		'collection':'pybble_core_content',
	}

#	def aux_data(self, desttype):
#		return {}

	def render_as(self,desttype, **aux):
		"""
		Convert me to some other type.

		This defaults to looking up the other type's class and (if it's
		text) running a template; if you need special handling for some
		types, override this.

		If the destination can't do it, try the same thing with the summary
		text.
		"""
		desttype = ContentType.get(desttype)

#		for k,v in self.aux_data(desttype):
#			aux.setdefault(k,v)
		try:
			return desttype.render(content=content, **aux)
		except NotImplementedError:
			return self.summary.render_as(desttype, orig=self)
		
class TextContent(Content):
	text = db.StringField(required=True)

#	def get_uid(self):
#		return str(self.id)
#
#	def get_themes(self):
#		themes = self.channel.get_themes()
#		theme = self.template_type and self.template_type.theme_name
#		if theme:
#			themes.insert(0, theme)
#		return list(set(themes))
#
#	def get_absolute_url(self, endpoint='detail'):
#		if self.channel.is_homepage:
#			long_slug = self.slug
#		else:
#			long_slug = self.long_slug
#
#		try:
#			return url_for(self.URL_NAMESPACE, long_slug=long_slug)
#		except:
#			return url_for(endpoint, long_slug=long_slug)
#
#	def get_canonical_url(self, *args, **kwargs):
#		return self.get_absolute_url()
#
#	def get_recommendations(self, limit=3, ordering='-created_at', *a, **k):
#		now = datetime.datetime.now()
#		filters = {
#			'published': True,
#			'available_at__lte': now,
#			"id__ne": self.id
#		}
#		contents = Content.objects(**filters).filter(tags__in=self.tags or [])
#
#		return contents.order_by(ordering)[:limit]
#
#	def get_summary(self):
#		if self.summary:
#			return self.summary
#		return self.get_text()
#
#	def get_text(self):
#		if hasattr(self, 'body'):
#			text = self.body
#		elif hasattr(self, 'description'):
#			text = self.description
#		else:
#			text = self.summary
#
#		if self.content_format == "markdown":
#			return markdown(text)
#		else:
#			return text
#
#	def __unicode__(self):
#		return self.title
#
#	@property
#	def model_name(self):
#		return self.__class__.__name__.lower()
#
#	@property
#	def module_name(self):
#		module = self.__module__
#		module_name = module.replace('quokka.modules.', '').split('.')[0]
#		return module_name
#
#	def heritage(self):
#		self.model = "{0}.{1}".format(self.module_name, self.model_name)
#
#	def save(self, *args, **kwargs):
#		self.validate_slug()
#		self.validate_long_slug()
#		self.heritage()
#		super(Content, self).save(*args, **kwargs)
#
#class Link(Content):
#	link = db.StringField(required=True)
