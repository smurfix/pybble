The Manager frontend
====================

The management code allows you to do a basic site content setup.

python manage.py
----------------

-	Environment

	-	PYBBLE

		The Python module with basic, non-overrideable configuration
		(database parameters, your installation's hash key)

-	Arguments

	-c CONFIG, --config CONFIG  Config file to use
	-d                          start in the debugger
	-D                          don't try to catch errors
	-s SITE, --site SITE        which Site to run on (default: root)
	-S SITE, --no-site          no site at all
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

	Examine and change Pybble's internal and mainly-non-site-specific data.

	-	config

		Dumps the site's configuration data.

		XXX: Warning: this may leak the app secret, or other site configuration items.

	-	check
		
		Dumps some status information.

	-	url [arg]

		shows which URLs a site accepts.

		Without an argument, lists all URLs and endpoints.

		If you provide an endpoint and parameters, the resulting URL is
		displayed and vice versa.

	-	shell

		Runs a Python shell in the Flask application context.

		-	Arguments

			--no-ipython   Do not use the Iython shell
			--no-bpython   Do not use BPython shell.

		The IPython or BPython interpreter loops are only used if they are
		available.

	-	migrate [args]

		controls database migrations.
		
		See the Alembic documentation for details.

	-	add [module]

		Add a module to ``Pybble``. See the :ref:`modules` documentation
		for details.

	-	mime

		Manage the list of MIME types known to Pybble.

		-	add name type/subtype extension
	
			Add a MIME type to Pybble's database. Use '-' if the type does
			not have a well-known filename extension.
		
		-	delete
		
			Marks a type for deletion.

		-	list

			Shows a list of known types, their default extension, and their name.
		
		-	doc type/subtype text

			Add a short documentation string to a MIME type.
			
			Without text, shows a type's docstring. Without a type, shows
			all which have one.

	-	objtyp

		Manage the list of objects known to Pybble.

		-	add name modpath
	
			Manually add an object type. (You'd usually use the module
			system for this.)
		
		-	delete
		
			Marks a type for deletion.

		-	list

			Shows a list of known types.
		
		-	doc type text

			Add a short documentation string to an object type.
			
			Without text, shows a type's docstring. Without a type, shows
			all which have one.

	-	schema

		Shows the database table creation statements.
		
		-	-x

			Execute the DDL commands instead of displaying them.

		-	-d

			Display DDL statements which transform the current database to
			the one described in Pybble's data model.

			This was implemented before Alembic was available and uses a
			custom tool which parses SQL schema commands, and creates
			statements to transform one into the other. It's a bit
			over-zealous these days (TODO: fix that), balancing Alembic
			which doesn't recognize some changes.

	-	populate
	
		Adds everything to the database which needs to be in it (root site,
		root user, initial set of templates and permissions, …) for a basic
		Pybble installation.

		If you add `--force`, any changes will be overwritten.
		
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

-	site

	A site in Pybble is the point where you attach a single domain.
	
	-	add

		Adds a new site.

		-	Arguments

			name        The site's internal name
			app         The Flask app to run the site with
			value       The value of that parameter

	-	dir

		Shows a list of Flask apps known to Pybble.

	-	list

		Show a list of sites.

	-	delete

		Disconnect a site. The domain it serves is no longer available.

	-	param

		Sites can be configured.

		-	Arguments

				name        The blueprint's internal name
				key         The parameter name
				value       The value

		Omitting the value will print that parameter; if you also omit the
		key, a list of that site's key+value pairs will be printed.

-	obj

	A command-line interface to Pybble's object system which allows you to
	list and change any system record.

	-	Arguments

		-	-x key

			Expand the values behind this key.

		-	-j, --json

			Emits JSON instead of key-value pairs.

	-	list [type]

		Lists all records of that type. Without type, lists all types.

	-	get [type] [ID]

		Retrieves a record. Without ID, lists all records of that type.
		Without type, lists all object types.

		The record contains a list of all other records which refer to it,
		which slows down output but is very useful.

		Thus:

			$ ./manage.py -t obj get Site 1
			‹Site:1 ‘_root’ @ localhost›
			_refs {14 entries}
			app ‹App:3 _root›
			config ‹ConfigData:4 for ‹Site:None ‘_root’ @ localhost››
			deleted False
			domain 'localhost'
			inherit_parent True
			name '_root'
			sub_sites [9 items]
			tracked 2014-06-03 10:51:12

			$ ./manage.py -t obj -x * get Site 1
			‹Site:1 ‘_root’ @ localhost›
			_refs Breadcrumb_site [2 items]
			      Group_parent [2 items]
			      Member_group [1 items]
			      Permission_target [416 items]
			      Permission_user [11 items]
			      SiteBlueprint_site [2 items]
			      Site_parent [9 items]
			      StaticFile_parent [29 items]
			      StaticFile_site [29 items]
			      Storage_site [1 items]
			      TemplateMatch_target [47 items]
			      Template_target [71 items]
			      Tracker_site [3 items]
			      User_site [3 items]
			app ‹App:3 _root›
			    _refs {1 entries}
			    config ‹ConfigData:3 App _root›
			    deleted False
			    name '_root'
			    path 'pybble.app._root.App'
			config ‹ConfigData:4 for ‹Site:None ‘_root’ @ localhost››
			       _refs {4 entries}
			       deleted False
			       name 'for \u2039Site:None \u2018_root\u2019 @ localhost\u203a'
			deleted False
			domain 'localhost'
			inherit_parent True
			name '_root'
			tracked 2014-06-03 10:51:12

			$ ./manage.py -t obj -x _refs.Site_parent get Site 1
			‹Site:1 ‘_root’ @ localhost›
			_refs Breadcrumb_site [2 items]
			      Group_parent [2 items]
			      Member_group [1 items]
			      Permission_target [416 items]
			      Permission_user [11 items]
			      SiteBlueprint_site [2 items]
			      Site_parent 1 ‹Site:2 ‘root alias’ @ desk›
			                  2 ‹Site:3 ‘root’ @ test.example.com›
			                  3 ‹Site:7 ‘AppTest’ @ atest›
			                  4 ‹Site:8 ‘BlueTest’ @ btest›
			                  5 ‹Site:9 ‘PageTest’ @ ptest›
			                  6 ‹Site:10 ‘s2root’ @ test.site2.example.com›
			                  7 ‹Site:12 ‘sroot’ @ test.site.example.com›
			                  8 ‹Site:17 ‘UserTest’ @ utest›
			                  9 ‹Site:18 ‘test’ @ test›
			      StaticFile_parent [29 items]
			      StaticFile_site [29 items]
			      Storage_site [1 items]
			      TemplateMatch_target [47 items]
			      Template_target [71 items]
			      Tracker_site [3 items]
			      User_site [3 items]
			app ‹App:3 _root›
			config ‹ConfigData:4 for ‹Site:None ‘_root’ @ localhost››
			deleted False
			domain 'localhost'
			inherit_parent True
			name '_root'
			sub_sites [9 items]
			tracked 2014-06-03 10:51:12
			
			$ ./manage.py -t obj -x _refs.Site_parent.2.parent,sub_sites get Site 1
			‹Site:1 ‘_root’ @ localhost›
			_refs Breadcrumb_site [2 items]
			      Group_parent [2 items]
			      Member_group [1 items]
			      Permission_target [416 items]
			      Permission_user [11 items]
			      SiteBlueprint_site [2 items]
			      Site_parent 1 ‹Site:2 ‘root alias’ @ desk›
			                    _refs {2 entries}
			                    app ‹App:1 _alias›
			                    config ‹ConfigData:11 for ‹Site:None ‘root alias’ @ desk››
			                    deleted False
			                    domain 'desk'
			                    inherit_parent True
			                    name 'root alias'
			                    parent ‹Site:1 ‘_root’ @ localhost›
			                    sub_sites [0 items]
			                    tracked 2014-06-03 10:51:18
			                  2 ‹Site:3 ‘root’ @ test.example.com›
			                  3 ‹Site:7 ‘AppTest’ @ atest›
			                  4 ‹Site:8 ‘BlueTest’ @ btest›
			                  5 ‹Site:9 ‘PageTest’ @ ptest›
			                  6 ‹Site:10 ‘s2root’ @ test.site2.example.com›
			                  7 ‹Site:12 ‘sroot’ @ test.site.example.com›
			                  8 ‹Site:17 ‘UserTest’ @ utest›
			                  9 ‹Site:18 ‘test’ @ test›
			      StaticFile_parent [29 items]
			      StaticFile_site [29 items]
			      Storage_site [1 items]
			      TemplateMatch_target [47 items]
			      Template_target [71 items]
			      Tracker_site [3 items]
			      User_site [3 items]
			app ‹App:3 _root›
			config ‹ConfigData:4 for ‹Site:None ‘_root’ @ localhost››
			deleted False
			domain 'localhost'
			inherit_parent True
			name '_root'
			sub_sites 1 ‹Site:2 ‘root alias’ @ desk›
			          2 ‹Site:3 ‘root’ @ test.example.com›
			          3 ‹Site:7 ‘AppTest’ @ atest›
			          4 ‹Site:8 ‘BlueTest’ @ btest›
			          5 ‹Site:9 ‘PageTest’ @ ptest›
			          6 ‹Site:10 ‘s2root’ @ test.site2.example.com›
			          7 ‹Site:12 ‘sroot’ @ test.site.example.com›
			          8 ‹Site:17 ‘UserTest’ @ utest›
			          9 ‹Site:18 ‘test’ @ test›
			tracked 2014-06-03 10:51:12
			
		You can add more than one `-x` argument. As this example shows, lists
		of objects can be selectively expanded with their object ID, not
		their position in the list. This output will not expand any object
		more than once, as the last example shows.

		JSON output is designed as a direct interface to Pybble's REST system;
		it does not include the `_refs` key and does not work with `-x`. It
		does, however, include one-to-many relationships like the `sub_sites`
		key in this example. (One-to-many relationships are not used much
		in the Pybble core. They do not yet work with unspecific references.)

		JSON knows how to encode references to Pybble objects, as well as some
		other data types. You can add your own.

	-	update

		Change a record.

			$ ./manage.py -t obj list User
			‹User:1 root›
			‹User:2 anon @ ‽›
			$ ./manage.py -t obj update User 1 password=fubar
			‹Change:5 changed ‹User:1 root››
			$ ./manage.py -t obj -x \*.Tracker_obj.* get Change 5
			‹Change:5 changed ‹User:1 root››
			_refs Tracker_obj 1 ‹Tracker:8 ‹User:1 root› changed ‹Change:5 changed ‹User:1 root›››
			                    _refs {0 entries}
			                    deleted False
			                    obj ‹Change:5 changed ‹User:1 root››
			                    site ‹Site:1 ‘_root’ @ localhost›
			                    timestamp 2014-06-04 05:03:38
			                    user ‹User:1 root›
			data '{"password":["‹old›","‹new›"]}'
			deleted False
			obj ‹User:1 root›
			    _refs {6 entries}
			    cur_login 2014-06-03 13:35:56
			    deleted False
			    email 'smurf@smurf.noris.de'
			    feed_age 10
			    last_login 2014-06-03 11:35:44
			    password 'pbkdf2:sha1:1000$ZGtDHpVh$ac93b47adf572ffc6c62d7b8aa939269a73a6dde'
			    site ‹Site:1 ‘_root’ @ localhost›
			    this_login 2014-06-03 11:35:44
			    username 'root'
			smurf@desk:~/pybble$ 
			
			As you can see, passwords are special insofar as neither the old nor the new information is logged.
			This applies to any field named 'password'.

			If you want to set a field that refers to an object, there are a couple of syntax options:

				* foo=- ⇒ None
				* foo=123 ⇒ converted to integer
				* foo=True ⇒ converted to Boolean (also: False, None)
				* foo==D:User ⇒ refer to the User table itself
				* foo==R:Read ⇒ refer to the "Read" access right
				* foo==T:Detail ⇒ refer to the "Detail" template type
				* foo==M:text/html ⇒ refer to this MIME type
				* foo==Bar:123 ⇒ reference to this database entry

			You need D: and R: for Permission objects. "D:User" is exactly the
			same as "ObjType" (with the number of the actual User table's
			entry, of course). The same holds for "M:" and the MIMEtype
			table.

