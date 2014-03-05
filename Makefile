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

fetch: pybble/static/jquery.js pybble/static/jquery.ui.js pybble/static/jquery.ui.css

pybble/static/jquery.js:
	wget -O $@ http://code.jquery.com/jquery-2.0.3.min.js

pybble/static/jquery.ui.js:
	wget -O $@ http://codeorigin.jquery.com/ui/1.10.3/jquery-ui.min.js

pybble/static/jquery.ui.css:
	wget -O $@ http://code.jquery.com/ui/1.10.3/themes/smoothness/jquery-ui.css

