##############################################################################
#
# Copyright (c) 2013 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
# This code was copied from ZODB/_compat.py

import zodbpickle.pickle


class Pickler(zodbpickle.pickle.Pickler):
    def __init__(self, f, protocol=None):
        super().__init__(f, protocol)


class Unpickler(zodbpickle.pickle.Unpickler):
    def __init__(self, f):
        super().__init__(f)

    # Python doesn't allow assignments to find_global,
    # instead, find_class can be overridden

    find_global = None

    def find_class(self, modulename, name):
        if self.find_global is None:
            return super().find_class(modulename, name)
        return self.find_global(modulename, name)
