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

class SimpleCommand(Command):
	'simple command'

	def run(self):
		print('OK')

class NamedCommand(Command):
	'named command'

	def run(self):
		print('OK')

class ExplicitNamedCommand(Command):
	'named command'

	name = 'named'

	def run(self):
		print('OK')

class NamespacedCommand(Command):
	'namespaced command'

	namespace = 'ns'

	def run(self):
		print('OK')

class CommandWithArgs(Command):
	'command with args'

	option_list = (
		Option('name'),
	)

	def run(self, name):
		print(name)

class CommandWithOptions(Command):
	'command with options'

	option_list = (
		Option('-n', '--name',
			   help='name to pass in',
			   dest='name'),
	)

	def run(self, name):
		print(name)

class CommandWithDynamicOptions(Command):
	'command with options'

	def __init__(self, default_name='Joe'):
		self.default_name = default_name

	def get_options(self):

		return (
			Option('-n', '--name',
				   help='name to pass in',
				   dest='name',
				   default=self.default_name),
		)

	def run(self, name):
		print(name)

class CommandWithCatchAll(Command):
	'command with catch all args'

	capture_all_args = True

	def get_options(self):
		return (Option('--foo', dest='foo',
					   action='store_true'),)

	def run(self, remaining_args, foo):
		print(remaining_args)

class TestRunCommands(TC):

	TESTING = True

	def setup(self):

		self.app = Flask(__name__)
		self.app.config.from_object(self)

