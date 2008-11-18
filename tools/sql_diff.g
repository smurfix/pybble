#!/usr/bin/python
# -*- coding: utf-8 -*-

"""\
This module reads table descriptions from two files, then generates minimal
SQL commands to transform A to B.

"""

import sys, os, copy, time, array
from traceback import format_exception_only

class DupTableError(ReferenceError):
	pass
class DupFieldError(ReferenceError):
	pass
class DupKeyError(ReferenceError):
	pass
class NoSuchTableError(IndexError):
	pass

verbose=1
_debug=None
keyseq = 0

r="\r"+(" "*70)+"\r"
INTs = ("int","smallint","bigint","tinyint","mediumint")

cnt=0
cntt = ""
ltm=int(time.time())-1

def trace(*x):
	if not verbose: return
	print >>sys.stderr, r+"  "+" ".join(map(str,x))+"   \r",
	sys.stderr.flush()

def tdump(n):
	if n.__class__ == ().__class__:
		r=""
		for f in n: r += "'%s', " % (f,)
		return "ENUM ("+r[:-2]+")"
	else:
		return n

class curtime: pass
class NotGiven: pass

def valprint(x):
	if x is None: return "NULL"
	if x is curtime: return "CURRENT_TIMESTAMP"
	return "'"+str(x)+"'" ## TODO: quote correctly

