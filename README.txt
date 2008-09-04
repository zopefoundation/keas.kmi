This package provides a NIST SP 800-57 compliant Key Management Infrastructure
(KMI).

To get started do::

  $ python boostrap.py # Must be Python 2.5
  $ ./bin/buildout # Depends on successfull compilation of M2Crypto
  $ ./bin/paster serve server.ini

The server will come up on port 8080. You can create a new key encrypting key
using::

  $ wget http://localhost:8080/new -O kek.dat

The data encryption key can now be retrieved by posting the KEK to another
URL::

  $ wget http://localhost:8080/key --post-file kek.dat -O datakey.dat

Note: To be compliant, the server must use an encrypted communication channel
of course.
