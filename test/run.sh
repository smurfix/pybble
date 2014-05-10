#!/bin/bash

test -n "$*" || set -x
set -e

test -d test || cd ..
test -d test
export PYBBLE=TEST
export PYBBLE_SQL_DRIVER=sqlite
export PYBBLE_SQL_DATABASE=/tmp/empty
export PYBBLE_MEDIA_PATH=/tmp/empty

usage() {
cat >&2 <<END
Usage: $(basename $0)  -- run Pybble in a test environment
	-h	this help
	-d	debug when a test fails / run using the debugger
	-k	keep intermediate files
	-n	don't rebuild the test database
	-p	don't mangle assertions
	-r	always rebuild the test database
	XX	run script XX instead of testing
END
exit $1
}

KEEP=
NOCHECK=
DEBUG=
PLAIN=
REBUILD=
export POSIXLY_CORRECT=1
T="$(/usr/bin/getopt "+dhknpr" "$@")" || usage 1
eval set -- "$T"
for i
do
        case "$i"
        in
                -d)
                        shift; DEBUG=y ;;
                -h)
                        usage 0 ;;
                -n)
                        shift; NOCHECK=y ;;
                -k)
                        shift; KEEP=y ;;
                -p)
                        shift; PLAIN=y ;;
                -r)
                        shift; REBUILD=y ;;
                --)
                        shift; break;;
        esac
done
[ "$KEEP$REBUILD" = "yy" ] && usage 1

D=/tmp/pybble/$USER
mkdir -p $D

skip=N

NREV=$(git rev-parse --short=9 HEAD)
rev="$D/tag"
OREV=""
redo=
if [ -f $rev ] ; then
	OREV="$(cat $rev)"
fi
if [ -n "$REBUILD" ] ; then
	redo=Y
elif [ -n "$KEEP" ] ; then
	if [ -z "$OREV" ] ; then
		echo "No existing test database" >&2
		exit 1
	fi
	redo=N
elif [ "$OREV" = "$NREV" ] ; then
	redo=N
else
	redo=Y
fi

if [ $redo = Y ] ; then
	if [ -n "$OREV" ] ; then
		rm -rf $D/"$OREV".*
	fi
	rm -f "$rev"
	echo "$NREV" > "$rev"
	PYBBLE_MEDIA_PATH="$D/$NREV"
	PYBBLE_SQL_DATABASE="$D/$NREV"

	./manage.py -t -S schema -x
	./manage.py -t -S populate
	echo "$NREV" > $rev
else
	PYBBLE_MEDIA_PATH="$D/$OREV".files
	PYBBLE_SQL_DATABASE="$D/$OREV".db
fi

DATA=$(tempfile)
SQL=$DATA.db
rm $DATA
cp -a "$PYBBLE_SQL_DATABASE" $SQL
cp -a "$PYBBLE_MEDIA_PATH" $DATA
PYBBLE_SQL_DATABASE="$SQL"
PYBBLE_MEDIA_PATH="$DATA"

SHELL=
PY=python
ASS=
if [ -n "$KEEP" ] ; then
	shift
	trap 'echo rm -r $DATA $SQL' 0 1 2 15
else
	trap 'rm -r $DATA $SQL' 0 1 2 15
    if [ -n "$PLAIN" ] ; then
		shift
		ASS="$ASS --assert=plain"
	fi
    if [ -n "$DEBUG" ] ; then
		PY=pdb
		ASS="$ASS -s --pdb"
		shift
	fi
fi

if [ "$*" = "" ] ; then
	./manage.py -t core check
	./manage.py -t core config | fgrep -qs 'SESSION_COOKIE_DOMAIN=None'

	#PYTHONPATH=$(pwd) test/run.py -x
	PYTHONPATH=$(pwd) py.test $ASS -x
else
	PYTHONPATH=$(pwd) $PY ./manage.py -t "$@"
fi

