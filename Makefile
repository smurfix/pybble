#!/usr/bin/make -f

all: fetch pybble/utils/sql_diff.py

.PHONY:	test retest
test:
	@sh test/run.sh -rv
retest:
	@sh test/run.sh -nvN

upgrade:
	./manage.py core migrate upgrade

rev:
	./manage.py core migrate revision --auto
	git add migrations/versions

update:
	@sh utils/update_boilerplate

.PHONY: fetch
fetch: pybble/static/jquery.js pybble/static/jquery.ui.js pybble/static/jquery.ui.css

pybble/static/jquery.js:
	wget -O $@ http://code.jquery.com/jquery-2.0.3.min.js

pybble/static/jquery.ui.js:
	wget -O $@ http://codeorigin.jquery.com/ui/1.10.3/jquery-ui.min.js

pybble/static/jquery.ui.css:
	wget -O $@ http://code.jquery.com/ui/1.10.3/themes/smoothness/jquery-ui.css

pybble/utils/sql_diff.py: pybble/utils/sql_diff.g
	yapps $< $@

