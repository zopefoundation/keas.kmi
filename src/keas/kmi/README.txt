=============================
Key Management Infrastructure
=============================

This package provides a NIST SP 800-57 compliant key management
infrastructure. Part of this infrastructure is a key management facility that
provides several services related to keys. All keys are stored in a specified
storage directory.

  >>> from __future__ import print_function
  >>> import tempfile
  >>> storage_dir = tempfile.mkdtemp()

  >>> from keas.kmi import facility
  >>> keys = facility.KeyManagementFacility(storage_dir)
  >>> keys
  <KeyManagementFacility (0)>

  >>> from zope.interface import verify
  >>> from keas.kmi import interfaces
  >>> verify.verifyObject(interfaces.IKeyManagementFacility, keys)
  True

One of the services the facility provides in the generation of new keys.

  >>> verify.verifyObject(interfaces.IKeyGenerationService, keys)
  True

The algorithm to generate a new pair of keys is somewhat involved. The
following features are required:

(A) The key local to the data cannot be directly used as the encrypting key.

(B) The encrypting key must be stored using a cipher that is at least as
    strong as the key itself.

(C) The computer storing the data cannot also store the key.

This suggests the following algorithm to generate and store a new encrypting
key:

1. Create the key encrypting key (private and public).

2. Create the encryption key.

3. Use the public key encrypting key to encrypt both the encryption keys.

4. Discard the public key encrypting key. It is important that this key is
   never stored anywhere.

5. Store the encrypted encryption key in the key management facility.

6. Return the private key encrypting key.

Let's now use the key generation service's API to generate a key.

  >>> key = keys.generate()
  >>> print(key.decode())
  -----BEGIN RSA PRIVATE KEY-----
  ...
  -----END RSA PRIVATE KEY-----

By default the system uses the AES 256 cipher, because public commentary
suggests that the AES 196 or AES 256 cipher sufficiently fulfill the PCI,
HIPAA and NIST key strength requirement.

You can now use this key encrypting key to extract the encryption keys:

  >>> from hashlib import md5
  >>> hash_key = md5(key).hexdigest()

  >>> len(keys.get(hash_key))
  256

Our key management facility also supports the encryption service, which allows
you to encrypt and decrypt a string given the key encrypting key.

  >>> verify.verifyObject(interfaces.IEncryptionService, keys)
  True

Let's now encrypt some data:

  >>> encrypted = keys.encrypt(key, b'Stephan Richter')
  >>> len(encrypted)
  16

We can also decrypt the data.

  >>> keys.decrypt(key, encrypted) == b'Stephan Richter'
  True

We can also encrypt data given by a file descriptor

  >>> import tempfile
  >>> tmp_file = tempfile.TemporaryFile()
  >>> data = b"encryptioniscool"*24*1024
  >>> pos = tmp_file.write(data)
  >>> pos = tmp_file.seek(0)
  >>> encrypted_file = tempfile.TemporaryFile()
  >>> keys.encrypt_file(key, tmp_file, encrypted_file)
  >>> tmp_file.close()

And decrypt the file

  >>> decrypted_file = tempfile.TemporaryFile()
  >>> pos = encrypted_file.seek(0)
  >>> keys.decrypt_file(key, encrypted_file, decrypted_file)
  >>> encrypted_file.close()

  >>> pos = decrypted_file.seek(0)
  >>> decrypted_data = decrypted_file.read()
  >>> decrypted_file.close()
  >>> decrypted_data == data
  True

And that's pretty much all there is to it. Most of the complicated
crypto-related work happens under the hood, transparent to the user.

One final note. Once the data encrypting key is looked up and decrypted, it is
cached, since constantly decrypting the the DEK is expensive.

  >>> hash_key in keys._KeyManagementFacility__dek_cache
  True

A timeout (in seconds) controls when a key must be looked up:

  >>> keys.timeout
  3600

Let's now force a reload by setting the timeout to zero:

  >>> keys.timeout = 0

The cache is a dictionary of key encrypting key to a 2-tuple that contains the
date/time the key has been fetched and the unencrypted DEK.

  >>> firstTime = keys._KeyManagementFacility__dek_cache[hash_key][0]

  >>> keys.decrypt(key, encrypted) == b'Stephan Richter'
  True

  >>> secondTime = keys._KeyManagementFacility__dek_cache[hash_key][0]

  >>> firstTime < secondTime
  True


The Local Key Management Facility
---------------------------------

However, using the master key management facility's encryption service is
expensive, since each encryption and decryption request would require a
network request. Fortunately, we can

(A) communicate encryption keys across multiple devices, and

(B) keep encryption keys in memory.

It is only required that the data transfer is completed via an encrypted
communication channel. In this implementation the communication protocol is
HTTP and thus a sufficiently strong SSL connection is appropriate.

Let's now instantiate the local key management facility:

  >>> localKeys = facility.LocalKeyManagementFacility('http://localhost/keys')
  >>> localKeys
  <LocalKeyManagementFacility 'http://localhost/keys'>

The argument to the constructor is the URL to the master key management
facility. The local facility will use a small REST API to communicate with the
server.

For the purpose of this test, we are going to install a network component that
only simulates the requests:

  >>> from keas.kmi import testing
  >>> testing.setupRestApi(localKeys, keys)

As with the master facility, the local facility provides the
``IEncryptionService`` interface:

  >>> verify.verifyObject(interfaces.IEncryptionService, localKeys)
  True

