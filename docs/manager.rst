The Manager frontend
====================

The management code allows you to do a basic site content setup.

python manage.py
----------------

-	Arguments

	-c CONFIG, --config CONFIG  Config file to use
	-s SITE, --site SITE        which Site to run on
	-v, --verbose               Enable verbose logging
	-t, --test                  Use the test database

-	blueprint

	The modules which actually process URLs are called Blueprint.
	
	-	doc

		Shows a blueprint's documentation string.

		-	Arguments

			name        The blueprint's internal name

		If no name is given, list all known blueprints.

	-	add

		Connect a blueprint to a site.

		-	Arguments

			name        The blueprint's internal name
			key         The parameter name
			value       The value of that parameter

	-	list

		Show which blueprints are connected to a site.

	-	delete

		Disconnect a blueprint. The URLs it serves are no longer available.

	-	param

		Some blueprints can be configured. Details are probably available
		in that blueprint's documentation.

		-	Arguments

			name        The blueprint's internal name
			key         The parameter name
			value       The value

		Omitting the value will print that parameter; if you also omit the
		key, a list of that blueprint's key+value pairs will be printed.

-	core

	Examine and change Pybble's internal data

-	shell

	Runs a Python shell in the Flask application context.

	-	Arguments

		--no-ipython   Do not use the Iython shell
		--no-bpython   Do not use BPython shell.

	The IPython or BPython interpreter loops are only used if they are
	available.

-	run

	Runs the Flask development server, i.e. app.run()

	- Arguments

		-h HOST, --host HOST   IP adress to bind to
		-p PORT, --port PORT   port to bind to, default: 5000
		--threaded             Use a threaded server model instead of subprocesses
		--processes PROCESSES  Use this many worker processes.
		--passthrough-errors   Dump errors to stderr, not just to the web
		-d, --debug            Use the web debugger
		-D, --no-debug         Do not use the debugger
		-r, --reload           Use the auto-reloader
		-R, --no-reload        Do not use the auto-reloader
		
		Defaults for `-r`/`-d` are from the configuration file.

-	populate

	TODO
	
	Set up some basic content types and an admin frontend for the main website.

-	app

	Runs app-specific commands. The site's 

-	sites

	Show a tree of this Pybble instances's configured (sub)sites.

	If you specify a site with `-s`, only that site and its sub-sites are shown.

-	urls

	Displays all of the url matching routes for this site.

	-	Flags

		--order=rule  Order the output by URL rule or endpoint name

-	new

	Add a new site.

	-	Arguments

		name        The new site's name
		app         The Pybble app module to install
		domain      The domain to listen to

	Calling `new` without arguments will list the installed apps.


