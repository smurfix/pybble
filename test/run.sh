#!/bin/bash
if test -z "$BASH_VERSION" ; then
	exec /bin/bash "$0" "$*"
fi

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
	-k	don't delete the databse copy afterwards
	-K	don't copy the database (breaks testing)
	-n	don't rebuild the test database
	-N	don't run the pre-test code
	-p	don't mangle assertions
	-r	always rebuild the test database
	-t	trace database execution
	-v	be verbose
	XX	run script XX instead of testing
END
exit $1
}

KEEP=
KEEPAFTER=
NOCHECK=
DEBUG=
PLAIN=
REBUILD=
V=
TRACE=
NOTEST=
DBG=
DBGENV=
PY="env python"
export POSIXLY_CORRECT=1
while getopts "dhkKnNprtv" i ; do
        case "$i"
        in
                d)
                        DEBUG=y
						DBG=-d
						DBGENV=PYBBLE_DEBUG_WEB=True
						;;
                h)
                        usage 0 ;;
                k)
                        KEEP=y ;;
                n)
                        NOCHECK=y ;;
                N)
                        NOTEST=y ;;
                K)
                        KEEPAFTER=y ;;
                p)
                        PLAIN=y ;;
                r)
                        REBUILD=y ;;
                t)
                        TRACE=y ;;
                v)
                        V=y ;;
                *)
                        usage 1 ;;
                --)
                        break ;;
        esac
done
[ "$NOCHECK$REBUILD" = "yy" ] && usage 1
[ "$KEEP$KEEPAFTER" = "yy" ] && usage 1
[ "$KEEPAFTER" = "y" -a -z "$*" ] && usage 1
shift $((OPTIND-1))

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
elif [ -n "$NOCHECK" ] ; then
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
	$PY ./manage.py -t -S $DBG core schema -x
	[ -z "$V" ] || echo "Populating database $NREV"
	$PY ./manage.py -t -S $DBG core populate
	echo "$NREV" > $rev
else
	[ -z "$V" ] || echo "Re-using database $OREV"
	PYBBLE_MEDIA_PATH="$D/$OREV".files
	PYBBLE_SQL_DATABASE="$D/$OREV".db
fi

if [ -z "$KEEPAFTER" ] ; then
	[ -z "$V" ] || echo "Copying database"
	DATA="$(tempfile)"
	SQL="$DATA.db"
	rm $DATA
	cp -a "$PYBBLE_SQL_DATABASE" "$SQL"
	cp -a "$PYBBLE_MEDIA_PATH" "$DATA"
	PYBBLE_SQL_DATABASE="$SQL"
	PYBBLE_MEDIA_PATH="$DATA"
	if [ -n "$KEEP" ] ; then
		trap 'echo rm -r $DATA $SQL' 0 1 2 15
	else
		trap 'rm -r $DATA $SQL' 0 1 2 15
	fi
else
	[ -z "$V" ] || echo "Modifying the database"
fi

SHELL=
ASS=
if [ -n "$PLAIN" ] ; then
	ASS="$ASS --assert=plain"
fi
if [ -n "$DEBUG" ] ; then
	PY=env pdb
	ASS="$ASS -s --pdb"
fi

if [ "$*" = "" ] ; then
	if [ -z "$NOTEST" ] ; then
		[ -z "$V" ] || echo "Consistency check"
		$PY ./manage.py -t $DBG core check
		[ -z "$V" ] || echo "Config dump"
		$PY ./manage.py -t core config | fgrep -qs 'SESSION_COOKIE_DOMAIN=None'
		# can't drop into pdb here, stdout is redirected
	fi

	[ -z "$V" ] || echo "Starting test run"
	#PYTHONPATH=$(pwd) test/run.py -x
	env PYTHONPATH=$(pwd):$PYTHONPATH $DBGENV py.test $ASS -x
else
	[ -z "$V" ] || echo "# ./manage.py -t $*"
	env PYTHONPATH=$(pwd):$PYTHONPATH $DBGENV $PY ./manage.py -t "$@"
fi