class Field(object):
	"""Declare a table's column"""
	def __init__(self,table,name,after=True):
		self.name=name
		self.old_name=name
		self.table=table
		self.tname=None
		self.next_col=None
		self.prev_col=None

		self.nullable=True
		self.len=None
		self.len2=None
		self.defval=NotGiven
		self.updval=NotGiven
		self.autoinc=False
		self.unsigned=False
		self.charset=None
		self.collation=None

		self._chained=False
		self._tagged=False
		table._new_field(self,after=after)

	def clone(self,table):
		f = Field(table,self.name)
		f.tname=self.tname
		f.nullable=self.nullable
		f.len=self.len
		f.len2=self.len2
		f.defval=self.defval
		f.updval=self.updval
		f.autoinc=self.autoinc
		f.unsigned=self.unsigned
		f.charset=self.charset
		f.collation=self.collation
		table._new_field(f)

	def create_done(self):
		"""Fill in some defaults"""
		if self.defval is NotGiven:
			if self.autoinc or self.nullable:
				self.defval = None
			elif self.tname in INTs:
				self.defval = "0"
			elif self.tname == "datetime":
				self.defval = "0000-00-00 00:00:00"
			else:
				self.defval = ""
		if self.len is None:
			if self.tname == "tinyint":
				self.len = 4
			elif self.tname == "smallint":
				self.len = 6
			elif self.tname == "mediumint":
				self.len = 9
			elif self.tname == "int":
				self.len = 11
			elif self.tname == "bigint":
				self.len = 20
			elif self.tname in INTs:
				raise RuntimeError("INT problem",self.tname)

			if self.unsigned and self.len and self.len != 20:
				self.len -= 1
		if self.tname == "timestamp" and self.defval is curtime \
				and not self.nullable:
			self.nullable = True
		if self.tname in INTs \
				and self.autoinc and self.nullable:
			self.nullable = False

	def drop(self):
		self.table._del_field(self)
	
	def dump(s,*f,**k):
		"""Dump myself, either completely or as a diff to column 'oc'"""
		a,b=s.dump2(*f,**k)
		return a

	def is_text_column(self):
		return (self.tname == "char" or self.tname == "varchar" or self.tname.endswith("text"))

	def dump2(self,oc=None,in_create=False,skip_flags=""):
		"""Dump myself, also return changes"""
		if not self.charset: self.charset=self.table.charset
		if not self.collation: self.collation=self.table.collation
		if oc:
			if not oc.charset: oc.charset=oc.table.charset
			if not oc.collation: oc.collation=oc.table.collation
		if not in_create:
			if not oc:
				r="ADD COLUMN "
			elif not self._diffs(oc,skip_flags=skip_flags):
				return None,None
			elif self.name != oc.name:
				r="CHANGE COLUMN `%s` " % (oc.name,)
			else: # MySQL Special ??
				r="MODIFY COLUMN "
		else:
			r=""
		rp=[]
		r += "`%s` %s" % (self.name,tdump(self.tname))
		if self.len is not None:
			if self.len2 is not None:
				r += "(%d,%d)" % (self.len,self.len2)
			else:
				r += "(%d)" % (self.len,)
		if oc: 
			if self.tname != oc.tname: rp.append(oc.tname)
			if self.len != oc.len or self.len2 != oc.len2:
				if oc.len is not None: rp.append("len=%d"%(oc.len,))
				else: rp.append("!len")

		if self.unsigned:
			r += " UNSIGNED"
		if oc:
			if self.unsigned != oc.unsigned:
				if oc.unsigned: rp.append("unsigned")
				else: rp.append("signed")

		do_cs=False
		if self.is_text_column():
			if 'c' not in skip_flags and self.charset:
				if oc and oc.charset == "utf8":
					charset = oc.charset
				else:
					charset = self.charset
				if charset != self.table.charset or charset != self.charset or (oc and (charset != oc.charset or charset != oc.table.charset)):
					r += " CHARACTER SET %s" % (charset,)
					do_cs=True
			if 'c' not in skip_flags and oc:
				if self.charset != oc.charset:
					rp.append("charset %s/%s"%(oc.charset,self.charset))
	
			if 'c' not in skip_flags and self.collation and not do_cs:
				if oc and oc.charset == "utf8" and oc.charset != self.charset:
					collation = oc.collation
				else:
					collation = self.collation
				r += " COLLATE %s" % (collation,)
			if 'c' not in skip_flags and oc and not do_cs:
				if oc.collation and (self.collation != oc.collation):
					rp.append("collate %s/%s"%(oc.collation,self.collation))
	
		if self.nullable:
			if not in_create:
				r += " NULL" # ist eh Default
		else:
			r += " NOT NULL"
		if oc:
			if self.nullable != oc.nullable:
				if oc.nullable: rp.append("null")
				else: rp.append("!null")

		if self.autoinc:
			r += " AUTO_INCREMENT"
		if oc:
			if self.autoinc != oc.autoinc:
				if oc.autoinc: rp.append("autoinc")
				else: rp.append("!autoinc")

		if self.defval is not NotGiven:
			r += " DEFAULT " + valprint(self.defval)
		if oc:
			if self.defval != oc.defval:
				if oc.defval != NotGiven: rp.append("default "+valprint(oc.defval))
				else: rp.append("!default")

		if self.updval is not NotGiven:
			r += " ON UPDATE " + valprint(self.updval)
		if oc:
			if self.updval != oc.updval:
				if oc.updval != NotGiven: rp.append("updefault "+valprint(oc.updval))
				else: rp.append("!updefault")

		if 'a' not in skip_flags and oc and self.prev_col != oc.prev_col and not in_create:
			if self.prev_col:
				r += " AFTER %s" % (self.prev_col.name,)
			else:
				r += " FIRST"
		if 'a' not in skip_flags and oc:
			if self.prev_col != oc.prev_col:
				if oc.prev_col: rp.append("after "+oc.prev_col.name)
				else: rp.append("first")

		return r,rp

	def _diffs(s,o,skip_flags=""):
		"""return TRUE if s and o differ"""
		if 'a' not in skip_flags:
			if s.prev_col: pa=s.prev_col.name
			else: pa=None
			if o.prev_col: pb=o.prev_col.name
			else: pb=None
			if pa != pb: return True
		if s.name != o.name: return True
		if s.tname != o.tname: return True
		if s.len != o.len or s.len2 != o.len2:
			if s.tname != "timestamp" or (s.len is not None and o.len is not None):
				return True
		if s.autoinc != o.autoinc: return True
		if s.unsigned != o.unsigned: return True
		if s.nullable != o.nullable: return True
		if s.is_text_column():
			if 'c' not in skip_flags and s.charset != o.charset and (s.charset == "utf8" or o.charset != "utf8"):
				return True
			if 'c' not in skip_flags and s.collation != o.collation:
				if o.collation is not None and s.collation is not None and s.collation != o.collation and (s.charset == "utf8" or o.charset != "utf8"):
					return True
		if s.defval != o.defval:
			if s.tname != "timestamp" or (s.defval is not NotGiven and s.defval is not curtime) or (o.defval is not NotGiven and o.defval is not curtime):
				return True
		if s.updval != o.updval:
			if s.tname != "timestamp" or (s.updval is not NotGiven and s.updval is not curtime) or (o.updval is not NotGiven and o.updval is not curtime):
				return True
		# ignore: next_col
		return False

	def __hash__(self): return self.old_name.__hash__() # is immutable
	def __str__(self): return "<%s:%s %s>" % (self.name,self.tname, self.table)
	def __repr__(self): return "<%s.%s>" % (self.table.name,self.name)

	def set_after(self,after=True,oc=None):
		self.table._del_field(self)
		self.table._new_field(self,after=after)
	def __eq__(self,other):
		if other is None: return False
		return self.name.__eq__(other.name)
	def __ne__(self,other):
		if other is None: return True
		return self.name.__ne__(other.name)
	#def __cmp__(self,other): return self.name.__cmp__(other.name)
		
