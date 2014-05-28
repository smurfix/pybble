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
        pybble.ext.wiki.Page, # direct object, and no name+doc
    )

The components are

    * (name of) table class
    * human-readable name
    * documentation

The documentation is optional. List all tables you use, even if indirectly,
otherwise some core Pybble features (like the object tree introspection)
will not work.

The database tables will be created during the import.

Models may have a couple of attributes which control an initial set of
permissions when a new site is created. The default is:

    _site_perm=None
    _anon_perm=None
    _admin_perm=PERM_ADMIN

    _site_add_perm=()
    _anon_add_perm=()
    _admin_add_perm=()

These are, respectively, for registered users, anonymous users, and
administrators. The first set controls the rights to existing records, the
second lists which objects this model may be added to.

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

You should add the VAR list to the app or blueprint which is actually using
the variable:

    class MyBlueprint(BaseBlueprint):
        …
        VAR = ( … )

Variables declared in a global VAR will be added to the site root, which is
probably not what you want because Pybble's (future … TODO) configuration
front-end will not find them.

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

A list of translators to install.

The format is the same as `MODEL`.

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

