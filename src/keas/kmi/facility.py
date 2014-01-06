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

import Crypto.Cipher
import Crypto.Cipher.PKCS1_v1_5
import Crypto.PublicKey.RSA
import binascii
import httplib
import logging
import os
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

    CipherFactory = Crypto.Cipher.AES
    CipherMode = Crypto.Cipher.AES.MODE_CBC

    # Note: Decryption fails if you use an empty initialization vector; but it
    # only fails when you restart the Python process.  The length of the
    # initialization vector is assumed to be 16 bytes because that's what
    #   openssl aes-256-cbc -nosalt -P -k 'a'
    # prints if you execute it on the command line
    initializationVector = '0123456789ABCDEF'

    def _pkcs7Encode(self, text, k=16):
        n = k - (len(text) % k)
        return text + binascii.unhexlify(n * ("%02x" % n))

    def _pkcs7Decode(self, text, k=16):
        n = int(binascii.hexlify(text[-1]), 16)
        if n > k:
            raise ValueError("Input is not padded or padding is corrupt")
        return text[:-n]

    _bytesToKeySalt = '12345678'
    def _bytesToKey(self, data):
        # Simplified version of M2Crypto.m2.bytes_to_key().
        assert len(self._bytesToKeySalt) == 8, len(self._bytesToKeySalt)
        data += self._bytesToKeySalt
        key = md5(data).digest()
        key += md5(key + data).digest()
        return key

    def encrypt(self, key, data):
        """See interfaces.IEncryptionService"""
        # 1. Extract the encryption key
        encryptionKey = self._bytesToKey(self.getEncryptionKey(key))
        # 2. Create a cipher object
        cipher = self.CipherFactory.new(
            key=encryptionKey, mode=self.CipherMode,
            IV=self.initializationVector)
        # 3. Apply padding.
        data = self._pkcs7Encode(data)
        # 4. Encrypt the data and return it.
        return cipher.encrypt(data)

    def decrypt(self, key, data):
        """See interfaces.IEncryptionService"""
        # 1. Extract the encryption key
        encryptionKey = self._bytesToKey(self.getEncryptionKey(key))
        # 2. Create a cipher object
        cipher = self.CipherFactory.new(
            key=encryptionKey, mode=self.CipherMode,
            IV=self.initializationVector)
        # 3. Decrypt the data.
        text = cipher.decrypt(data)
        # 4. Remove padding and return result.
        return self._pkcs7Decode(text)


class KeyManagementFacility(EncryptionService):
    zope.interface.implements(interfaces.IExtendedKeyManagementFacility)

    timeout = 3600

    rsaKeyLength = 2048 # The length of the key encrypting key
    rsaKeyExponent = 65537 # Should be sufficiently high and non-symmetric
    rsaPassphrase = 'key management facility'

    keyLength = rsaKeyLength/16

    def __init__(self, storage_dir):
        self.storage_dir = storage_dir
        self.__data_cache = {}
        self.__dek_cache = {}

    def keys(self):
        return [filename[:-4] for filename in os.listdir(self.storage_dir)
                if filename.endswith('.dek')]

    def __iter__(self):
        return iter(self.keys())

    def __getitem__(self, name):
        if name in self.__data_cache:
            return self.__data_cache[name]
        if name+'.dek' not in os.listdir(self.storage_dir):
            raise KeyError(name)
        fn = os.path.join(self.storage_dir, name+'.dek')
        with open(fn, 'rb') as file:
            data = file.read()
            self.__data_cache[name] = data
            return data

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
            file.write(key)
        logger.info('New key added (hash): %s', name)

    def __delitem__(self, name):
        if name in self.__data_cache:
            del self.__data_cache[name]
        fn = os.path.join(self.storage_dir, name+'.dek')
        os.remove(fn)
        logger.info('Key removed (hash): %s', name)

    def generate(self):
        """See interfaces.IKeyGenerationService"""
        # 1. Generate the private/public RSA key encrypting key
        rsa = Crypto.PublicKey.RSA.generate(
            self.rsaKeyLength, e=self.rsaKeyExponent)
        # 2. Extract the private key from the RSA object
        privateKey = rsa.exportKey(passphrase=self.rsaPassphrase)
        # 3. Generate the encryption key
        key = Crypto.Random.new().read(self.keyLength)
        # 4. Create the lookup key in the container
        hash = md5()
        hash.update(privateKey)
        # 5. Save the encryption key
        encryptedKey = Crypto.Cipher.PKCS1_v1_5.new(rsa).encrypt(key)
        self[hash.hexdigest()] = encryptedKey
        # 6. Return the private key encrypting key
        return privateKey

    def getEncryptionKey(self, key):
        """Given the key encrypting key, get the encryption key."""
        # 1. Create the lookup key in the container
        hash = md5()
        hash.update(key)
        hash_key = hash.hexdigest()
        # 2. Try to look up the key in the cache first.
        if (hash_key in self.__dek_cache and
            self.__dek_cache[hash_key][0] + self.timeout > time.time()):
            return self.__dek_cache[hash_key][1]
        # 3. Extract the encrypted encryption key
        encryptedKey = self[hash_key]
        # 4. Decrypt the key.
        rsa = Crypto.PublicKey.RSA.importKey(key, self.rsaPassphrase)
        error = object()
        decryptedKey = Crypto.Cipher.PKCS1_v1_5.new(rsa).decrypt(
            encryptedKey, error)
        if decryptedKey is error:
            raise ValueError('Error while decrypting key.')
        # 5. Return decrypted encryption key
        logger.info('Encryption key requested: %s', hash_key)
        # 6. Add the key to the cache
        self.__dek_cache[hash_key] = (time.time(), decryptedKey)
        # 7. Return the key
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
        self.__cache = {}

    def generate(self):
        """See interfaces.IKeyGenerationService"""
        pieces = urlparse.urlparse(self.url)
        conn = self.httpConnFactory(pieces.netloc)
        conn.request('POST', '/new', '', {})
        response = conn.getresponse()
        data = response.read()
        response.close()
        return data

    def getEncryptionKey(self, key):
        """Given the key encrypting key, get the encryption key."""
        if (key in self.__cache and
            self.__cache[key][0] + self.timeout > time.time()):
            return self.__cache[key][1]
        pieces = urlparse.urlparse(self.url)
        conn = self.httpConnFactory(pieces.netloc)
        conn.request('POST', '/key', key, {'content-type': 'text/plain'})
        response = conn.getresponse()
        encryptionKey = response.read()
        response.close()
        self.__cache[key] = (time.time(), encryptionKey)
        return encryptionKey

    def __repr__(self):
        return '<%s %r>' %(self.__class__.__name__, self.url)
