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
"""Automatic ZODB installation

$Id$
"""
__docformat__ = "reStructuredText"

import transaction
from zope.component import adapter
from zope.app.appsetup.interfaces import IDatabaseOpenedEvent
from zope.app.appsetup.bootstrap import getInformationFromEvent
from zope.app.publication.zopepublication import ZopePublication

from keas.kmi.facility import KeyManagementFacility
from keas.kmi.interfaces import IKeyManagementFacility


@adapter(IDatabaseOpenedEvent)
def bootstrapKeyManagementFacility(event):
    """Installs KeyManagementFacility as the root object of the DB."""
    db, connection, root, root_object = getInformationFromEvent(event)
    if root_object is None:
        root[ZopePublication.root_name] = KeyManagementFacility()
        transaction.commit()
    elif not IKeyManagementFacility.providedBy(root_object):
        raise RuntimeError('Your database root object is not a key management'
                           ' facility.  Remove your Data.fs and try again.')
    connection.close()

