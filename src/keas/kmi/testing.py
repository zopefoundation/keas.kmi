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
"""Testing Support
"""
from io import BytesIO
import webob
from zope.interface import implementer
from keas.kmi import facility, rest, interfaces

from hashlib import md5

KeyEncyptingKey = b'''-----BEGIN RSA PRIVATE KEY-----
MIIBOAIBAAJBAL+VS9lDsS9XOaeJppfK9lhxKMRFdcg50MR3aJEQK9rvDEqNwBS9
rQlU/x/NWxG0vvFCnrDn7VvQN+syb3+a0DMCAgChAkAzKw3lwPxw0VVccq1J7qeO
4DXR1iEMIoWruiCyq0aLkHnQzrZpaHnd4w+JNKIGOVDEWItf3iZNMXkoqj2hoPmp
AiEA5kWTkYrfH+glJUfV/GvU6jcPSNctcJCnqTfMjQU0KEUCIQDU/R3iz5Lojw1S
R1v6C5gdY/mrQydegHVGFS/p276KFwIgDk124UnRb7IyAlDI6xteUVSDVZ4Pivd+
fP6yEkylbQkCIDo1Ri4VvzRtDsVkmFdqhcucHhIu+UTCHN6uVjy7QmIpAiB7Gl9m
F4a4UlXVivb82J7ew3ZABnFIC9Q+dHW7WeZhxg==
-----END RSA PRIVATE KEY-----
'''

EncryptedEncryptionKey = (
    b'\xbc\x08\xdbo\x04\xe3\xc7G\x13\xd3\x86\x92\xfa\xe8i>,+\xda\xf8/B2]s\xd4'
    b'\x10}[\xfd\x19\x98\xb1\xfa*V~U\xdf\t\x02\x01\xa6\xa8\xae\x8b\x8cm\xd9n'
    b'\xd5\x83\xa1%k\x16lfuY\\q\x8c\x8b')

class FakeHTTPMessage(object):

    def __init__(self, res):
        self.res = res
        self.headers = ['Server: Fake/1.0']

class FakeHTTPResponse(object):

    # These attributes should be overridden by the test setup.
    status = 200
    reason = 'Ok'

    def __init__(self, data):
        self.fp = BytesIO(data)
        self.fp_len = len(data)
        self.msg = FakeHTTPMessage(self)

    def read(self, amt=10*2**10):
        data = self.fp.read(amt)
        if self.fp_len == self.fp.tell():
            self.fp = None
        return data

    def close(self):
        pass


class FakeHTTPConnection(object):

    def __init__(self, host, port=None, timeout=10):
        self.host = host
        self.port = port
        self.request_data = None

    def request(self, method, url, body=None, headers=None):
        self.request_data = (method, url, body, headers)

    def getresponse(self, buffering=False):
        url = self.request_data[1]
        if url == '/new':
            view = rest.create_key
        elif url == '/key':
            view = rest.get_key

        io = BytesIO(self.request_data[2])
        req = webob.Request({'wsgi.input': io})
        res = view(self.context, req)
        return FakeHTTPResponse(res.body)


def setupRestApi(localFacility, masterFacility):
    localFacility.httpConnFactory = type(
        'MyFakeHTTPConnection', (FakeHTTPConnection,),
        {'context': masterFacility})


class TestingKeyManagementFacility(facility.KeyManagementFacility):

    def __init__(self, storage_dir):
        super(TestingKeyManagementFacility, self).__init__(storage_dir)
        md5Key = md5(KeyEncyptingKey).hexdigest()
        self[md5Key] = EncryptedEncryptionKey

    def generate(self):
        return KeyEncyptingKey


@implementer(interfaces.IKeyHolder)
class TestingKeyHolder(object):
    key = KeyEncyptingKey

