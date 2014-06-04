Templates
#########

Pybble uses Jinja2 templates, but you can plug in many other templating
systems.

It installs a somewhat-large number of extensions to help with its object
system.

Variables
=========

obj
~~~

Within Pybble's standard templates, the object which the template is supposed
to display.

USER
~~~~

The user who is currently logged in (itself an object)

MESSAGES
~~~~~~~~

A list of flashed messages. Their .success attribute tells you whether to
display them in green (everything worked: True), red (something is wrong:
False) or yellow (the user needs to do something: None).

SITE
~~~~

The domain the template is used on (itself an object)

CRUMBS
~~~~~~

A list of the last 20 pages the user visited here.

NOW
~~~

The current time.

Constants
=========

tm_*
~~~~

These constants (short for "Template Mode") denote which kind of template
to interpolate for a given object. The following are available:

* page

	This denotes the whole-page template, i.e. a specific object should be
	rendered. Typically, this template consists of a lot of boilerplate and
	then embeds the object's `subpage` view.
	
* subpage

	This is the standard "display" view. Its HTML output is usually
	embedded in a <div>.

	Default: missing_2.html

* string

	This view typically shows an object's node ID and a short string like
	its name.

	Default: missing_3.html

* detail

	This is a "close-up" list of an object's attributes, suitable for
	debugging. It usually consists of an <h2> tag with the object's name
	and a key-value <table>. Any references to other objects should go to
	their detail view.
	
	Default: missing_4.html
	
* snippet

	This is a detail of an object, used for display within the object
	hierarchy tree.

	Default: missing_5.html

* hierarchy

	This view is used for hierarchical display, like a discussion tree
	where messages are indented below the one they're in reply of.

	Default: missing_6.html

* rss

	This view outputs a short HTML segment which will be embedded
	(via CDATA) in Pybble's RSS stream.

	Default: missing_7.html

* email

	This is a text-only template for sending an object change notification
	via email.

	Default: missing_8.html

* preview

	This template emits a preview of a changed object. Details for that are
	up to the blueprint which implements the editor. The difference between
	this and a subpage is that a preview will get some data, but not an
	actual stored object (it is not), a preview should be designed in a more
	unobtrusive way, and any links within the preview should open in a new
	window.

	Default: missing_9.html

These "missing_#" templates are not referred to by name, but by way of the
normal unnamed-template lookup rules.

Additionally, there is a named "missing_0.html" template which is attached
to the root site. It is displayed when the requested domain is not known to
Pybble.

Filters
=======

render
~~~~~~

Insert an object's HTML view. You can add a parameter telling Pybble which
variant to use; the most common are `tm_subpage` (inclusion on the main
page) and `tm_string` (a short human-readable text).

Translator structure
====================

The code which actually transforms a template text to output is called a
`translator` in Pybble.

	*	`init_app(app)` does whatever it needs to do to the Flask app.
		If you set up an initial environment, don't store it in the app,
		just return it.
	
	*	`template` is a property with a `render()` method which accepts
		arbitrary keyword arguments for your template's variables, and
		which returns the actual result of applying the template.

		Your environment is available as `self.env`, and the Pybble
		template object is `self.db_template`.

See `pybble/translator/jinja/__init__.py` for a complete example, including
caching.

