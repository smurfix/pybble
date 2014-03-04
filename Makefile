#!/usr/bin/make -f

.PHONY:	test
test:
	@nosetests
	@echo "app.config" | \
		python manage.py shell --no-ipython | \
		grep -qs "SESSION_COOKIE_DOMAIN.:.None"
	@sh test/manager.sh

update:
	@sh utils/update_boilerplate