class Key(object):
	def __init__(self,table,name,ktype,fields):
		self.table=table
		self.name=name
		self.ktype=ktype
		self.fields=fields
		self.id = (ktype,fields)

	def pref(self,pref_seq=False):
		"""Pref value for this key"""
		pr=1000

		if len(self.fields)==1 and self.ktype=="U":
			k = self.fields[0][0]
			if k.autoinc and pref_seq:
				pr *= 10
			if not k.autoinc and not pref_seq:
				pr *= 10
		if self.name is None: # primary key
			pr += 20

		for f in self.fields:
			f = f[0]
			if f.name in ("id","lfd"):
				pr += 50
			if f.tname == "int":
				if pref_seq: # also prefer integer keys
					pr += 100/len(self.fields)
			else:
				if not pref_seq:
					pr += 100/len(self.fields)

		if self.ktype!="U":
			pr /= 10
		return pr/len(self.fields)

	def dump(self,ok=None,in_create=False,skip_flags=""):
		"""Dump myself, either completely or as a diff to key 'ok'"""
		if not in_create:
			if not ok:
				r="ADD"
			elif not self._diffs(ok,skip_flags=skip_flags):
				return None
			else:
				r=""
				if ok.name is None:
					r += "DROP PRIMARY KEY,\n    "
				else:
					r += "DROP KEY `%s`,\n    " % (ok.name,)
				r+="ADD"

		else:
			r=""

		if self.name is None:
			r += " PRIMARY KEY"
		else:
			if self.ktype == "U": r+=" UNIQUE"
			r += " KEY `%s`" % (self.name,)
		r += "("
		ra=""
		for f in self.fields:
			r += ra+"`"+f[0].name+"`"
			if f[1]:
				r += "("+str(f[1])+")"
			ra=","
		r += ")"
		return r

	def _diffs(self,ok,skip_flags=""):
		if self.fields != ok.fields: return True
		if 'i' not in skip_flags and self.name != ok.name: return True
		if self.ktype != ok.ktype: return True
		return False

	def __str__(self):
		n=self.name
		if not n: n="PRIMARY"
		return "<%s %s %s>" % (self.ktype,n,",".join(map(str,self.fields)))
	def __repr__(self):
		n=self.name
		if not n: n="PRIMARY"
		return "<%s %s.%s %s>" % (self.ktype,self.table.name,n,self.fields)


class FKey(object):
	def __init__(self,name,table,fields,rtable,rfields, opt):
		self.name=name
		self.table=table
		self.rtable=rtable
		self.fields=fields
		self.rfields=rfields
		self.opt=opt

	def dump(self,ok=None,in_create=False,skip_flags=""):
		"""Dump myself, either completely or as a diff to key 'ok'"""
		if not in_create:
			if not ok:
				r="ADD"
			elif not self._diffs(ok,skip_flags=skip_flags):
				return None
			else:
				r=""
				r += "DROP CONSTRAINT `%s`,\n    " % (ok.name,)
				r += "ADD"

		else:
			r=""

		r += " CONSTRAINT `%s` FOREIGN KEY (" % (self.name,)
		ra=""
		for f in self.fields:
			r += ra+"`"+f.name+"`"
			ra=","
		r += ") REFERENCES `%s` (" % (self.rtable,)
		ra=""
		for f in self.rfields:
			r += ra+"`"+f+"`"
			ra=","
		r += ")"
		for a,b in self.opt.items():
			r += " ON %s %s" % (a.upper(),b)
		return r

	def _diffs(self,ok,skip_flags=""):
		if 'i' not in skip_flags and self.name != ok.name:
			print "#FK Name:",self.name,ok.name
			return True
		if self.rtable != ok.rtable:
			print "#FK",self.name,"rtable:",self.rtable,ok.rtable
			return True
		fs=[f.name for f in self.fields]
		ofs=[f.name for f in ok.fields]
		if fs != ofs:
			print "#FK",self.name,"fields:",fs,ofs
			return True
		if self.rfields != ok.rfields:
			print "#FK",self.name,"rfields:",self.rfields,ok.rfields
			return True
		for a,b in self.opt.items():
			try: c=ok.opt[a]
			except KeyError:
				print "#FK",self.name,"k_opt",a,"??"
				return True
			else:
				if b != c:
					print "#FK",self.name,"k_opt",a,b,c
					return True
		for a,b in ok.opt.items():
			try: c=self.opt[a]
			except KeyError:
				print "#FK",self.name,"ok_opt",a,"??"
				return True
			else:
				if b != c:
					print "#FK",self.name,"ok_opt",a,b,c
					return True
		return False

	def __str__(self): return "<%s %s>" % \
				(",".join([f.name for f in self.fields]),
				 ",".join(self.rfields))
	def __repr__(self): return "<%s.%s %s.%s>" % \
				(self.table, ",".join([f.name for f in self.fields]),
				 self.rtable, ",".join(self.rfields))


