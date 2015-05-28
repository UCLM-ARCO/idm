# -*- mode: python; coding: utf-8 -*-

import Ice


class Broker(object):
    def __init__(self, ic):
        self.ic = ic
        self.router = ic.propertyToProxy("IDM.Router.Proxy")
        self.router = self.router.ice_encodingVersion(Ice.Encoding_1_0)

    def getProxy(self, identity):
        identity = self.ic.stringToIdentity(identity)
        return self.router.ice_identity(identity)
