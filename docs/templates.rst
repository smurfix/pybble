Templates
#########

Pybble uses Jinja2 templates.

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

{1:"Page", 2:"Subpage", 3:"String", 4:"Detail", 5:"Snippet",
        6:"Hierarchy", 7:"RSS", 8:"email", 9:"preview"

Additionally, there is a "missing_0.html" template which is attached to the
Pybble root. It is displayed when the requested domain is unknown.

Filters
=======

render
~~~~~~

Insert an object's vew

