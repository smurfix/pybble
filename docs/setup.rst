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

	pybble -S core schema --exec
	pybble -S core populate
	pybble -S core migrate stamp head

You now have a basic Pybble installation.

	pybble run 

You now can access the main root at http://localhost/5000.
If you're using a remote desktop,

	pybble run --host 0.0.0.0

(or the machine's internal IP address) will be usable; an alias entry
for the server's domain-less hostname has been created. If your browser
cannot resolve that name, add it to your /etc/hosts file for now; you
will discover ways to teach Pybble about alternate host names later.

Database upgrades
-----------------

Pybbles uses `Flask-Migrate` (which uses Alembic) to manage database
transitions.

After changing the schema, do

	pybble -S core migrate revision --auto

You will then find a new file in `migrations/versions` which applies your
changes to the database. Edit this file as appropriate, and add it to the
git revision that contains your changes.

To upgrade the actual database, run

	pybble -S core migrate upgrade

Note that Alembic does not find some changes, e.g. altered column lengths.
An alternate solution is to run `dbdiff`, which is packaged with Pybble:

	pybble -S core schema --diff

Depending on the database you use, this will likely report a large number
of spurious differences, but it _will_ notice when a column gets longer.

Because of the spurious-differences problem, the output of this program
needs to be applied selectively and manually.

