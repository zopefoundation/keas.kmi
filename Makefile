# quick simple makefile to build docker images and whatnot
SHELL := bash

.PHONY: all
all: bin/kmi

.PHONY: clean
clean:
	git clean -dxf

.PHONY: update
update: bin/buildout
	bin/buildout update-versions-file=versions.cfg

bin/kmi: bin/buildout
	ve/bin/pip install 'setuptools<38.2'
	bin/buildout

bin/buildout: venv/bin/python
	venv/bin/python bootstrap.py

ve/ venv/bin/python venv/bin/pip:
	virtualenv -p python2 venv/
