#!/bin/bash

set -ex

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
	if [ $rev = $(cat $REV) ] ; then
		skip=Y
	else
		rm -r $D/$(cat $REV).*
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

SQL=$(tempfile)
DATA=$(tempfile)
rm $DATA
trap 'rm -r $DATA $SQL' 0 1 2 15
cp -a $PYBBLE_SQL_DATABASE $SQL
cp -a $PYBBLE_MEDIA_PATH $DATA
PYBBLE_SQL_DATABASE=$SQL
PYBBLE_MEDIA_PATH=$DATA

./manage.py -t core check
./manage.py -t core config
PYTHONPATH=$(pwd) test/run.py -x

