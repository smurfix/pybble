#!/usr/bin/make -f

all: fetch pybble/utils/sql_diff.py

.PHONY:	test
test:
	@sh test/run.sh -r

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

