"""
WSGI application for the Key Management Server.
"""

import os

from zope.app.wsgi import getWSGIApplication


def application_factory(global_conf, conf='kms.conf', **local_conf):
    configfile = os.path.join(global_conf['here'], conf)
    application = getWSGIApplication(configfile)
    return application

