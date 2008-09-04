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
__docformat__ = "reStructuredText"
import zope.interface
import zope.schema
from zope.app.container import interfaces


class IKey(zope.interface.Interface):
    """Encryption Key"""

    created = zope.schema.Datetime(
        title=u'Creation Date/Time',
        description=u'The date/time the key pair was created.',
        required=True)

    creator = zope.schema.TextLine(
        title=u'Creator',
        description=u'The principal/user that requested the new key.',
        required=True)

    key = zope.schema.Bytes(
        title=u'Key',
        description=u'The key used to encrypt and decrypt the data.',
        required=True)


class IEncryptionService(zope.interface.Interface):
    """Utility providing encryption mechanism"""

    def encrypt(key, data):
        """Returns the encrypted data"""

    def decrypt(key, data):
        """Returns the decrypted data"""


class IKeyGenerationService(zope.interface.Interface):
    """A component that can generate a key encryption pair."""

    def generate():
        """Generate a new set of keys.

        Returns the private key encrypting key.
        """

class IKeyManagementFacility(IEncryptionService, IKeyGenerationService):
    """Key Management Facility

    A key management facility provides several key management services.
    """

class IExtendedKeyManagementFacility(IKeyManagementFacility,
                                     interfaces.IContainer):
    """Extended Key Management Facility.

    This facility also also the management of the keys via Python's mapping
    API.
    """


class IKeyHolder(zope.interface.Interface):
    """Key Holder

    A key holder stores a single key.
    """

    key = zope.schema.Bytes(
        title=u'Key',
        description=u'The key used to encrypt and decrypt the data.',
        required=True)

