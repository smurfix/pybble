#!/usr/bin/make -f

.PHONY:	test
test:
	nosetests
	echo "app.config" | \
		python manage.py shell --no-ipython | \
		fgrep -qs "SESSION_COOKIE_DOMAIN.:.None"
