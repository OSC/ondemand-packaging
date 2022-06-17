VIRTUALENV := ~/.pyenv/versions/3.6.5/envs/ondemand-packaging

default: all

.PHONY: all

all: virtualenv

pyenv-osx:
	brew install pyenv
	pyenv install --patch 3.6.5 < <(curl -sSL https://github.com/python/cpython/commit/8ea6353.patch)
	brew install pyenv-virtualenv

virtualenv: .requirements.txt ## Setup test environment
	test -d  || pyenv virtualenv 3.6.5 ondemand-packaging
	$(VIRTUALENV)/bin/pip install --upgrade pip
	$(VIRTUALENV)/bin/pip install -Ur .requirements.txt