class TestScripting:

	TESTING = True

	def setup(self):

		self.app = Flask(__name__)
		self.app.config.from_object(self)

	@capture
	def test_simple_command_decorator(self, capsys):

		manager = Manager(self.app)

		@manager.command
		def hello():
			print('hello')

		assert 'hello' in manager._commands

		code = run('manage.py hello', manager.run)
		out, err = capsys.readouterr()
		assert 'hello' in out

	@capture
	def test_simple_command_decorator_with_pos_arg(self, capsys):

		manager = Manager(self.app)

		@manager.command
		def hello(name):
			print('hello ' + name)

		assert 'hello' in manager._commands

		code = run('manage.py hello joe', manager.run)
		out, err = capsys.readouterr()
		assert 'hello joe' in out

	@capture
	def test_command_decorator_with_options(self, capsys):

		manager = Manager(self.app)

		@manager.command
		def hello(name='fred'):
			'Prints your name'
			print('hello ' + name)

		assert 'hello' in manager._commands

		code = run('manage.py hello --name=joe', manager.run)
		out, err = capsys.readouterr()
		assert 'hello joe' in out

		code = run('manage.py hello -n joe', manager.run)
		out, err = capsys.readouterr()
		assert 'hello joe' in out

		code = run('manage.py hello -?', manager.run)
		out, err = capsys.readouterr()
		assert 'Prints your name' in out

		code = run('manage.py hello --help', manager.run)
		out, err = capsys.readouterr()
		assert 'Prints your name' in out

	@capture
	def test_command_decorator_with_boolean_options(self, capsys):

		manager = Manager(self.app)

		@manager.command
		def verify(verified=False):
			'Checks if verified'
			print('VERIFIED ? ' + 'YES' if verified else 'NO')

		assert 'verify' in manager._commands

		code = run('manage.py verify --verified', manager.run)
		out, err = capsys.readouterr()
		assert 'YES' in out

		code = run('manage.py verify -v', manager.run)
		out, err = capsys.readouterr()
		assert 'YES' in out

		code = run('manage.py verify', manager.run)
		out, err = capsys.readouterr()
		assert 'NO' in out

		code = run('manage.py verify -?', manager.run)
		out, err = capsys.readouterr()
		assert 'Checks if verified' in out

	@capture
	def test_simple_command_decorator_with_pos_arg_and_options(self, capsys):

		manager = Manager(self.app)

		@manager.command
		def hello(name, url=None):
			if url:
				assert type(url) is text_type
				print('hello ' + name + ' from ' + url)
			else:
				assert type(name) is text_type
				print('hello ' + name)

		assert 'hello' in manager._commands

		code = run('manage.py hello joe', manager.run)
		out, err = capsys.readouterr()
		assert 'hello joe' in out

		code = run('manage.py hello joe --url=reddit.com', manager.run)
		out, err = capsys.readouterr()
		assert 'hello joe from reddit.com' in out

	@capture
	def test_command_decorator_with_additional_options(self, capsys):

		manager = Manager(self.app)

		@manager.option('-n', '--name', dest='name', help='Your name')
		def hello(name):
			print('hello ' + name)

		assert 'hello' in manager._commands

		code = run('manage.py hello --name=joe', manager.run)
		out, err = capsys.readouterr()
		assert 'hello joe' in out

		code = run('manage.py hello -?', manager.run)
		out, err = capsys.readouterr()
		assert 'Your name' in out

		@manager.option('-n', '--name', dest='name', help='Your name')
		@manager.option('-u', '--url', dest='url', help='Your URL')
		def hello_again(name, url=None):
			if url:
				print('hello ' + name + ' from ' + url)
			else:
				print('hello ' + name)

		assert 'hello_again' in manager._commands

		code = run('manage.py hello_again --name=joe', manager.run)
		out, err = capsys.readouterr()
		assert 'hello joe' in out

		code = run('manage.py hello_again --name=joe --url=reddit.com', manager.run)
		out, err = capsys.readouterr()
		assert 'hello joe from reddit.com' in out

	@capture
	def test_global_option_provided_before_and_after_command(self, capsys):

		manager = Manager(self.app)
		manager.add_option('-c', '--config', dest='config_name', required=False, default='Development')
		manager.add_command('simple', SimpleCommand())

		assert isinstance(manager._commands['simple'], SimpleCommand)

		code = run('manage.py -c Development simple', manager.run)
		out, err = capsys.readouterr()
		assert code == 0
		assert 'OK' in out

	@capture
	def test_global_option_value(self, capsys):

		def create_app(config_name='Empty'):
			print(config_name)
			return self.app

		manager = Manager(create_app)
		manager.add_option('-c', '--config', dest='config_name', required=False, default='Development')
		manager.add_command('simple', SimpleCommand())

		assert isinstance(manager._commands['simple'], SimpleCommand)

		code = run('manage.py simple', manager.run)
		out, err = capsys.readouterr()
		assert code == 0
		assert 'Empty' not in out  # config_name is overwritten by default option value
		assert 'Development' in out
		assert 'OK' in out

	def test_get_usage(self):

		manager = Manager(self.app)
		manager.add_command('simple', SimpleCommand())

		usage = manager.create_parser('manage.py').format_help()
		assert 'simple command' in usage

	def test_get_usage_with_specified_usage(self):

		manager = Manager(self.app, usage='hello')
		manager.add_command('simple', SimpleCommand())

		usage = manager.create_parser('manage.py').format_help()
		assert 'simple command' in usage
		assert 'hello' in usage

	@capture
	def test_run_existing_command(self, capsys):

		manager = Manager(self.app)
		manager.add_command('simple', SimpleCommand())
		code = run('manage.py simple', manager.run)
		out, err = capsys.readouterr()
		assert 'OK' in out

	@capture
	def test_run_non_existant_command(self, capsys):

		manager = Manager(self.app)
		run('manage.py simple', manager.run)
		out, err = capsys.readouterr()
		assert 'invalid choice' in err

	@capture
	def test_run_existing(self, capsys):

		manager = Manager(self.app)
		manager.add_command('simple', SimpleCommand())

		code = run('manage.py simple', manager.run)
		out, err = capsys.readouterr()
		assert 0 == code
		assert 'OK' in out

	@capture
	def test_run_existing_bind_later(self, capsys):

		manager = Manager(self.app)

		code = run('manage.py simple', lambda: manager.run({'simple': SimpleCommand()}))
		out, err = capsys.readouterr()
		assert code == 0
		assert 'OK' in out

	@capture
	def test_run_not_existing(self, capsys):

		manager = Manager(self.app)

		code = run('manage.py simple', manager.run)
		out, err = capsys.readouterr()
		assert code == 2
		assert 'OK' not in out

	@capture
	def test_run_no_name(self, capsys):

		manager = Manager(self.app)
		manager.add_command('simple', SimpleCommand())

		code = run('manage.py', manager.run)
		out, err = capsys.readouterr()
		assert code == 2
		assert 'simple command' in out

	@capture
	def test_run_good_options(self, capsys):

		manager = Manager(self.app)
		manager.add_command('simple', CommandWithOptions())

		code = run('manage.py simple --name=Joe', manager.run)
		out, err = capsys.readouterr()
		assert code == 0
		assert 'Joe' in out

	@capture
	def test_run_dynamic_options(self, capsys):

		manager = Manager(self.app)
		manager.add_command('simple', CommandWithDynamicOptions('Fred'))

		code = run('manage.py simple', manager.run)
		out, err = capsys.readouterr()
		assert code == 0
		assert 'Fred' in out

	@capture
	def test_run_catch_all(self, capsys):
		manager = Manager(self.app)
		manager.add_command('catch', CommandWithCatchAll())

		code = run('manage.py catch pos1 --foo pos2 --bar', manager.run)
		out, err = capsys.readouterr()
		assert code == 0
		assert "['pos1', 'pos2', '--bar']" in out

	@capture
	def test_run_bad_options(self, capsys):
		manager = Manager(self.app)
		manager.add_command('simple', CommandWithOptions())

		code = run('manage.py simple --foo=bar', manager.run)
		assert code == 2

	def test_init_with_flask_instance(self):
		manager = Manager(self.app)
		assert callable(manager.app)

	def test_init_with_callable(self):
		manager = Manager(lambda: self.app)
		assert callable(manager.app)

	def test_raise_index_error(self):

		manager = Manager(self.app)

		@manager.command
		def error():
			raise IndexError()

		with raises(IndexError):
			run('manage.py error', manager.run)

	@capture
	def test_run_with_default_command(self, capsys):
		manager = Manager(self.app)
		manager.add_command('simple', SimpleCommand())

		code = run('manage.py', lambda: manager.run(default_command='simple'))
		out, err = capsys.readouterr()
		assert code == 0
		assert 'OK' in out

	@capture
	def test_command_with_prompt(self, capsys):

		manager = Manager(self.app)

		@manager.command
		def hello():
			print(prompt(name='hello'))

		@Catcher
		def hello_john(msg):
			if re.search("hello", msg):
				return 'john'

		with hello_john:
			code = run('manage.py hello', manager.run)
			out, err = capsys.readouterr()
			assert 'hello: john' in out

	@capture
	def test_command_with_default_prompt(self, capsys):

		manager = Manager(self.app)

		@manager.command
		def hello():
			print(prompt(name='hello', default='romeo'))

		@Catcher
		def hello(msg):
			if re.search("hello", msg):
				return '\n'  # just hit enter

		with hello:
			code = run('manage.py hello', manager.run)
			out, err = capsys.readouterr()
			assert 'hello [romeo]: romeo' in out

		@Catcher
		def hello_juliette(msg):
			if re.search("hello", msg):
				return 'juliette'

		with hello_juliette:
			code = run('manage.py hello', manager.run)
			out, err = capsys.readouterr()
			assert 'hello [romeo]: juliette' in out

	@capture
	def test_command_with_prompt_bool(self, capsys):

		manager = Manager(self.app)

		@manager.command
		def hello():
			print(prompt_bool(name='correct', default=True, yes_choices=['y'],
							  no_choices=['n']) and 'yes' or 'no')

		@Catcher
		def correct_default(msg):
			if re.search("correct", msg):
				return '\n'  # just hit enter

		@Catcher
		def correct_y(msg):
			if re.search("correct", msg):
				return 'y'

		@Catcher
		def correct_n(msg):
			if re.search("correct", msg):
				return 'n'

		with correct_default:
			code = run('manage.py hello', manager.run)
			out, err = capsys.readouterr()
			assert 'correct [y]: yes' in out

		with correct_y:
			code = run('manage.py hello', manager.run)
			out, err = capsys.readouterr()
			assert 'correct [y]: yes' in out

		with correct_n:
			code = run('manage.py hello', manager.run)
			out, err = capsys.readouterr()
			assert 'correct [y]: no' in out

