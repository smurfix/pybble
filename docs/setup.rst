Setting up pybble
=================

Create a file named LOGIN.py with, at minimum, the following content:

	# -*- coding: utf-8 -*-
	sql_user="test"
	sql_pass="test"
	sql_database="test_pybble"
	SECRET_KEY="Change this, or risk being hacked!"
	ADMIN_EMAIL="you@your.domain.example"

Then, run

	pybble -S schema --exec
	pybble -S populate

You now have a basic Pybble installation.

	pybble run 

You now can access the main root at http://localhost/5000.
If you're using a remote desktop,

	pybble run --host 0.0.0.0

(or the machine's internal IP address) will be usable; an alias entry
for the server's domain-less hostname has been created. If your browser
cannot resolve that name, add it to your /etc/hosts file for now; you
will discover ways to teach Pybble about alternate host names later.