class Table(object):
	"""Declare a table"""
	def __init__(self,name,db=None):
		self.name=name
		self.engine=None
		self.charset="utf8"
		self.collation="utf8_general_ci"
		self.packing=None
		self.maxrows=None

		self.col={}
		self.key={}
		self.knames={}
		self.dupkeys=[]

		self.fkey={}
		self.fknames={}
		self.dupfkeys=[]

		if db:
			db.tables[name]=self
			self.tables = db.tables

		self.first_col=None
		self.last_col=None

		self.db = db

	def clone(self,db):
		t = Table(self.name)
		t.engine = self.engine
		t.charset = self.charset
		t.collation = self.collation
		t.packing = self.packing
		t.maxrows = self.maxrows

		f = self.first_col
		while f:
			f.clone(t)
			f = f.next_col
		t.key.update(self.key)
		t.knames.update(self.knames)
		t.dupkeys = self.dupkeys[:]

		t.fkey.update(self.fkey)
		t.fknames.update(self.fknames)
		t.dupfkeys = self.dupfkeys[:]

		t.first_col = self.first_col
		t.last_col = self.last_col
		t.tables = db.tables
		t.db = db
		return t

	def best_keys(self, pref_seq=True):
		"""Returns all indices on the table, sorted by preference."""
		k=self.key.values()
		k.sort(lambda a,b: b.pref(pref_seq)-a.pref(pref_seq))
		return k

	def timestamp(self):
		# Liefere die Spalte mit dem Ãnderungs-Timestamp.
		for c in self.col.itervalues(): # MySQL neu
			if c.updval == curtime:
				return c
		for c in self.col.itervalues(): # Django, kundebunt
			if c.tname == "modified":
				return c
		for c in self.col.itervalues(): # kunde alt
			if c.tname == "timestamp":
				return c
		for c in self.col.itervalues(): # ESS
			if c.name == "tstamp":
				return c
		return None
		
	def new_fkey(self,name,fl1,rtable,fl2,opt):
		if name in self.fknames:
			raise DupKeyError(name)
		fl1=tuple(fl1)
		fl2=tuple(fl2)
		try:
			k=self.fkey[fl1]
		except KeyError:
			k=FKey(name,self,fl1,rtable,fl2,opt)
			self.fkey[fl1]=k
			self.fknames[name]=k
			try: self.dupfkeys = self.dupfkeys.remove(name)
			except ValueError: pass
		else:
			if k.name is None: repl=False
			elif name is None: repl=True
			else: repl=False
			if repl: # alten Key rauswerfen
				self.dupfkeys.append(k.name)
				del self.fknames[k.name]

				k.name=name
				self.fknames[name]=k
			else:
				if k.name < name:
					self.dupfkeys.append(name)
				else:
					self.dupfkeys.append(k.name)
					k.name = name
	
	def del_fkey(self,name):
		try:
			k=self.fknames.pop(name)
		except KeyError:
			self.dupfkeys=self.dupfkeys.remove(name)
		else:
			del self.fkey[k.fields]

	def new_key(self,name,ktype,fields):
		if name == "":
			global keyseq
			keyseq += 1
			name = "x_" + str(keyseq)
		if name in self.knames:
			raise DupKeyError(name)
		fields=tuple(fields)
		k=Key(self,name,ktype,fields)
		try:
			k=self.key[k.id]
		except KeyError:
			self.key[k.id]=k
			self.knames[name]=k
			try: self.dupkeys = self.dupkeys.remove(name)
			except ValueError: pass
		else:
			if k.name is None: repl=False
			elif name is None: repl=True
			elif ktype != k.ktype: repl=True
			else: repl=False
			if repl: # alten Key rauswerfen
				self.dupkeys.append(k.name)
				del self.knames[k.name]

				k.name=name
				self.knames[name]=k
			else:
				if k.name != name: self.dupkeys.append(name)
	
	def del_key(self,name):
		try:
			k=self.knames.pop(name)
		except KeyError:
			self.dupkeys=self.dupkeys.remove(name)
		else:
			del self.key[k.id]

	def drop(self):
		del self.tables[self.name]

	def columns(self):
		c=self.first_col
		while c:
			cn=c.next_col
			yield c
			c=cn

	def new_field(self,name,old_col):
		"""add a new field to this table.
		  (May be a clone of some old field.)"""

		if old_col:
			if old_col is True:
				old_col=name
			old_col=self.col[old_col]
			after = old_col.prev_col
			old_col.drop()
			old_col.name=name
			old_col._chained=False
			self._new_field(old_col,after=after)

			return old_col
		else:
			if self.col.has_key(name):
				raise DupFieldError(self,name)
			return Field(self,name)

	def _new_field(self,col,after=True):
		if col._chained: return
		col._chained=True
		self.col[col.name]=col

		if after is None:
			col.prev_col=None
			col.next_col=self.first_col
		elif after is True:
			col.next_col=None
			col.prev_col=self.last_col
		else:
			col.prev_col=after
			col.next_col=after.next_col

		if col.prev_col: col.prev_col.next_col = col
		else: self.first_col=col
		if col.next_col: col.next_col.prev_col = col
		else: self.last_col=col

	def del_field(self,name):
		self.col[name].drop()
	def _del_field(self,col):
		if self.col[col.name] != col: raise IndexError

		if not col._chained: return
		col._chained=False
		del self.col[col.name]

		if col.prev_col: col.prev_col.next_col=col.next_col
		else: self.first_col=col.next_col
		if col.next_col: col.next_col.prev_col=col.prev_col
		else: self.last_col=col.prev_col

	def dump(self,skip_flags=""):
		r= "CREATE TABLE %s (\n    " % (self.name,)
		ra=""
		for c in self.columns():
			r += ra+c.dump(in_create=True,skip_flags=skip_flags)
			ra=",\n    "
		for k in self.key.values():
			r += ra+k.dump(in_create=True,skip_flags=skip_flags)
			ra=",\n    "
		for k in self.fkey.values():
			r += ra+k.dump(in_create=True,skip_flags=skip_flags)
			ra=",\n    "
		r += ")"
		if self.engine:
			r += " ENGINE="+self.engine
		if 'c' not in skip_flags and self.charset:
			r += " CHARACTER SET="+self.charset
		if 'c' not in skip_flags and self.collation:
			r += " COLLATE="+self.collation
		if 'm' not in skip_flags and self.maxrows:
			r += " MAX_ROWS="+self.maxrows
		if 'p' not in skip_flags and self.packing is not None:
			r += " PACK_KEYS="+str(self.packing)
		return r

	def diff1(s,o,skip_flags=""):
		r=""
		ra="ALTER TABLE %s\n    " % (s.name,)

		for on in o.dupkeys:
			if on == "":
				r += ra+"DROP PRIMARY KEY"
			else:
				r += ra+"DROP KEY `%s`" % (on,)
			ra=",\n    "

		if 'k' not in skip_flags:
			for fk in o.fkey.values():
				if fk.name not in s.fknames or s.fknames[fk.name]._diffs(fk,skip_flags=skip_flags):
					r += ra+"DROP FOREIGN KEY `%s`" % (fk.name,)
					ra=",\n    "
		if s.engine and s.engine != o.engine:
			r += ra+" ENGINE="+s.engine
			ra=""
		if 'c' not in skip_flags and s.charset and s.charset != o.charset:
			r += ra+" CHARACTER SET="+s.charset
			ra=""
		if 'c' not in skip_flags and o.collation and s.collation and s.collation != o.collation:
			r += ra+" COLLATE="+s.collation
			ra=""
		if 'm' not in skip_flags and s.maxrows and s.maxrows != o.maxrows:
			r += ra+" MAX_ROWS="+str(s.maxrows)
			ra=""
		if 'p' not in skip_flags and s.packing is not None and s.packing != o.packing:
			r += ra+" PACK_KEYS="+str(s.packing)
			ra=""
		return r

	def diff2(s,o,skip_flags=""):
		r=""
		ra="ALTER TABLE %s\n    " % (s.name,)
		rb=""

		dels = []
		for k in o.key.values():
			if 'i' in skip_flags and k.name is not None:
				if k.id in s.key: continue
			else:
				if k.name in s.knames: continue
			r += ra+"DROP "
			if k.name is None:
				r +="PRIMARY KEY"
			else:
				r += "KEY `%s`" % (k.name,)
			ra=",\n    "
			rb += "# %s \n" % (k,)
			dels.append(k)
		for k in dels:
			del o.key[k.id]
			del o.knames[k.name]

		for k in o.key.values():
			try:
				if 'i' in skip_flags:
					ok=s.key[k.id]
				else:
					ok=s.knames[k.name]
			except KeyError:
				r += ra+"DROP "
				if k.name is None:
					r +="PRIMARY KEY"
				else:
					r += "KEY `%s`" % (k.name,)
			else:
				continue
		# First pass: add new columns
		for c in s.columns():
			nr=""
			try: oc=o.col[c.old_name]
			except KeyError:
				r += ra+c.dump(skip_flags=skip_flags)
				ra=",\n    "
		# Second pass: modify new columns
		for c in s.columns():
			nr=""
			try: oc=o.col[c.old_name]
			except KeyError: continue
			else:
				nr,onr = c.dump2(oc,skip_flags=skip_flags)
				oc._tagged=True
				if nr:
					r += ra+nr
					ra=",\n    "
					rb += "#%s: %s\n" % (c.name,", ".join(onr))
		# Third pass: delete old columns
		for c in o.columns():
			if not c._tagged:
				r += ra+"DROP COLUMN `%s`" % (c.name,)
				ra=",\n    "
			else:
				c._tagged=False

		# Now fix the indices
		for k in s.key.values():
			try:
				if 'i' in skip_flags:
					ok=o.key[k.id]
				else:
					ok=o.knames[k.name]
			except KeyError:
				nr=k.dump(skip_flags=skip_flags)
			else:
				if k._diffs(ok,skip_flags=skip_flags):
					nr=k.dump(ok,skip_flags=skip_flags)
				else:
					nr=""
			if nr:
				r += ra+nr
				ra=",\n    "

		return r,rb

	def diff3(s,o,skip_flags=""):
		r=""
		ra="ALTER TABLE %s\n    " % (s.name,)

		if 'k' not in skip_flags:
			for fk in s.fkey.values():
				try:
					if 'i' in skip_flags:
						ok=o.fkey[fk.fields]
					else:
						ok=o.fknames[fk.name]
				except KeyError:
					nr=fk.dump(skip_flags=skip_flags)
				else:
					if fk._diffs(ok,skip_flags=skip_flags):
						nr=fk.dump(ok,skip_flags=skip_flags)
					else:
						nr=""
				if nr:
					r += ra+nr
					ra=",\n    "
		return r
		
	def __str__(self): return "<%s %s>" % (self.name,self.db)
	__repr__=__str__
	def colnames(self):
		n=[]
		c=self.first_col
		while c:
			n.append(c.name)
			c=c.next_col
		return n
		
