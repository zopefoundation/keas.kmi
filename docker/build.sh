#!/usr/bin/env bash
set -eux

python2 - > requirements.txt <<'PYTHON'
"""convert versions.cfg to requirements.txt
   also remove buildout stuff
"""
import ConfigParser
import re

p = ConfigParser.SafeConfigParser()
assert p.read(['versions.cfg'])

requirements = (
    "{0}=={1}".format(name, version)
    for name, version in p.items('versions')
    if not re.search(r'\.recipe\.|buildout|\.testing', name)
)

for version_string in requirements:
    print(version_string)

PYTHON
rm -f versions.cfg

pip install --no-cache-dir -r requirements.txt
