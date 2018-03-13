TEST_FILE?=psef_test/
SHELL=/bin/bash
TEST_FLAGS?=
PYTHON?=env/bin/python3.6
export PYTHONPATH=$(CURDIR)

.PHONY: test_setup
test_setup:
	mkdir -p /tmp/psef/uploads
	mkdir -p /tmp/psef/mirror_uploads

.PHONY: test_quick
test_quick: test_setup
	DEBUG=on env/bin/pytest --cov psef --cov-report term-missing $(TEST_FILE) -vvvvv -x $(TEST_FLAGS)

.PHONY: test
test: test_setup
	DEBUG=on env/bin/pytest --cov psef --cov-report term-missing $(TEST_FILE) -vvvvv $(TEST_FLAGS)

.PHONY: reset_db
reset_db:
	DEBUG_ON=True ./.scripts/reset_database.sh
	$(MAKE) db_upgrade
	$(MAKE) test_data

.PHONY: migrate
migrate:
	DEBUG_ON=True $(PYTHON) manage.py db migrate
	DEBUG_ON=True $(PYTHON) manage.py db edit
	$(MAKE) db_upgrade

.PHONY: db_upgrade
db_upgrade:
	DEBUG_ON=True $(PYTHON) manage.py db upgrade

.PHONY: test_data
test_data:
	DEBUG_ON=True $(PYTHON) $(CURDIR)/manage.py test_data

.PHONY: start_dev_celery
start_dev_celery:
	DEBUG=on env/bin/celery worker --app=runcelery:celery -E -l info

.PHONY: start_dev_server
start_dev_server:
	DEBUG=on ./.scripts/start_dev.sh python

.PHONY: start_dev_npm
start_dev_npm: privacy_statement
	DEBUG=on ./.scripts/start_dev.sh npm

.PHONY: privacy_statement
privacy_statement: src/components/PrivacyNote.vue
src/components/PrivacyNote.vue:
	./.scripts/generate_privacy.py

.PHONY: build_front-end
build_front-end: privacy_statement
	npm run build

.PHONY: seed_data
seed_data:
	DEBUG_ON=True $(PYTHON) $(CURDIR)/manage.py seed

.PHONY: format
format:
	yapf -rip ./psef ./psef_test

.PHONY: shrinkwrap
shrinkwrap:
	npm shrinkwrap --dev

lint:
	pylint psef --rcfile=setup.cfg