dbid = 0

class Schema:
	# self.tables: current tables
	# .old_tables: tables when starting up
	#
	def __init__(self, db=None):
		"""Initiiere ein Schema zu einer Datenbank."""
		self.db=db
		self.in_get=False

		self.old_tables={}
		self.tables={}
		global dbid
		dbid += 1
		self.db_id = dbid

	def __str__(self):
		return "db_%d" % (self.db_id,)
	
	def get_table(self,name):

		if self.in_get: return None

		# die Tabelle wird geladen, wenn sie noch nicht ablegegt ist
		try:
			t=self.tables[name]
		except KeyError:
			raise NoSuchTableError(name)

		return t
	
	def scan(self,*a,**k):
		P = SQL(SQLScanner(*a,**k))
		try: P.goal(self)
		except runtime.SyntaxError, e:
			runtime.print_error(e, P._scanner)
			sys.exit(1)

	def dump(self, tables=(),skip_flags=""):
		if tables:
			tv=tables
		else:
			tv=self.tables.keys()
			tv.sort()
		tvv=[]

		for tn in tv:
			t=self.tables[tn]
			if t is None:
				#del self.old_tables[tn]
				continue
			try: ot=self.old_tables[t.name]
			except KeyError: yield t.dump(skip_flags=skip_flags)
			else:
				if ot is None:
					yield t.dump(skip_flags=skip_flags)
				else:
					r=t.diff1(ot,skip_flags=skip_flags)
					if r: yield r
					#del self.old_tables[t.name]
					tvv.append((t,ot))

		for t,ot in tvv:
			r,rb = t.diff2(ot,skip_flags=skip_flags)
			if r:
				yield r
				if verbose:
					print rb
		if "k" not in skip_flags:
			for t,ot in tvv:
				r=t.diff3(ot,skip_flags=skip_flags)
				if r: yield r

		otv=self.old_tables.keys()
		otv.sort()
		for tn in otv:
			# ot=old_tables[tn]
			if tn not in self.tables and (not tables or tn in tables):
				yield "DROP TABLE `%s`" % (tn,)

