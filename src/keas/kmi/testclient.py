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
"""Test client to access the KMI server API.
"""
from __future__ import print_function

import os
import sys
import optparse
import textwrap
try:
    # Python 3
    from urllib.parse import urlparse
except ImportError:
    # Python 2
    from urlparse import urlparse

from keas.kmi.facility import LocalKeyManagementFacility

def ping(kmf):
    pieces = urlparse(kmf.url)
    conn = kmf.httpConnFactory(pieces.netloc)
    conn.request('GET', '/')
    response = conn.getresponse()
    print(response.status, response.reason)
    print()
    print(response.read())


def new_key(kmf):
    os.write(sys.stdout.fileno(), kmf.generate())


def read_kek(kekfile):
    try:
        with open(kekfile, 'rb') as fp:
            return fp.read()
    except IOError as e:
        print("Could not read key encrypting key from %s" % kekfile, file=sys.stderr)
        print(e, file=sys.stderr)
        sys.exit(1)


def read_data(filename=None):
    if not filename:
        return sys.stdin.read()
    else:
        try:
            with open(filename, 'rb') as fp:
                return fp.read()
        except IOError as e:
            print("Could not read %s" % filename, file=sys.stderr)
            print(e, file=sys.stderr)
            sys.exit(1)


def get_key(kmf, kekfile):
    key_encrypting_key = read_kek(kekfile)
    key = kmf.getEncryptionKey(key_encrypting_key)
    os.write(sys.stdout.fileno(), key)


def encrypt(kmf, kekfile, filename=None):
    key_encrypting_key = read_kek(kekfile)
    data = read_data(filename)
    encrypted = kmf.encrypt(key_encrypting_key, data)
    os.write(sys.stdout.fileno(), encrypted)


def decrypt(kmf, kekfile, filename=None):
    key_encrypting_key = read_kek(kekfile)
    data = read_data(filename)
    decrypted = kmf.decrypt(key_encrypting_key, data)
    os.write(sys.stdout.fileno(), decrypted)


parser = optparse.OptionParser(textwrap.dedent("""\
     %prog URL

           see if the server is alive

           %prog URL -n > key.txt
                generate a new key and key encrypting key

           %prog URL -e key.txt data.txt > encrypted.txt
                encrypt data

           %prog URL -d key.txt encrypted.txt > data.txt
                decrypt data

           %prog URL -g key.txt > secretkey.bin
                get the secret encryption key
    """.rstrip()),
    description="Client for a Key Management Server.")
parser.add_option(
    '-n', '--new',
    help='generate a new key',
    action='store_const', dest='action',
    const=new_key)
parser.add_option(
    '-g', '--get-key',
    help='get key',
    action='store_const', dest='action',
    const=get_key)
parser.add_option(
    '-e', '--encrypt',
    help='encrypt data',
    action='store_const', dest='action',
    const=encrypt)
parser.add_option(
    '-d', '--decrypt',
    help='decrypt data',
    action='store_const', dest='action',
    const=decrypt)

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    opts, args = parser.parse_args(argv)
    if not opts.action:
        opts.action = ping
    if not args:
        parser.error('Please specify the KMS server URL')

    url = args.pop(0)
    kmf = LocalKeyManagementFacility(url)

    try:
        opts.action(kmf, *args)
    except TypeError as err:
        parser.error('incorrect number of arguments')
