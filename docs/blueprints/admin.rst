Administrative view
===================

You can create an admin page (courtesy of the ``flask.ext.admin``
extension) of any Pybble document collection.

	manage.py -s yoursite blueprint add SomeDataView _admin /yourdata
	manage.py -s yoursite blueprint param SomeDataView model pybble.app.yourapp.models.somedata

This causes http://example.com/yourdata to present a list of `somedata` objects, .