def main():
	global args,verbose,_debug

	try: from optparse import OptionParser
	except ImportError: from optik import OptionParser

	parser = OptionParser(conflict_handler="resolve")
	parser.add_option("-h","--help","-?", action="help",
						help="print this help text")
	parser.add_option("-v", "--verbose", dest="verbose", action="count",
						help="verbose output", default=1)
	parser.add_option("-q", "--quiet", dest="verbose", action="store_const",
						help="no output", const=0)
	parser.add_option("-s", "--src", dest="db1file", default=None,
						help="database setup with new tables")
	parser.add_option("-d", "--dst", dest="db2file", default=None,
						help="database setup with old tables")
	parser.add_option("-c","--continue", action="store_true", dest="cont",
						help="continue after errors", default=False)
	parser.add_option("-n","--skip-change", action="store", dest="skip_flags",
						help="Skip: c=Charset,a=FieldOrder,k=ForeignKey,i=keyName,p=pack,m=max", default="")

	(opts, args) = parser.parse_args()
	verbose=opts.verbose
	if verbose>1:
		_debug=sys.stderr

	if opts.db1file is not None and opts.db2file is not None and \
			opts.db1file == "-" and opts.db2file == "-":
		print >>sys.stderr,"You can't read STDIN for both files"
		sys.exit(1)

	db2=None
	if opts.db2file:
		trace("Processing",opts.db2file)
		if opts.db2file == "-":
			f=sys.stdin
		else:
			f=open(opts.db2file,"r")
		db2=Schema()
		try: db2.scan("", filename=opts.db2file, file=f)
		except runtime.SyntaxError, e:
			runtime.print_error(e, P._scanner)
			sys.exit(1)

		f.close()

	else:
		print >>sys.stderr,parser.format_help()
		sys.exit(1)

	if opts.db1file:
		trace("Processing",opts.db1file)
		if opts.db1file == "-":
			f=sys.stdin
		else:
			f=open(opts.db1file,"r")
		db1=Schema(db2)

		try: db1.scan("", filename=opts.db1file, file=f)
		except runtime.SyntaxError, e:
			runtime.print_error(e, P._scanner)
			sys.exit(1)

		f.close()

	else:
		if args:
			print >>sys.stderr,parser.format_help()
			sys.exit(1)

	db1.old_tables=db2.tables

	exitcode = 0
	for t in db1.dump(tables=args,skip_flags=opts.skip_flags):
		if t is None: continue

		t += ";"
		print t

		exitcode=2

	return exitcode


