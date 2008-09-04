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

import sys
import optparse
import textwrap

from keas.kmi.facility import LocalKeyManagementFacility


def ping(kmf):
    client = kmf.clientClass(kmf.url)
    print client.fullStatus
    print
    print client.contents


def new_key(kmf):
    sys.stdout.write(kmf.generate())


def read_kek(kekfile):
    try:
        return file(kekfile, 'rb').read()
    except IOError, e:
        print >> sys.stderr, "Could not read key encrypting key from %s" % kekfile
        print >> sys.stderr, e
        sys.exit(1)


def read_data(filename=None):
    if not filename:
        return sys.stdin.read()
    else:
        try:
            return file(filename, 'rb').read()
        except IOError, e:
            print >> sys.stderr, "Could not read %s" % filename
            print >> sys.stderr, e
            sys.exit(1)


def get_key(kmf, kekfile):
    key_encrypting_key = read_kek(kekfile)
    key = kmf.getEncryptionKey(key_encrypting_key)
    sys.stdout.write(key)


def encrypt(kmf, kekfile, filename=None):
    key_encrypting_key = read_kek(kekfile)
    data = read_data(filename)
    encrypted = kmf.encrypt(key_encrypting_key, data)
    sys.stdout.write(encrypted)


def decrypt(kmf, kekfile, filename=None):
    key_encrypting_key = read_kek(kekfile)
    data = read_data(filename)
    decrypted = kmf.decrypt(key_encrypting_key, data)
    sys.stdout.write(decrypted)


def main():
    parser = optparse.OptionParser(textwrap.dedent("""\
                usage: %prog URL
                            see if the server is alive

                       %prog URL -n > key.txt
                            generate a new key and key encrypting key

                       %prog URL -e key.txt data.txt > encrypted.txt
                            encrypt data

                       %prog URL -d key.txt encrytped.txt > data.txt
                            decrypt data

                       %prog URL -g key.txt > secretkey.bin
                            get the secret encryption key
                """.rstrip()),
                description="Client for a Key Management Server.")
    parser.add_option('-n', '--new',
                      help='generate a new key',
                      action='store_const', dest='action',
                      const=new_key)
    parser.add_option('-g', '--get-key',
                      help='get key',
                      action='store_const', dest='action',
                      const=get_key)
    parser.add_option('-e', '--encrypt',
                      help='encrypt data',
                      action='store_const', dest='action',
                      const=encrypt)
    parser.add_option('-d', '--decrypt',
                      help='decrypt data',
                      action='store_const', dest='action',
                      const=decrypt)
    opts, args = parser.parse_args()
    if not opts.action:
        opts.action = ping
    if not args:
        parser.error('please specify the KMS server URL')

    url = args.pop(0)
    kmf = LocalKeyManagementFacility(url)

    try:
        opts.action(kmf, *args)
    except TypeError:
        parser.error('incorrect number of arguments')
