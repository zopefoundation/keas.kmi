##############################################################################
#
# Copyright (c) 2008 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""
$Id$
"""
import os
from setuptools import setup, find_packages

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

setup (
    name='keas.kmi',
    version='3.2.1',
    author = "Stephan Richter and the Zope Community",
    author_email = "zope-dev@zope.org",
    description = "A Key Management Infrastructure",
    long_description=(
        read('README.txt')
        + '\n\n' +
        read('src', 'keas', 'kmi', 'README.txt')
        + '\n\n' +
        read('src', 'keas', 'kmi', 'persistent.txt')
        + '\n\n' +
        read('CHANGES.txt')
        ),
    license = "ZPL 2.1",
    keywords = "security key management infrastructure nist 800-57",
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Zope Public License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Topic :: Internet :: WWW/HTTP'],
    url = 'http://pypi.python.org/pypi/keas.kmi',
    packages = find_packages('src'),
    include_package_data = True,
    package_dir = {'':'src'},
    namespace_packages = ['keas'],
    extras_require = dict(
        test = [
            'zope.testing',
            'zope.app.testing',
            ],
        ),
    install_requires = [
        'pycrypto',
        'pyramid',
        'pyramid_zcml',
        'setuptools',
        'six',
        'transaction',
        'zope.interface',
        'zope.schema',
        ],
    zip_safe = False,
    entry_points = """
    [console_scripts]
    testclient = keas.kmi.testclient:main

    [paste.app_factory]
    main = keas.kmi.wsgi:application_factory
    """,
)
