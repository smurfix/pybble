#!/bin/sh

TMP=$(tempfile)
exec >$TMP 2>&1

set -ex
trap 'cat $TMP >&2; exit 1' 0 1 2 15

## Everything with trailing `&& exit 1` is expected to fail

./manage.py && exit 1
./manage.py -t check
./manage.py -t config

## cleanup

trap 'rm $TMP; exit 0' 0
exit 0