class TestSubScripting:

	TESTING = True

	def setup(self):

		self.app = Flask(__name__)
		self.app.config.from_object(self)

	def test_add_submanager(self):

		sub_manager = Manager()

		manager = Manager(self.app)
		manager.add_command('sub_manager', sub_manager)

		assert isinstance(manager._commands['sub_manager'], Manager)
		assert sub_manager.parent == manager
		assert sub_manager.get_options() == manager.get_options()

	@capture
	def test_run_submanager_command(self, capsys):

		sub_manager = Manager()
		sub_manager.add_command('simple', SimpleCommand())

		manager = Manager(self.app)
		manager.add_command('sub_manager', sub_manager)

		code = run('manage.py sub_manager simple', manager.run)
		out, err = capsys.readouterr()
		assert code == 0
		assert 'OK' in out

	@capture
	def test_submanager_has_options(self, capsys):

		sub_manager = Manager()
		sub_manager.add_command('simple', SimpleCommand())

		manager = Manager(self.app)
		manager.add_command('sub_manager', sub_manager)
		manager.add_option('-c', '--config', dest='config', required=False)

		code = run('manage.py sub_manager simple', manager.run)
		out, err = capsys.readouterr()
		assert code == 0
		assert 'OK' in out

		code = run('manage.py -c Development sub_manager simple', manager.run)
		out, err = capsys.readouterr()
		assert code == 0
		assert 'OK' in out

	@capture
	def test_manager_usage_with_submanager(self, capsys):

		sub_manager = Manager(usage='Example sub-manager')

		manager = Manager(self.app)
		manager.add_command('sub_manager', sub_manager)

		code = run('manage.py -?', manager.run)
		out, err = capsys.readouterr()
		assert code == 0
		assert 'Example sub-manager' in out

	@capture
	def test_submanager_usage_and_help_and_description(self, capsys):

		sub_manager = Manager(usage='sub_manager [--foo]',
							  help='shorter desc for submanager',
							  description='longer desc for submanager')
		sub_manager.add_command('simple', SimpleCommand())

		manager = Manager(self.app)
		manager.add_command('sub_manager', sub_manager)

		code = run('manage.py -?', manager.run)
		out, err = capsys.readouterr()
		assert code == 0
		assert 'sub_manager [--foo]' not in out
		assert 'shorter desc for submanager' in out
		assert 'longer desc for submanager' not in out

		code = run('manage.py sub_manager', manager.run)
		out, err = capsys.readouterr()
		assert code == 2
		assert 'sub_manager [--foo]' in out
		assert 'shorter desc for submanager' not in out
		assert 'longer desc for submanager' in out
		assert 'simple command' in out

		code = run('manage.py sub_manager -?', manager.run)
		out, err = capsys.readouterr()
		assert code == 0
		assert 'sub_manager [--foo]' in out
		assert 'shorter desc for submanager' not in out
		assert 'longer desc for submanager' in out
		assert 'simple command' in out

		code = run('manage.py sub_manager simple -?', manager.run)
		out, err = capsys.readouterr()
		assert code == 0
		assert 'sub_manager [--foo] simple [-?]' in out
		assert 'simple command' in out

	def test_submanager_has_no_default_commands(self):

		sub_manager = Manager()

		manager = Manager()
		manager.add_command('sub_manager', sub_manager)

		assert 'runserver' not in sub_manager._commands
		assert 'shell' not in sub_manager._commands
