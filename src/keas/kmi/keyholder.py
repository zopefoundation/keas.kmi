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
"""Simple Key Holder
"""
from zope.interface import implementer
from keas.kmi.interfaces import IKeyHolder


@implementer(IKeyHolder)
class KeyHolder(object):
    """A key holder utility that loads the key from a file and keeps it in RAM."""

    def __init__(self, filename):
        with open(filename, 'rb') as f:
            self.key = f.read()

