FROM python:2.7.14

MAINTAINER Shoobx Ops <ops@shoobx.com>

WORKDIR "/opt/keas.kmi"

COPY src/ ./src/
COPY setup.py README.txt CHANGES.txt ./
RUN pip install -e . --no-cache-dir

COPY docker/entrypoint.sh ./
ENTRYPOINT ["bash", "entrypoint.sh"]

VOLUME ["/opt/keas.kmi/keys/"]
EXPOSE 8080

CMD ["run"]