### PARSER ###

%%
parser SQL:
	ignore: '[ \r\t\n]+'
	ignore: '#.*?\n'
	ignore: '--\\s.*?\n'
	ignore: '--\n'
	ignore: '/\\*.*?\\*/'
	# TODO: multi-line /*...*/ comments

	token END: "$"

	token ADD: "(?i)ADD"
	token AFTER: "(?i)AFTER"
	token ALTER: "(?i)ALTER"
	token AUTO_INCREMENT: "(?i)AUTO_INCREMENT"
	token CASCADE: "(?i)CASCADE"
	token CHANGE: "(?i)CHANGE"
	token CHARACTER: "(?i)CHARACTER"
	token CHARSET: "(?i)CHARSET"
	token COLUMN: "(?i)COLUMN"
	token COLLATE: "(?i)COLLATE"
	token CONSTRAINT: "(?i)CONSTRAINT"
	token CREATE: "(?i)CREATE"
	token CURRENT_TIMESTAMP: "(?i)CURRENT_TIMESTAMP"
	token DEFAULT: "(?i)DEFAULT"
	token DELETE: "(?i)DELETE"
	token DROP: "(?i)DROP"
	token ENUM: "(?i)ENUM"
	token ENGINE: "(?i)ENGINE"
	token EXISTS: "(?i)EXISTS"
	token FOREIGN: "(?i)FOREIGN"
	token FIRST: "(?i)FIRST"
	token GLOBAL: "(?i)GLOBAL"
	token IF: "(?i)IF"
	token KEY: "(?i)KEY"
	token MAX_ROWS: "(?i)MAX_ROWS"
	token MODIFY: "(?i)MODIFY"
	token NOT: "(?i)NOT"
	token NULL: "(?i)NULL"
	token ON: "(?i)ON"
	token PACK_KEYS: "(?i)PACK_KEYS"
	token PRIMARY: "(?i)PRIMARY"
	token REFERENCES: "(?i)REFERENCES"
	token RESTRICT: "(?i)RESTRICT"
	token SESSION: "(?i)SESSION"
	token SET: "(?i)SET"
	token TABLE: "(?i)TABLE"
	token TYPE: "(?i)TYPE"
	token UNIQUE: "(?i)UNIQUE"
	token UNSIGNED: "(?i)UNSIGNED"
	token UPDATE: "(?i)UPDATE"

	token NAME: "(?i)[a-z][a-z_0-9]*"
	token XNAME: "(?i)[^`]+"
	token SQTEXT: "[^']*"
	token NUM: "-?[0-9]+"

	rule goal<<db>>:
		{{ self.db = db }}
		( statement ";" ? )* END
	
	rule statement:
		s_create | s_alter | s_drop | s_set

	rule s_drop:
		DROP TABLE (
			IF EXISTS qname {{ if self.db.tables.has_key(qname): self.db.get_table(qname).drop() }}
			| qname {{ self.db.get_table(qname).drop() }}
			)

	rule s_alter_add<<t>>:
		ADD s_create_def<<t>>

	rule s_alter_change<<t>>:
		CHANGE COLUMN? qname s_create_col<<t,qname>>

	rule s_alter_modify<<t>>:
		MODIFY COLUMN? s_create_col<<t,True>>

	rule s_alter_del<<t>>:
		DROP
		( ( PRIMARY KEY? {{ name=None }} 
		       | UNIQUE KEY? qname {{ name=qname }}
			   | KEY qname {{ name=qname }}
			   ) 
		  {{ t.del_key(name) }}
		| ( CONSTRAINT | FOREIGN KEY? ) qname {{ t.del_fkey(qname) }}
		| COLUMN? qname {{ t.del_field(qname) }}
		)

	rule s_alter_decl<<t>>:
		( s_alter_add<<t>>
		| s_alter_del<<t>>
		| s_alter_change<<t>>
		| s_alter_modify<<t>>
		)* s_table_opt<<t>>*

	rule s_alter:
		ALTER TABLE qname {{ t=self.db.get_table(qname); trace(qname) }}
		s_alter_decl<<t>> ( "," s_alter_decl<<t>> )*

	rule s_create:
		CREATE TABLE qname {{ t=Table(qname,self.db); trace(qname) }}
		"\(" s_create_def<<t>> ( "," s_create_def<<t>> )*
		     s_create_decl<<t>>* "\)"
		s_table_opt<<t>>*

	rule s_table_opt<<t>>:
		( ENGINE | TYPE ) "=" qname {{ t.engine=qname }}
		| AUTO_INCREMENT "="  NUM
		| DEFAULT? ( CHARACTER SET | CHARSET ) "=" qname {{ t.charset=qname; t.collation=None; }}
		| COLLATE "=" qname {{ t.collation=qname }}
		| PACK_KEYS "=" val {{ t.packing=val }}
		| MAX_ROWS "=" val {{ t.maxrows=val }}

	rule s_create_foreign<<t,name>>:
		{{ fl1=[]; fl2=[] }}
		"\(" qname {{ fl1.append(t.col[qname]) }}
			( "," qname {{ fl1.append(t.col[qname]) }} )* "\)"
		REFERENCES qname {{ rtable=qname }}
		"\(" qname {{ fl2.append(qname) }}
			( "," qname {{ fl2.append(qname) }} )* "\)"
		{{ opt={"update":"cascade","delete":"restrict"} }}
		( 
		  ON ( UPDATE ref_opt {{ opt["update"]=ref_opt.lower() }} 
		     | DELETE ref_opt {{ opt["delete"]=ref_opt.lower() }}
		) )*
		{{ t.new_fkey(name,fl1,rtable,fl2, opt) }}

	rule ref_opt:
		CASCADE {{ return "CASCADE" }}
		| DELETE {{ return "DELETE" }}
		| RESTRICT {{ return "RESTRICT" }}

	rule s_create_def<<t>>:
		( PRIMARY KEY? {{ ktyp="U"; qname=None }}
		| UNIQUE KEY? {{ ktyp="U"; qname="" }} qname?
		| KEY {{ ktyp="-"; qname="" }} qname?
		) {{ name=qname; pkey= [] }}
		"\(" qname {{ klen=None }} ( "\(" val {{ klen=val }} "\)" ) ?
				{{ pkey.append((t.col[qname],klen)); klen=None }} 
		  ( "," qname {{ klen=None }} ( "\(" val {{ klen=val }} "\)" ) ?
		  		{{ pkey.append((t.col[qname],klen)) }} )* "\)"
		  {{ t.new_key(name,ktyp,pkey) }}
		| ( ( CONSTRAINT {{ name=None }} ( qname {{ name=qname }} )? )
		  | {{ name=None }} )
		  FOREIGN KEY? ( qname {{ if name is None: name=qname }} )?
		  s_create_foreign<<t,name>>
		| s_create_col<<t,None>>

	rule s_col_enum<<c>>:
		{{ vals=[] }}
		"\(" val {{ vals.append(val) }} 
		( "," val {{ vals.append(val) }} )* "\)"
		{{ c.tname = tuple(vals) }}

	rule s_create_col<<t,oc>>:
		qname {{ c=t.new_field(qname,oc) }} 
			( ENUM s_col_enum<<c>>
			| qname {{ c.tname = qname.lower() }}
			  ( "\(" NUM {{ c.len=int(NUM) }}
			    ( "," NUM {{ c.len2 = int(NUM) }} ) ? "\)" ) ? 
			)
			(
			  NULL {{ c.nullable=True }}
			| PRIMARY KEY {{ t.new_key(None,"U",[(c,None)]) }}
			| NOT NULL {{ c.nullable=False }}
			| AUTO_INCREMENT {{ c.autoinc=True }}
			| UNSIGNED {{ c.unsigned=True }}
			| (CHARSET | CHARACTER SET) qname {{ c.charset=qname }}
			| COLLATE qname {{ c.collation=qname }}
			| DEFAULT ntval {{ c.defval=ntval }} 
			| ON UPDATE ntval {{ c.updval=ntval }} 
			| FIRST {{ c.set_after(None,oc) }}
			| AFTER qname {{ c.set_after(t.col[qname],oc) }}
			)* {{ c.create_done() }}

	rule s_create_decl<<t>>:
		TYPE "=" NAME
		
	rule s_set: SET ( SESSION | GLOBAL )? qname "=" val

	rule qname: "`" XNAME "`" {{ return XNAME.lower() }}
			| NAME {{ return NAME.lower() }}

	rule nval: NULL {{ return None }}
			| val {{ return val }}

	rule ntval: NULL {{ return None }}
			| CURRENT_TIMESTAMP {{ return curtime }}
			| sval {{ return sval }}

	rule val: NUM {{ return int(NUM) }}
			| "'" SQTEXT "'" {{ return SQTEXT }}

	rule sval: NUM {{ return NUM }}
			| "'" SQTEXT "'" {{ return SQTEXT }}

%%

if __name__ == "__main__":
	sys.exit(main())
