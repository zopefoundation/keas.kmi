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
"""Encrypted persistent objects
"""
from __future__ import absolute_import
from keas.kmi._compat import BytesIO, Pickler, Unpickler
import persistent
import persistent.wref
from zope.component import getUtility
from keas.kmi.interfaces import IEncryptionService
from keas.kmi.interfaces import IKeyHolder


class EncryptedPersistent(persistent.Persistent):
    """A persistent object that is stored in encrypted form."""

    def __getstate__(self):
        state = super(EncryptedPersistent, self).__getstate__()
        return encrypt_state(state)

    def __setstate__(self, encrypted_state):
        state = decrypt_state(encrypted_state)
        super(EncryptedPersistent, self).__setstate__(state)


def encrypt_state(state):
    key = getUtility(IKeyHolder).key
    service = getUtility(IEncryptionService)
    stringified_data, persistent_refs = pickle_nonpersistent(state)
    encrypted_data = service.encrypt(key, stringified_data)
    return encrypted_data, persistent_refs


def decrypt_state(state):
    encrypted_data, persistent_refs = state
    key = getUtility(IKeyHolder).key
    service = getUtility(IEncryptionService)
    stringified_data = service.decrypt(key, encrypted_data)
    return unpickle_nonpersistent(stringified_data, persistent_refs)


def pickle_nonpersistent(state):
    buf = BytesIO()
    persistent_refs = []
    cache = {}
    def persistent_id(obj):
        # this should probably handle the same kinds of objects that
        # ZODB.serialize.ObjectWriter.persistent_id does.
        if not isinstance(obj, (persistent.Persistent, type,
                                persistent.wref.WeakRef)):
            # Not persistent, pickle normally
            return None
        # Otherwise let ZODB (instead of our local pickler) handle these.
        idx = cache.get(id(obj), None)
        if idx is None:
            idx = cache[id(obj)] = len(persistent_refs)
            persistent_refs.append(obj)
        return idx
    pickler = Pickler(buf, 2)
    pickler.persistent_id = persistent_id
    pickler.dump(state)
    return buf.getvalue(), persistent_refs


def unpickle_nonpersistent(data, persistent_refs):
    buf = BytesIO(data)
    def persistent_load(ref):
        return persistent_refs[ref]
    unpickler = Unpickler(buf)
    unpickler.persistent_load = persistent_load
    return unpickler.load()


def convert_object_to_encrypted(obj):
    """Convert a Persistent object to EncryptedPersistent.

    ``obj`` should be a persistent ghost of a class that used to subclass
    Persistent and now subclasses EncryptedPersistent.

    DO NOT USE THIS METHOD FOR REAL DATA without fully understanding all
    the implications (existing non-persistent bits will continue to be
    stored on the disk).  Also, this function uses black magic.
    """

    # Black magic happens here
    real_setstate = obj.__class__.__setstate__
    obj.__class__.__setstate__ = persistent.Persistent.__setstate__
    obj._p_activate()
    obj.__class__.__setstate__ = real_setstate
    obj._p_changed = True

