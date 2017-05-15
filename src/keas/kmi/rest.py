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
"""REST-API to master key management facility
"""
from webob import Response, exc

def get_status(context, request):
    return Response(
        'KMS server holding %d keys' % len(context),
        charset='utf-8',
        headerlist=[('Content-Type', 'text/plain')])

def create_key(context, request):
    return Response(
        context.generate(),
        charset='utf-8',
        headerlist=[('Content-Type', 'text/plain')])

def get_key(context, request):
    key = request.body
    try:
        return Response(
            context.getEncryptionKey(key),
            charset='utf-8',
            headerlist=[('Content-Type', 'text/plain')])
    except KeyError:
        return exc.HTTPNotFound('Key not found')

