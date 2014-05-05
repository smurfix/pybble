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

import re
import sys
from functools import wraps

from flask import Flask
from flask.ext.script._compat import StringIO, text_type
from flask.ext.script import Command, Manager, Option, prompt, prompt_bool

from pytest import raises
from .base import TC

## This is flask_script's test case, rewritten for testing with nose

class Catcher(object):
	"""Helper decorator to test raw_input."""
	## see: http://stackoverflow.com/questions/13480632/python-stringio-selectively-place-data-into-stdin

	def __init__(self, handler):
		self.handler = handler
		self.inputs = []

	def __enter__(self):
		self.__stdin  = sys.stdin
		self.__stdout = sys.stdout
		sys.stdin = self
		sys.stdout = self

	def __exit__(self, type, value, traceback):
		sys.stdin  = self.__stdin
		sys.stdout = self.__stdout

	def write(self, value):
		self.__stdout.write(value)
		result = self.handler(value)
		if result is not None:
			self.inputs.append(result)

	def readline(self):
		return self.inputs.pop()

	def getvalue(self):
		return self.__stdout.getvalue()

	def truncate(self, pos):
		return self.__stdout.truncate(pos)

class StdoutWrap(object):
	def __init__(self,base,attr):
		self.base = base
		self.attr = attr
	def write(self, value):
		setattr(self.base,self.attr, getattr(self.base,self.attr)+value)

class CapSys(object):
	def __init__(self):
		self.out,self.err = "",""
	def __enter__(self):
		self.__stdout = sys.stdout
		self.__stderr = sys.stderr
		sys.stdout = StdoutWrap(self,"out")
		sys.stderr = StdoutWrap(self,"err")
		return self

	def __exit__(self, a,b,c):
		sys.stdout = self.__stdout
		sys.stderr = self.__stderr
	
	def readouterr(self):
		out,err = self.out,self.err
		self.out,self.err = "",""
		return out,err

def capture(x):
	@wraps(x)
	def runner(self):
		with CapSys() as cap:
			x(self,cap)
	return runner

def run(command_line, manager_run):
	'''
		Returns tuple of standard output and exit code
	'''
	sys.argv = command_line.split()
	exit_code = None
	try:
		manager_run()
	except SystemExit as e:
		exit_code = e.code

	return exit_code

