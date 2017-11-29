#!/usr/bin/env bash
set -eux
HERE="$(dirname $(realpath "$0"))"
PROJECT_DIR="$(realpath "${HERE}/../")"
DOCKER_TAG="${DOCKER_TAG:-shoobx/keas.kmi:$(python setup.py --version)}"

exec docker run -it -p 8080:8080 --rm --name=keas.kmi \
  --mount "type=bind,source=${PROJECT_DIR}/src/keas,target=/opt/keas.kmi/src/keas" \
  --mount "type=bind,source=${PROJECT_DIR}/keys,target=/opt/keas.kmi/keys" \
  "${DOCKER_TAG}" "$@"
