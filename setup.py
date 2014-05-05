#!/usr/bin/env python
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

from setuptools import setup, find_packages

import pybble.version as V

kwargs = {}
try:
	from babel.messages import frontend as babel
	kwargs['cmdclass'] = {
		'extract_messages': babel.extract_messages,
		'update_catalog': babel.update_catalog,
		'compile_catalog': babel.compile_catalog,
		'init_catalog': babel.init_catalog,
	}
	kwargs['message_extractors'] = {
		'pybble': [
			('**.py', 'python', None),
			('**/templates/**.html', 'jinja2', {
				'extensions': (
					'jinja2.ext.autoescape,'
					'jinja2.ext.with_,'
					'jinja2.ext.do,'
				)
			})
		]
	}
except ImportError:
	pass

REQUIREMENTS = [i.strip() for i in open("requirements.txt").readlines()
				if not i.startswith("http")]

dependency_links = [i.strip() for i in open("requirements.txt").readlines()
					if i.startswith("http")]

classifiers = [
	"Development Status :: 3 - Alpha",
	"Environment :: Web Environment",
	"Framework :: Flask",
	"Intended Audience :: Developers",
	"License :: OSI Approved :: GPLv3",
	"Natural Language :: English",
	"Operating System :: MacOS :: MacOS X",
	"Operating System :: POSIX :: Linux",
	"Programming Language :: JavaScript",
	"Programming Language :: Python :: 2.7",
	'Programming Language :: Python',
	"Topic :: Internet :: WWW/HTTP :: Dynamic Content",
	'Topic :: Software Development :: Libraries :: Python Modules'
]

try:
	long_description = open('README.md').read()
except:
	long_description = V.description

setup(name='pybble',
	  version=V.version,
	  description=V.description,
	  long_description=long_description,
	  classifiers=classifiers,
	  keywords='pybble cms flask publishing mongodb',
	  author=V.author,
	  author_email=V.email,
	  url='http://pybble.smurf.noris.de',
	  download_url="https://github.com/smurfix/pybble/tarball/master",
	  license=V.license,
	  packages=find_packages(exclude=('doc', 'docs',)),
	  package_dir={'pybble': 'pybble'},
	  install_requires=REQUIREMENTS,
	  dependency_links=dependency_links,
	  include_package_data=True,
	  test_suite='nose.collector',
	  **kwargs)
