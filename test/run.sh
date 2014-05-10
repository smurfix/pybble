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
	-t	trace database execution
	-v	be verbose
	XX	run script XX instead of testing
END
exit $1
}

KEEP=
NOCHECK=
DEBUG=
PLAIN=
REBUILD=
V=
TRACE=
export POSIXLY_CORRECT=1
T="$(/usr/bin/getopt "+dhknprtv" "$@")" || usage 1
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
                -t)
                        shift; TRACE=y ;;
                -v)
                        shift; V=y ;;
                --)
                        shift; break;;
        esac
done
[ "$KEEP$REBUILD" = "yy" ] && usage 1

D=/tmp/pybble/$USER
mkdir -p $D

if [ -n "$TRACE" ] ; then
	export PYBBLE_TRACE=True
fi

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
	[ -z "$V" ] || echo "Building database $NREV"
	if [ -n "$OREV" ] ; then
		rm -rf $D/"$OREV".*
	fi
	rm -f "$rev"
	echo "$NREV" > "$rev"
	PYBBLE_MEDIA_PATH="$D/$NREV".files
	PYBBLE_SQL_DATABASE="$D/$NREV".db

	mkdir -p "$PYBBLE_MEDIA_PATH"
	./manage.py -t -S schema -x
	[ -z "$V" ] || echo "Populating database $NREV"
	./manage.py -t -S populate
	echo "$NREV" > $rev
else
	[ -z "$V" ] || echo "Re-using database $OREV"
	PYBBLE_MEDIA_PATH="$D/$OREV".files
	PYBBLE_SQL_DATABASE="$D/$OREV".db
fi

[ -z "$V" ] || echo "Copying database"
DATA="$(tempfile)"
SQL="$DATA.db"
rm $DATA
cp -a "$PYBBLE_SQL_DATABASE" "$SQL"
cp -a "$PYBBLE_MEDIA_PATH" "$DATA"
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
	[ -z "$V" ] || echo "Consistency check"
	./manage.py -t core check
	[ -z "$V" ] || echo "Config dump"
	./manage.py -t core config | fgrep -qs 'SESSION_COOKIE_DOMAIN=None'

	[ -z "$V" ] || echo "Starting test run"
	#PYTHONPATH=$(pwd) test/run.py -x
	PYTHONPATH=$(pwd) py.test $ASS -x
else
	[ -z "$V" ] || echo "# ./manage.py -t $*"
	PYTHONPATH=$(pwd) $PY ./manage.py -t "$@"
fi

