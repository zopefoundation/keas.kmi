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

import Crypto.Cipher
import Crypto.Cipher.PKCS1_v1_5
import Crypto.PublicKey.RSA
from Crypto.Random import random
import binascii
try:
    # Python 3
    from http.client import HTTPSConnection
    from urllib.parse import urlparse
except ImportError:
    # Python 2
    from httplib import HTTPSConnection
    from urlparse import urlparse
import logging
import os
import struct
import time
from zope.interface import implementer
from keas.kmi import interfaces

from hashlib import md5


logger = logging.getLogger('kmi')


@implementer(interfaces.IEncryptionService)
class EncryptionService(object):

    CipherFactory = Crypto.Cipher.AES
    CipherMode = Crypto.Cipher.AES.MODE_CBC

    # Note: Decryption fails if you use an empty initialization vector; but it
    # only fails when you restart the Python process.  The length of the
    # initialization vector is assumed to be 16 bytes because that's what
    #   openssl aes-256-cbc -nosalt -P -k 'a'
    # prints if you execute it on the command line
    initializationVector = b'0123456789ABCDEF'

    def _pkcs7Encode(self, text, k=16):
        n = k - (len(text) % k)
        return text + binascii.unhexlify(n * ("%02x" % n))

    def _pkcs7Decode(self, text, k=16):
        # In Python 3, text[-1] returns an int, not bytes, we need text[-1:] to
        # have bytes. In Python 2, it doesn't matter, both return str.
        # Actually it seems we could just do `n = text[-1]` in Python 3.
        n = int(binascii.hexlify(text[-1:]), 16)
        if n > k:
            raise ValueError("Input is not padded or padding is corrupt")
        return text[:-n]

    _bytesToKeySalt = b'12345678'
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

    def encrypt_file(self, key, fsrc, fdst, chunksize=24*1024):
        """ Encrypts a file with the given key.

        :param key: The encryption key.
        :param fsrc: File descriptor to read from (opened with 'rb')
        :param fdst: File descriptor to write to (opened with 'wb').
                     Its an append operation.
        :param chunksize: Sets the size of the chunk which the function
                          uses to read and encrypt the file. Larger chunk
                          sizes can be faster for some files and machines.
                          chunksize must be divisible by 16.
        """
        # 1. Extract the encryption key
        encryptionKey = self._bytesToKey(self.getEncryptionKey(key))

        # 2. Create a random initialization vector
        # bytes(bytearray(generator)) is needed for Python 2,
        # with Python 3 bytes(generator) works
        iv = bytes(bytearray((random.randint(0, 0xFF)) for i in range(16)))

        # 3. Create a cipher object
        cipher = self.CipherFactory.new(
            key=encryptionKey, mode=self.CipherMode,
            IV=iv
        )

        # 4. Get the current position so we can seek later back to it
        #    so we can write the filesize.
        fdst_startpos = fdst.tell()

        # 5. Write a spacer for the later filesize.
        fdst.write(struct.pack('<Q', 0))

        # 6. Write the initialization vector.
        fdst.write(iv)

        # 7. Read plain and write the encrypted file.
        filesize = 0
        while True:
            chunk = fsrc.read(chunksize)
            if len(chunk) == 0:
                break

            filesize += len(chunk)

            # Apply padding.
            if len(chunk) % 16 != 0:
                chunk += b' ' * (16 - len(chunk) % 16)

            # Write the chunk
            fdst.write(cipher.encrypt(chunk))

        # 8. Write the correct filesize.
        fdst_endpos = fdst.tell()
        fdst.seek(fdst_startpos)
        fdst.write(struct.pack('<Q', filesize))

        # 9. Seek back to end of the file
        fdst.seek(fdst_endpos)

    def decrypt(self, key, data):
        """See interfaces.IEncryptionService

        :raises ValueError: if it can't decrypt the data.
        """
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

    def decrypt_file(self, key, fsrc, fdst, chunksize=24*1024):
        """ Decrypts a file using with the given key.
        Parameters are similar to encrypt_file.

        :raises ValueError: if it can't decrypt the file.
        """
        origsize = struct.unpack('<Q', fsrc.read(struct.calcsize('Q')))[0]
        iv = fsrc.read(16)

        # 1. Extract the encryption key
        encryptionKey = self._bytesToKey(self.getEncryptionKey(key))
        # 2. Create a cipher object
        cipher = self.CipherFactory.new(
            key=encryptionKey, mode=self.CipherMode,
            IV=iv
        )

        while True:
            chunk = fsrc.read(chunksize)
            if len(chunk) == 0:
                break
            fdst.write(cipher.decrypt(chunk))

        fdst.truncate(origsize)


@implementer(interfaces.IExtendedKeyManagementFacility)
class KeyManagementFacility(EncryptionService):

    timeout = 3600

    rsaKeyLength = 2048 # The length of the key encrypting key
    rsaKeyExponent = 65537 # Should be sufficiently high and non-symmetric
    rsaPassphrase = 'key management facility'

    keyLength = rsaKeyLength // 16

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
        with open(fn, 'wb') as file:
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


@implementer(interfaces.IKeyManagementFacility)
class LocalKeyManagementFacility(EncryptionService):
    """A local facility that requests keys from the master facility."""

    timeout = 3600
    httpConnFactory = HTTPSConnection

    def __init__(self, url):
        self.url = url
        self.__cache = {}

    def generate(self):
        """See interfaces.IKeyGenerationService"""
        pieces = urlparse(self.url)
        conn = self.httpConnFactory(pieces.netloc)
        conn.request('POST', '/new', b'', {})
        response = conn.getresponse()
        data = response.read()
        response.close()
        return data

    def getEncryptionKey(self, key):
        """Given the key encrypting key, get the encryption key."""
        if (key in self.__cache and
            self.__cache[key][0] + self.timeout > time.time()):
            return self.__cache[key][1]
        pieces = urlparse(self.url)
        conn = self.httpConnFactory(pieces.netloc)
        conn.request('POST', '/key', key, {'content-type': 'text/plain'})
        response = conn.getresponse()
        encryptionKey = response.read()
        response.close()
        self.__cache[key] = (time.time(), encryptionKey)
        return encryptionKey

    def __repr__(self):
        return '<%s %r>' %(self.__class__.__name__, self.url)
