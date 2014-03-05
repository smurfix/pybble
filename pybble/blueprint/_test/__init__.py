##BP

from pybble.blueprint import BaseBlueprint
from flask import render_template, abort
from jinja2 import TemplateNotFound

class Blueprint(BaseBlueprint):
	def add_routes(self):
		super(Blueprint,self).add_routes()

		@self.route('/red')
		def test_red():
			return "This is Red Color"

		@self.route('/green')
		def test_green():
			return render_template('green.haml')

		@self.route('/blue')
		def test_blue():
			return render_template('blue.html')
