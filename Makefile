# quick simple makefile to build docker images and whatnot
SHELL := bash
VENV := venv

DOCKER_IMAGE_NAME ?= shoobx/keas.kmi
KMI_VERSION ?= $(shell python setup.py --version)
export DOCKER_TAG := $(DOCKER_IMAGE_NAME):$(KMI_VERSION)

.PHONY: all  # default target builds kmi locally
all: bin/kmi

.PHONY: clean  # clears untracked files
clean:
	git clean -dxf

.PHONY: update  # generates a new frozen versions.cfg
update: bin/buildout
	bin/buildout update-versions-file=versions.cfg

.PHONY: docker  # builds the docker image
docker:
	docker build -t "$(DOCKER_TAG)" .

.PHONY: docker-publish  # publishes the docker image
docker-publish: docker
	docker push "$(DOCKER_TAG)"

.PHONY: docker-run  # quick example of running this
docker-run: docker keys/
	bash docker/run_dev.sh

bin/kmi: bin/buildout
	$(VENV)/bin/pip install 'setuptools<38.2'
	bin/buildout

bin/buildout: venv/bin/python
	$(VENV)/bin/python bootstrap.py

ve/ venv/bin/python venv/bin/pip:
	virtualenv -p python2 $(VENV)/

keys/:
	mkdir -p "$@"
