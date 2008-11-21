# -*- coding: utf-8 -*-
"""
    inyoka.utils.decorators
    ~~~~~~~~~~~~~~~~~~~~~~~

    Decorators and decorator helpers.

    :copyright: Copyright 2008 by Armin Ronacher.
    :license: GNU GPL.
"""

from pybble.database import NoResult
from werkzeug.exceptions import NotFound

def patch_wrapper(decorator, base):
    decorator.__name__ = base.__name__
    decorator.__module__ = base.__module__
    decorator.__doc__ = base.__doc__
    decorator.__dict__ = base.__dict__
    return decorator

def add_to(cls):
	def adder(func):
		setattr(cls,func.__name__, func)
		return None
	return adder

def ResultNotFound(proc):
	def wrapper(*a,**k):
		try:
			r = proc(*a,**k)
		except NoResult:
			raise NotFound()
	return patch_wrapper(wrapper,proc)

#class deferred(object):
#    """
#    Deferred properties.  Calculated once and then it replaces the
#    property object.
#    """
#
#    def __init__(self, func, name=None):
#        self.func = func
#        self.__name__ = name or func.__name__
#        self.__module__ = func.__module__
#        self.__doc__ = func.__doc__
#
#    def __get__(self, obj, type=None):
#        if obj is None:
#            return self
#        value = self.func(obj)
#        setattr(obj, self.__name__, value)
#        return value
#
#    @staticmethod
#    def clear(obj):
#        """Clear all deferred objects on that class."""
#        for key, value in obj.__class__.__dict__.iteritems():
#            if getattr(value, '__class__', None) is deferred:
#                try:
#                    delattr(obj, key)
#                except AttributeError:
#                    continue
