VIRTUALENV_DIR=virtualenv

default: all

.PHONY: all

all: virtualenv

virtualenv: virtualenv/bin/activate ## Activate test environment
virtualenv/bin/activate: .requirements.txt ## Setup test environment
	test -d $(VIRTUALENV_DIR) || virtualenv $(VIRTUALENV_DIR)
	$(VIRTUALENV_DIR)/bin/pip install -Ur .requirements.txt
	touch $(VIRTUALENV_DIR)/bin/activate
