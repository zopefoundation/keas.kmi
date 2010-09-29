##############################################################################
#
# Copyright (c) 2008 Zope Corporation and Contributors.
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
import doctest
import tempfile
import transaction
import unittest

from zope.app.testing import setup
from zope.component import provideUtility

from keas.kmi.testing import TestingKeyManagementFacility
from keas.kmi.interfaces import IKeyManagementFacility


def setUpPersistent(test):
    setup.setUpTestAsModule(test, name='keas.kmi.tests.doctestfile')
    setup.placelessSetUp()
    provideUtility(TestingKeyManagementFacility(tempfile.mkdtemp()),
                   provides=IKeyManagementFacility)


def tearDownPersistent(test):
    transaction.abort()
    setup.placelessTearDown()
    setup.tearDownTestAsModule(test)


def test_suite():
    return unittest.TestSuite([
        doctest.DocFileSuite(
            'README.txt',
            optionflags=doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS),
        doctest.DocFileSuite(
            'facility.txt',
            optionflags=doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS),
        doctest.DocFileSuite(
            'persistent.txt',
            setUp=setUpPersistent, tearDown=tearDownPersistent,
            optionflags=doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS),
    ])
