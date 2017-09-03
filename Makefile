TEST_FILE?=
TEST_FLAGS?=
export PYTHONPATH=$(CURDIR)

.PHONY: test_setup
test_setup:
	mkdir -p /tmp/psef/uploads
	mkdir -p /tmp/psef/mirror_uploads

.PHONY: test_quick
test_quick: test_setup
	DEBUG_ON=True env/bin/pytest --cov psef --cov-report term-missing psef_test/$(TEST_FILE) -vvvvv -x $(TEST_FLAGS)

.PHONY: test
test: test_setup
	DEBUG_ON=True env/bin/pytest --cov psef --cov-report term-missing psef_test/$(TEST_FILE) -vvvvv $(TEST_FLAGS)

.PHONY: reset_db
reset_db:
	DEBUG_ON=True ./.scripts/reset_database.sh
	$(MAKE) db_upgrade
	$(MAKE) test_data

.PHONY: migrate
migrate:
	DEBUG_ON=True env/bin/python3.6 manage.py db migrate
	DEBUG_ON=True env/bin/python3.6 manage.py db edit
	$(MAKE) db_upgrade

.PHONY: db_upgrade
db_upgrade:
	DEBUG_ON=True env/bin/python3.6 manage.py db upgrade

.PHONY: test_data
test_data:
	DEBUG_ON=True env/bin/python3.6 $(CURDIR)/manage.py test_data

.PHONY: start_dev_server
start_dev_server:
	DEBUG_ON=True ./.scripts/start_dev.sh python

.PHONY: start_dev_npm
start_dev_npm:
	DEBUG_ON=True ./.scripts/start_dev.sh npm

build_front-end:
	npm run build

.PHONY: seed_data
seed:
	DEBUG_ON=True env/bin/python3.6 $(CURDIR)/manage.py seed

.PHONY: format
format:
	yapf -rip ./psef ./psef_test

.PHONY: shrinkwrap
shrinkwrap:
	npm shrinkwrap --dev
