##BP

import os
from importlib import import_module

from flask import render_template, abort
from jinja2 import TemplateNotFound

from flask.ext.admin import AdminIndexView, expose
from flask.ext.admin import BaseView as AdminBaseView

from .. import BaseBlueprint

class TheView(AdminBaseView):
	@expose('/')
	def index(self):
		self._template_args['model'] = self.base.model
		return self.render(['admin/index.haml','admin/index.html'])

class FakeAdmin(object):
	def __init__(self,bp):
		self.url = bp.url_prefix
	def menu(self):
		return ()
	def menu_links(self):
		return ()
	subdomain = None
	static_url_path = "/static"
	url = None
	base_template="admin/base.html"

class Blueprint(BaseBlueprint):
	"""
	Admin frontend for a specific document class.
	Parameters:
	* model   which model to process
	* index   whether to generate an index page
	"""
	def has_params(self):
		super(Blueprint,self).has_params()
		try:
			base,model = self.params['model'].rsplit('.',1)
		except KeyError:
			pass
		else:
			base = import_module(base)
			self.model = getattr(base,model)
		self.view = TheView(self.name+"_view", endpoint=self.name, url=self.url_prefix)
		self.view.base = self
		view_bp = self.view.create_blueprint(FakeAdmin(self))
		view_bp.name = self.name+"_view"
		self.app.register_blueprint(view_bp)

		static_folder=os.path.join(os.path.dirname(os.path.abspath(os.path.dirname(__name__))),'static')
		def send_file(filename):
			return send_from_directory(static_folder, filename)
		self.app.add_url_rule(self.url_prefix + '/static/<path:filename>', endpoint='admin.static', view_func=send_file)

