#!/usr/bin/make
SHELL=/bin/bash
SQL=mysql
## sql_diff currently doesn't support PostgreSQL.
## sqlite cannot drop columns.

release: tools/sql_diff.py
	@mkdir -p sql; \
	for db in $(SQL) ; do \
		env DATABASE_TYPE=$$db python manage.py showdb > .temp1; \
		if test -f sql/$$db.sql ; then \
		python tools/sql_diff.py -na -q -d sql/$$db.sql -s .temp1 > .temp2 || true; \
		if test -s .temp2; then q=$$(( $$(cat sql/$$db.version) + 1 )); echo $$q > sql/$$db.version; \
			mv .temp1 sql/$$db.sql; mkdir -p sql/$$db; mv .temp2 sql/$$db/$$(printf '%04d' $$q).sql; fi; \
		else echo 1 > sql/$$db.version; mv .temp1 sql/$$db.sql; fi; \
		done; \
		rm -f .temp1 .temp2

tools/sql_diff.py: tools/sql_diff.g
	yapps tools/sql_diff.g
