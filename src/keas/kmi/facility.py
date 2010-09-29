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
"""
from __future__ import absolute_import
__docformat__ = "reStructuredText"

import M2Crypto
import os
import httplib
import logging
import time
import urlparse
import zope.interface
from keas.kmi import interfaces

try:
    from hashlib import md5
except ImportError:
    from md5 import md5

logger = logging.getLogger('kmi')

class EncryptionService(object):

    cipher = 'aes_256_cbc'

    # Note: Decryption fails if you use an empty initialization vector; but it
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


class KeyManagementFacility(EncryptionService):
    zope.interface.implements(interfaces.IExtendedKeyManagementFacility)

    rsaKeyLength = 512 # The length of the key encrypting key
    rsaKeyExponent = 161 # Should be sufficiently high and non-symmetric
    rsaPassphrase = 'key management facility'
    rsaPadding = M2Crypto.RSA.pkcs1_padding

    keyLength = rsaKeyLength/16

    def __init__(self, storage_dir):
        self.storage_dir = storage_dir

    def keys(self):
        return [filename[:-4] for filename in os.listdir(self.storage_dir)
                if filename.endswith('.dek')]

    def __iter__(self):
        return iter(self.keys())

    def __getitem__(self, name):
        if name+'.dek' not in os.listdir(self.storage_dir):
            raise KeyError(name)
        fn = os.path.join(self.storage_dir, name+'.dek')
        with open(fn, 'rb') as file:
            return file.read()

    def get(self, name, default=None):
        try:
            return self[name]
        except KeyError:
            return default

    def values(self):
        return [value for name, value in self.items()]

    def __len__(self):
        return len(self.keys())

    def items(self):
        return [(name, self[name]) for name in self.keys()]

    def __contains__(self, name):
        return name in self.keys()

    has_key = __contains__

    def __setitem__(self, name, key):
        fn = os.path.join(self.storage_dir, name+'.dek')
        with open(fn, 'w') as file:
            return file.write(key)
        logger.info('New key added (hash): %s', name)

    def __delitem__(self, name):
        fn = os.path.join(self.storage_dir, name+'.dek')
        os.remove(fn)
        logger.info('Key removed (hash): %s', name)

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
        hash = md5()
        hash.update(privateKey)
        # 5. Save the encryption key
        encryptedKey = rsa.public_encrypt(key, self.rsaPadding)
        self[hash.hexdigest()] = encryptedKey
        # 6. Return the private key encrypting key
        return privateKey

    def getEncryptionKey(self, key):
        """Given the key encrypting key, get the encryption key."""
        # 1. Create the lookup key in the container
        hash = md5()
        hash.update(key)
        # 2. Extract the encrypted encryption key
        encryptedKey = self[hash.hexdigest()]
        # 3. Decrypt the key.
        rsa = M2Crypto.RSA.load_key_string(key)
        decryptedKey = rsa.private_decrypt(encryptedKey, self.rsaPadding)
        # 4. Return decrypted encryption key
        logger.info('Encryption key requested: %s', hash.hexdigest())
        return decryptedKey

    def __repr__(self):
        return '<%s (%i)>' %(self.__class__.__name__, len(self))


class LocalKeyManagementFacility(EncryptionService):
    """A local facility that requests keys from the master facility."""
    zope.interface.implements(interfaces.IKeyManagementFacility)

    timeout = 3600
    httpConnFactory = httplib.HTTPSConnection

    def __init__(self, url):
        self.url = url
        self._cache = {}

    def generate(self):
        """See interfaces.IKeyGenerationService"""
        pieces = urlparse.urlparse(self.url)
        conn = self.httpConnFactory(pieces.netloc)
        conn.request('POST', '/new', '', {})
        response = conn.getresponse()
        return response.read()

    def getEncryptionKey(self, key):
        """Given the key encrypting key, get the encryption key."""
        if (key in self._cache and
            self._cache[key][0] + self.timeout > time.time()):
            return self._cache[key][1]
        pieces = urlparse.urlparse(self.url)
        conn = self.httpConnFactory(pieces.netloc)
        conn.request('POST', '/key', key, {'content-type': 'text/plain'})
        encryptionKey = conn.getresponse().read()
        self._cache[key] = (time.time(), encryptionKey)
        return encryptionKey

    def __repr__(self):
        return '<%s %r>' %(self.__class__.__name__, self.url)
