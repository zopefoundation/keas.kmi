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
import sys
from six import PY3

# This code was copied from ZODB/_compat.py

if not PY3:
    # Python 2.x
    # PyPy's cPickle doesn't have noload, and noload is broken in Python 2.7,
    # so we need zodbpickle.
    # Get the fastest working version we can (PyPy has no fastpickle)
    try:
        import zodbpickle.fastpickle as cPickle
    except ImportError:
        import zodbpickle.pickle as cPickle
    Pickler = cPickle.Pickler
    Unpickler = cPickle.Unpickler
else:
    # Python 3.x: can't use stdlib's pickle because
    # http://bugs.python.org/issue6784
    import zodbpickle.pickle

    class Pickler(zodbpickle.pickle.Pickler):
        def __init__(self, f, protocol=None):
            super(Pickler, self).__init__(f, protocol)

    class Unpickler(zodbpickle.pickle.Unpickler):
        def __init__(self, f):
            super(Unpickler, self).__init__(f)

        # Py3: Python 3 doesn't allow assignments to find_global,
        # instead, find_class can be overridden

        find_global = None

        def find_class(self, modulename, name):
            if self.find_global is None:
                return super(Unpickler, self).find_class(modulename, name)
            return self.find_global(modulename, name)


try:
    # XXX: why not just import BytesIO from io?
    from cStringIO import StringIO as BytesIO
except ImportError:
    # Python 3.x
    from io import BytesIO
