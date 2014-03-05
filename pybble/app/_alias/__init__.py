##BP

from pybble.app import WrapperApp

class App(WrapperApp):
	"""
	This app simply does the same thing as its parent.
	"""
	def __call__(self, environ, start_response):
		return self.pybble_dispatcher.get_application(site=self.site.parent)(environ, start_response)

