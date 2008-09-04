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

$Id$
"""
from zope.publisher.browser import BrowserPage

class RestView(BrowserPage):

    def __call__(self):
        method = self.request.method
        if not hasattr(self, method):
            self.request.response.setStatus(405)
            return 'Method not allowed.'
        return getattr(self, method)()

class NewView(RestView):

    def GET(self):
        self.request.response.setHeader('content-type', 'text/plain')
        return self.context.generate()

    POST = GET

class KeyView(RestView):

    def POST(self):
        stream = self.request.bodyStream.getCacheStream()
        stream.seek(0)
        key = stream.read()
        self.request.response.setHeader('content-type', 'text/plain')
        return self.context.getEncryptionKey(key)
