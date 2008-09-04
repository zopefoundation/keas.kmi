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
import md5
import cStringIO
from zope.publisher import browser
from zope.interface import implements
from keas.kmi import facility, rest, interfaces

KeyEncyptingKey = '''-----BEGIN RSA PRIVATE KEY-----
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
    '\xbc\x08\xdbo\x04\xe3\xc7G\x13\xd3\x86\x92\xfa\xe8i>,+\xda\xf8/B2]s\xd4'
    '\x10}[\xfd\x19\x98\xb1\xfa*V~U\xdf\t\x02\x01\xa6\xa8\xae\x8b\x8cm\xd9n'
    '\xd5\x83\xa1%k\x16lfuY\\q\x8c\x8b')

class FakeRESTClient(object):

    context = None

    def __init__(self, url):
        self.url = url

    def POST(self, url, data=None):
        io = cStringIO.StringIO(data) if data else None
        request = browser.TestRequest(io)
        request.method = 'POST'
        if url == '/new':
            klass = rest.NewView
        elif url == '/key':
            klass = rest.KeyView
        else:
            raise ValueError(url)

        view = klass(self.context, request)
        self.contents = view()


def setupRestApi(localFacility, masterFacility):
    MyFakeRESTClient = type(
        'FakeRESTClient', (FakeRESTClient,), {'context': masterFacility})
    localFacility.clientClass = MyFakeRESTClient


class TestingKeyManagementFacility(facility.KeyManagementFacility):

    def __init__(self):
        super(TestingKeyManagementFacility, self).__init__()
        hash = md5.new()
        hash.update(KeyEncyptingKey)
        md5Key = hash.hexdigest()
        self[md5Key] = facility.Key(EncryptedEncryptionKey)

    def generate(self):
        return KeyEncyptingKey


class TestingKeyHolder(object):
    implements(interfaces.IKeyHolder)
    key = KeyEncyptingKey