So en- and decryption is very easy to do:

  >>> encrypted = localKeys.encrypt(key, b'Stephan Richter')
  >>> len(encrypted)
  16

  >>> localKeys.decrypt(key, encrypted) == b'Stephan Richter'
  True

Instead of forwarding the en- an decryption request to the master facility,
the local facility merely fetches the encryption key pair and executes the
operation locally. This approach has the following advantages:

(A) There is no general network latency for any en- and decryption call.

(B) The expensive task of en- and decrypting a message is delegated to
    multiple servers, allowing better scaling.

(C) Fetched keys can be cached locally decreasing the network calls to a once
    in a while process.

In this implementation, we do cache the keys in a private attribute:

  >>> key in localKeys._LocalKeyManagementFacility__cache
  True

A timeout (in seconds) controls when a key must be refetched:

  >>> localKeys.timeout
  3600

Let's now force a reload by setting the timeout to zero:

  >>> localKeys.timeout = 0

The cache is a dictionary of key encrypting key to a 3-tuple that contains the
date/time the key has been fetched, the encryption (public) key, and the
decryption (private) key.

  >>> firstTime = localKeys._LocalKeyManagementFacility__cache[key][0]

  >>> localKeys.decrypt(key, encrypted) == b'Stephan Richter'
  True

  >>> secondTime = localKeys._LocalKeyManagementFacility__cache[key][0]

  >>> firstTime < secondTime
  True

The local facility also provides the ``IKeyGenerationService`` interface:

  >>> verify.verifyObject(interfaces.IKeyGenerationService, keys)
  True

The local method call is identical to the master one:

  >>> key2 = localKeys.generate()
  >>> print(key2.decode())
  -----BEGIN RSA PRIVATE KEY-----
  ...
  -----END RSA PRIVATE KEY-----

The operation is forwarded to the master server, so that the key is available
there as well:

  >>> hash = md5(key2)

  >>> hash.hexdigest() in keys
  True


The REST API
------------

The REST API of the master key management facility defines the communication
with the local facility. When a new encryption key pair is created, we simply
make a `POST` call to the following URL::

  http://server:port/new

The request should have no body and the response is simply the key encrypting
key.

So let's have a look at the call:

  >>> from keas.kmi import rest
  >>> from webob import Request

  >>> request = Request({})
  >>> key3 = rest.create_key(keys, request).body
  >>> print(key3.decode())
  -----BEGIN RSA PRIVATE KEY-----
  ...
  -----END RSA PRIVATE KEY-----

The key is available in the facility of course:

  >>> hash = md5(key3)
  >>> hash.hexdigest() in keys
  True

We can now fetch the encryption key pair using a `POST` call to this URL::

  http://server:port/key

The request sends the key encrypting key in its body. The response is the
encryption key string:

  >>> request = Request({})
  >>> request.body = key3

  >>> encKey = rest.get_key(keys, request)
  >>> len(encKey.body)
  128

If you try to request a nonexistent key, you get a 404 error: encryption key
string:

  >>> request.body = b'xxyz'
  >>> print(rest.get_key(keys, request))
  Key not found

A `GET` request to the root shows us a server status page

  >>> print(rest.get_status(keys, Request({})))
  200 OK
  Content-Type: text/plain
  Content-Length: 25
  <BLANKLINE>
  KMS server holding 3 keys


The Testing Key Management Facility
-----------------------------------

The testing facility only manages a single key that is always constant. This
allows you to install a testing facility globally, not storing the keys in the
database and still reuse a ZODB over multiple sessions.

  >>> storage_dir = tempfile.mkdtemp()
  >>> testingKeys = testing.TestingKeyManagementFacility(storage_dir)

Of course, the key generation service is supported:

  >>> verify.verifyObject(interfaces.IKeyGenerationService, keys)
  True

However, you will always receive the same key:

  >>> def getKeySegment(key):
  ...     return str(key.decode().split('\n')[1])

  >>> getKeySegment(testingKeys.generate())
  'MIIBOAIBAAJBAL+VS9lDsS9XOaeJppfK9lhxKMRFdcg50MR3aJEQK9rvDEqNwBS9'
  >>> getKeySegment(testingKeys.generate())
  'MIIBOAIBAAJBAL+VS9lDsS9XOaeJppfK9lhxKMRFdcg50MR3aJEQK9rvDEqNwBS9'

  >>> storage_dir = tempfile.mkdtemp()
  >>> testingKeys = testing.TestingKeyManagementFacility(storage_dir)
  >>> getKeySegment(testingKeys.generate())
  'MIIBOAIBAAJBAL+VS9lDsS9XOaeJppfK9lhxKMRFdcg50MR3aJEQK9rvDEqNwBS9'

All other methods remain the same:

  >>> key = testingKeys.generate()
  >>> testingKeys.getEncryptionKey(key) == b'_\xc4\x04\xbe5B\x7f\xaf\xd6\x92\xbd\xa0\xcf\x156\x1d\x88=p9{\xaal\xb4\x84M\x1d\xfd\xb2z\xae\x1a'
  True

We can also safely en- and decrypt:

  >>> encrypted = testingKeys.encrypt(key, b'Stephan Richter')
  >>> testingKeys.decrypt(key, encrypted) == b'Stephan Richter'
  True


Key Holder
----------

The key holder is a simple class designed to store a key in RAM:

  >>> from keas.kmi import keyholder
  >>> holder = keyholder.KeyHolder(__file__)

  >>> verify.verifyObject(interfaces.IKeyHolder, holder)
  True
