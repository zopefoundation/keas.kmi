FROM python:2.7.14

MAINTAINER Shoobx Ops <ops@shoobx.com>

WORKDIR "/opt/keas.kmi"

COPY docker/build.sh versions.cfg ./
RUN ["bash", "build.sh"]

COPY docker/entrypoint.sh ./
ENTRYPOINT ["bash", "entrypoint.sh"]

COPY src/ ./src/
COPY setup.py README.txt CHANGES.txt ./
RUN pip install -e .

VOLUME ["/opt/keas.kmi/keys/"]
EXPOSE 8080

CMD ["run"]


