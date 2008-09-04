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
"""Implementation of Key Management Facility

$Id$
"""
from __future__ import absolute_import
__docformat__ = "reStructuredText"
import M2Crypto
import datetime
import md5
import persistent
import time
import zope.interface
import zope.location
from z3c.rest import client
from zope.annotation.interfaces import IAttributeAnnotatable
from zope.app.container import btree
from zope.dublincore import property
from zope.schema.fieldproperty import FieldProperty
from keas.kmi import interfaces

class Key(zope.location.Location, persistent.Persistent):
    zope.interface.implements(interfaces.IKey, IAttributeAnnotatable)

    created = property.DCProperty('created')
    creator = property.DCProperty('creator')
    key = FieldProperty(interfaces.IKey['key'])

    def __init__(self, key):
        self.key = key

    def __repr__(self):
        return '<%s %r>' %(self.__class__.__name__, self.key)


class EncryptionService(object):

    cipher = 'aes_256_cbc'

    # Note: decryption fails if you use an empty initialization vector; but it
    # only fails when you restart the Python process.  The length of the
    # initialization vector is assumed to be 16 bytes because that's what
    #   openssl aes-256-cbc -nosalt -P -k 'a'
    # prints if you execute it on the command line
    initializationVector = '0123456789ABCDEF'

    def encrypt(self, key, data):
        """See interfaces.IEncryptionService"""
        # 1. Extract the encryption key
        encryptionKey = self.getEncryptionKey(key)
        # 2. Create a cipher object
        cipher = M2Crypto.EVP.Cipher(
            self.cipher, encryptionKey, self.initializationVector, 1)
        # 3. Feed the data to the cipher
        encrypted = cipher.update(data)
        encrypted += cipher.final()
        # 4. Return encrypted data
        return encrypted

    def decrypt(self, key, data):
        """See interfaces.IEncryptionService"""
        # 1. Extract the encryption key
        encryptionKey = self.getEncryptionKey(key)
        # 2. Create a cipher object
        cipher = M2Crypto.EVP.Cipher(
            self.cipher, encryptionKey, self.initializationVector, 0)
        # 3. Feed the data to the cipher
        decrypted = cipher.update(data)
        decrypted += cipher.final()
        # 4. Return encrypted data
        return decrypted


class KeyManagementFacility(EncryptionService, btree.BTreeContainer):
    zope.interface.implements(interfaces.IExtendedKeyManagementFacility)

    rsaKeyLength = 512 # The length of the key encrypting key
    rsaKeyExponent = 161 # Should be sufficiently high and non-symmetric
    rsaPassphrase = 'key management facility'
    rsaPadding = M2Crypto.RSA.pkcs1_padding

    keyLength = rsaKeyLength/16

    def generate(self):
        """See interfaces.IKeyGenerationService"""
        # 1. Generate the private/public RSA key encrypting key
        rsa = M2Crypto.RSA.gen_key(
            self.rsaKeyLength, self.rsaKeyExponent,
            lambda x: None)
        # 2. Extract the private key from the RSA object
        buf = M2Crypto.BIO.MemoryBuffer('')
        rsa.save_key_bio(buf, None, lambda x: self.rsaPassphrase)
        privateKey = buf.getvalue()
        # 3. Generate the encryption key
        key = M2Crypto.Rand.rand_bytes(self.keyLength)
        # 4. Create the lookup key in the container
        hash = md5.new()
        hash.update(privateKey)
        # 5. Save the encryption key
        encryptedKey = rsa.public_encrypt(key, self.rsaPadding)
        self[hash.hexdigest()] = Key(encryptedKey)
        # 6. Return the private key encrypting key
        return privateKey

    def getEncryptionKey(self, key):
        """Given the key encrypting key, get the encryption key."""
        # 1. Create the lookup key in the container
        hash = md5.new()
        hash.update(key)
        # 2. Extract the encrypted encryption key
        encryptedKey = self[hash.hexdigest()].key
        # 3. Decrypt the key.
        rsa = M2Crypto.RSA.load_key_string(key)
        decryptedKey = rsa.private_decrypt(encryptedKey, self.rsaPadding)
        # 4. Return decrypted encryption key
        return decryptedKey

    def __repr__(self):
        return '<%s (%i)>' %(self.__class__.__name__, len(self))


class LocalKeyManagementFacility(EncryptionService):
    """A local facility that requests keys from the master facility."""
    zope.interface.implements(interfaces.IKeyManagementFacility)

    timeout = 3600
    clientClass = client.RESTClient

    def __init__(self, url):
        self.url = url
        self._cache = {}

    def generate(self):
        """See interfaces.IKeyGenerationService"""
        client = self.clientClass(self.url)
        client.POST('/new')
        return client.contents

    def getEncryptionKey(self, key):
        """Given the key encrypting key, get the encryption key."""
        if (key in self._cache and
            self._cache[key][0] + self.timeout > time.time()):
            return self._cache[key][1]
        client = self.clientClass(self.url)
        client.POST('/key', key)
        encryptionKey = client.contents
        self._cache[key] = (time.time(), encryptionKey)
        return encryptionKey

    def __repr__(self):
        return '<%s %r>' %(self.__class__.__name__, self.url)
