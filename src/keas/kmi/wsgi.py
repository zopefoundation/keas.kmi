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
"""WSGI application for the Key Management Server.
"""
import keas.kmi
import os
from repoze.bfg.router import make_app
from keas.kmi import facility

FACILITY = None

def get_facility(environ):
    return FACILITY

def application_factory(global_config, **kw):
    storage_dir = os.path.abspath(kw['storage-dir'])
    if not os.path.exists(storage_dir):
        os.mkdir(storage_dir)
    global FACILITY
    FACILITY = facility.KeyManagementFacility(storage_dir)
    return make_app(get_facility, keas.kmi, options=kw)

