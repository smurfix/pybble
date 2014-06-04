Modularity
==========

Pybble is modular. You can add a module with the `manage core add
some.module` command, where `some.module` is a regular Python module with a
couple of special top-level variables.

All lists of objects are only read once, thus you can use generators.

MIME
----

A list of MIME types which should be known to Pybble.
Example:

    MIME = (
        ('image','jpeg','jpg',"JPEG image","A photograph or similar tonal image"),
        ('image','png ,'png',"PNG image","Graphs or similar images"),
        …
    )

The components are

    * MIME type
    * MIME subtype
    * filename extension (may be `None`)
    * name
    * description

MODEL
-----

A list of database tables: subtypes of `pybble.core.models.object.Object`.

    MODEL = (
        ('pybble.ext.wiki.Page','WikiPage','An inline-editable page'),
        pybble.ext.wiki.Page, # a class named 'Page', docstring from there
    )

The components are

    * (name of) table class
    * human-readable name
    * documentation

The documentation is optional. You need to list all tables you use, even if
indirectly, otherwise some core Pybble features (like the object tree
introspection) will not work.

Database tables will be created during the import.

For further documentation about Pybble models and attributes used during
iport, see the :ref:`model` document.

APP
---

A list of apps to install.

The format is the same as `MODEL`.

BLUEPRINT
---------

A list of apps to install.

The format is the same as `MODEL`.

VAR
---

A list of configuration variables. Note that their namespace is global, so
you should call your variables `YOURMODULE_NAME` to disambiguate.

    VAR = (
        ('("YOURMODEL_CSS","black.css","default CSS for yourmodel"),
    )

The components are

    * Variable name
    * default value
    * short documentation

The value can be any JSON-serializeable Python expression.

Variables declared in this way, i.e. a global VAR, will be added to the
site root, which is probably not what you want because Pybble's (future …
TODO) configuration front-end will not find them.

Instead, you should add the VAR list to the app or blueprint which is
actually using the variable:

    class MyBlueprint(BaseBlueprint):
        …
        VAR = ( … )

From your code, you can refer to the variable's value via
`current_site.config.VARNAME`.

TEMPLATE
--------

A list of named templates to add. Like variables, you should attach these
to the app or blueprint instead of loading them globally.

    TEMPLATE = (
        ("/path/to/the/file", "some/templatepath.html", ""),
    )

The third parameter contains lines which should be prepended to the file
contents. This is a 

TRANSLATOR
----------

A list of translators (i.e. template engines) to install. A SASS/SCSS
compiler would accept both .sass and .scss by way of different translators.

The format is the same as `MODEL`.

See ref:`templates` for a description of the code required to implement a
translator.

VERIFIER
--------

A list of verifiers to install.

The format is the same as `MODEL`.

FILE
----

A list of static files, or directories to recursively copy static files from.

    FILE = (
        ("static", "my_module"),
    )

The first parameter is the file/directory name, relative to your module;
the second is the path prefix, if any.

