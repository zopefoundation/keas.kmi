FROM python:2.7.14-alpine3.6

MAINTAINER Shoobx Ops <ops@shoobx.com>

WORKDIR /opt/keas.kmi

COPY bootstrap.py ./
RUN python bootstrap.py

COPY src/ buildout.cfg versions.cfg

RUN bin/buildout


