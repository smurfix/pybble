Setting up pybble
=================

Create a file named LOGIN.py with, at minimum, the following content:

	# -*- coding: utf-8 -*-
	mysql_user="test"
	mysql_pass="test"
	mysql_admin_user="test"
	mysql_admin_pass="test"
	mysql_database="test_pybble"
	SECRET_KEY="Change this, or risk being hacked!"

You can delete the Admin entries later.

Then, run

	pybble -S schema --exec
	pybble -S populate

You now have a basic Pybble installation.

