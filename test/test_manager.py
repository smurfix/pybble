# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, division, unicode_literals
##
## This is part of Pybble, a WMS (Whatever Management System) based on
## Jinja2/Haml, Werkzeug, Flask, and Optimism.
##
## Pybble is Copyright © 2009-2014 by Matthias Urlichs <matthias@urlichs.de>,
## it is licensed under the GPLv3. See the file `README.md` for details,
## including an optimistic statements by the author.
##
## This paragraph is auto-generated and may self-destruct at any time,
## courtesy of "make update". The original is in ‘utils/_boilerplate.py’.
## Thus, please do not remove the next line, or insert any blank lines.
##BP


from .manager import ManagerTC
from pybble.manager.main import RootManager
from .script import capture

class TestManager(ManagerTC):
	@capture
	def test_simple_command_decorator(self, capsys):
		pass
		# TODO
		#code = self.run_manager('manage.py -t app hello --foo=fubar', app=self.app)
		#out, err = capsys.readouterr()
		#assert 'Oh hello' in out

