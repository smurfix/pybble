#!/bin/bash

test -n "$*" || set -x
set -e

test -d test || cd ..
test -d test
export PYBBLE=TEST
export PYBBLE_SQL_DRIVER=sqlite
export PYBBLE_SQL_DATABASE=/tmp/empty
export PYBBLE_MEDIA_PATH=/tmp/empty

D=/tmp/pybble/$USER
mkdir -p $D

skip=N

rev=$(git rev-parse --short=9 HEAD)
REV=$D/tag
if [ -f $REV ] ; then
	if [ $rev = $(cat $REV) -a -f $D/$rev.db ] ; then
		skip=Y
	else
		rm -rf $D/$(cat $REV).*
	fi
fi
if [ $skip = N ] ; then
	echo $rev > $REV
	PYBBLE_MEDIA_PATH=$D/$rev.files
	PYBBLE_SQL_DATABASE=$D/$rev.db

	./manage.py -t -S schema -x
	./manage.py -t -S populate
else
	PYBBLE_MEDIA_PATH=$D/$rev.files
	PYBBLE_SQL_DATABASE=$D/$rev.db
fi

DATA=$(tempfile)
SQL=$DATA.db
rm $DATA
cp -a $PYBBLE_SQL_DATABASE $SQL
cp -a $PYBBLE_MEDIA_PATH $DATA
PYBBLE_SQL_DATABASE=$SQL
PYBBLE_MEDIA_PATH=$DATA

SHELL=
PY=python
if [ "$1" = "-k" ] ; then
	shift
	trap 'echo rm -r $DATA $SQL' 0 1 2 15
else
	trap 'rm -r $DATA $SQL' 0 1 2 15
    if [ "$1" = "-p" ] ; then
		shift
		ASS=--assert=plain
    elif [ "$1" = "-d" ] ; then
		PY=pdb
		shift
	fi
fi

if [ "$*" = "" ] ; then
	./manage.py -t core check
	./manage.py -t core config

	#PYTHONPATH=$(pwd) test/run.py -x
	PYTHONPATH=$(pwd) py.test $ASS -x
else
	PYTHONPATH=$(pwd) $PY ./manage.py -t "$@"
fi

