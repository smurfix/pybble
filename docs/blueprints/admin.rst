Administrative view
===================

You can create an admin page (courtesy of the ``flask.ext.admin``
extension) of any Pybble document collection.

	manage.py -s yoursite blueprint add yourdata _admin /yourdata
	manage.py -s yoursite blueprint param yourdata model pybble.app.yourapp.models.yourdata

