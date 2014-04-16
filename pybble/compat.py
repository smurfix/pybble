##BP

from flask._compat import PY2,reraise,StringIO, iteritems,iterkeys,itervalues, text_type, string_types,integer_types

if not PY2:
	def py2_unicode(cls):
		return cls

else:
	def py2_unicode(cls):
		cls.__unicode__ = cls.__str__
		replace_repr = cls.__repr__ is cls.__str__
		cls.__str__ = lambda x: x.__unicode__().encode('utf-8')

		if replace_repr:
			cls.__repr__ = cls.__str__
			
		return cls

