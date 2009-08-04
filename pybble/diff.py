#!/usr/bin/python2.2
# -*- coding: utf-8 -*-

"""HTML Diff: http://www.aaronsw.com/2002/diff
Rough code, badly documented. Send me comments and patches."""

__author__ = 'Aaron Swartz <me@aaronsw.com>'
__copyright__ = '(C) 2003 Aaron Swartz. GNU GPL 2.'
__version__ = '0.22'

import difflib, string
from jinja2 import Markup
esc = Markup.escape
m = Markup

def isTag(x): return x[0] == "<" and x[-1] == ">"

def textDiff(a, b):
	"""Takes in strings a and b and returns a human-readable HTML diff."""

	out = []
	a, b = html2list(a), html2list(b)
	s = difflib.SequenceMatcher(None, a, b)
	for e in s.get_opcodes():
		if e[0] == "replace":
			# @@ need to do something more complicated here
			# call textDiff but not for html, but for some html... ugh
			# gonna cop-out for now
			out.append(m('<del class="diff modified">')+esc(''.join(a[e[1]:e[2]])) + m('</del><ins class="diff modified">')+esc(''.join(b[e[3]:e[4]]))+m("</ins>"))
		elif e[0] == "delete":
			out.append(m('<del class="diff">')+esc(''.join(a[e[1]:e[2]])) + m("</del>"))
		elif e[0] == "insert":
			out.append(m('<ins class="diff">')+esc(''.join(b[e[3]:e[4]])) + m("</ins>"))
		elif e[0] == "equal":
			s = "".join(b[e[3]:e[4]])
			ss = s.split("\n")
			if len(ss) > 6:
				s = "\n".join(ss[:3]+[u"[…]"]+ss[-3:])
			out.append(esc(s))
		else: 
			raise AssertionError("Um, something's broken. I didn't expect a '" + `e[0]` + "'.")
	return ''.join(out)

def textOnlyDiff(a, b):
	"""Takes in strings a and b and returns a human-readable ASCII diff."""

	out = []
	a, b = html2list(a), html2list(b)
	s = difflib.SequenceMatcher(None, a, b)
	for e in s.get_opcodes():
		if e[0] == "replace":
			# @@ need to do something more complicated here
			# call textDiff but not for html, but for some html... ugh
			# gonna cop-out for now
			delt = ''.join(a[e[1]:e[2]])
			inst = ''.join(b[e[3]:e[4]])
			rest = ""
			while delt and inst and delt[-1]==inst[-1]:
				rest = inst[-1]+rest
				delt = delt[:-1]
				inst = inst[:-1]
			out.append("{-%s-}{+%s+}%s" % (delt,inst,rest))
		elif e[0] == "delete":
			delt = ''.join(a[e[1]:e[2]])
			out.append("{-%s-}" % (delt,))
		elif e[0] == "insert":
			inst = ''.join(b[e[3]:e[4]])
			out.append("{+%s+}" % (inst,))
		elif e[0] == "equal":
			s = "".join(b[e[3]:e[4]])
			ss = s.split("\n")
			if len(ss) > 6:
				s = "\n".join(ss[:3]+[u"[…]"]+ss[-3:])
			out.append(esc(s))
		else: 
			raise AssertionError("Um, something's broken. I didn't expect a '" + `e[0]` + "'.")
	return ''.join(out)

def html2list(x, b=0):
	mode = 'char'
	cur = ''
	out = []
	for c in x:
		if c.isspace():
			out.append(cur+c);
			cur = ''
		elif mode == 'special':
			if c.isalnum():
				out.append(cur)
				cur = c
				mode = 'special'
			else: cur += c
		elif mode == 'char':
			if not c.isalnum():
				out.append(cur)
				cur = c
				mode = 'special'
			else: cur += c
	out.append(cur)
	return filter(lambda x: x is not '', out)

if __name__ == '__main__':
	import sys
	try:
		a, b = sys.argv[1:3]
	except ValueError:
		print "htmldiff: highlight the differences between two html files"
		print "usage: " + sys.argv[0] + " a b"
		sys.exit(1)
	print textDiff(open(a).read(), open(b).read())
	
