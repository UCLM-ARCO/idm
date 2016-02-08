# -*- mode: python; coding: utf-8 -*-

import os
import uuid
# import Ice

import pyendpoint as pe

# pe.log.activated = False
ICE_XENDP_TYPE = 55


class EndpointInfo:
    def __init__(self, strEndpoint):
        pe.trace()

    def __del__(self):
        pe.trace()

    def __str__(self):
        return " "


class EndpointFactoryI(pe.EndpointFactoryI):
    def __init__(self, communicator):
        pe.trace()
        pe.EndpointFactoryI.__init__(self, communicator)

        self._type = ICE_XENDP_TYPE
        self._protocol = "xendp"

    def __del__(self):
        pe.trace()

    def create(self):
        pe.trace()
        return EndpointI(self._communicator, self._protocol)

#     # required by IceGrid
#     def read(self, stream):
#         pe.trace()

#         stream.startReadEncaps()
#         pan = stream.readString()
#         name = stream.readString()
#         stream.endReadEncaps()

#         strEndpoint = " -p {} -n {}".format(pan, name)
#         endp = self.create()
#         endp.initWithOptions(strEndpoint.split(), False)


class EndpointI(pe.EndpointI):
    def __init__(self, communicator, protocol):
        pe.trace()

        pe.EndpointI.__init__(self, communicator, protocol)
        self._info = None
        self._type = ICE_XENDP_TYPE

    def __del__(self):
        pe.trace()

    def initWithOptions(self, args, oaEndpoint):
        self._info = EndpointInfo(" ".join(args))
        self._oaEndpoint = oaEndpoint

    def options(self):
        pe.trace()
        return str(self._info)

    def datagram(self):
        return True

#     # required by IceGrid
#     def streamWrite(self, stream):
#         pe.trace()

#         stream.startWriteEncaps()

#         panid = str(self._info.panID)
#         for i in range(8 - len(panid)):
#             panid += chr(0)

#         # NOTE: writeString prepends size, but panID is always 8 bytes
#         # (with leading 0s if needed).
#         stream.writeBlob(panid, 8)

#         stream.writeString(self._info.nodeName)
#         stream.endWriteEncaps()

    def transceiver(self):
        pe.trace()
        return ServiceTransceiverI(self._communicator, self._protocol, self._info)

    def endpoint(self, trans):
        pe.trace()

        args = str(self._info).split()
        endp = EndpointI(self._communicator, self._protocol)
        endp.initWithOptions(args, self._oaEndpoint)
        return endp

    def equivalent(self, other):
        pe.trace()
        return False

    def connectors_async(self, callback):
        pe.trace()

        conns = [ConnectorI(self._communicator, self._protocol, self._info)]
        callback.connectors(conns)

#     # required by IceGrid
#     def toString(self):
#         pe.trace()

#         handler = self._communicator.propertyToProxy("XBee.Service.Proxy")
#         handler = IceXBeeHandler.SerialHandlerPrx.checkedCast(handler)
#         if handler and self._oaEndpoint:
#             info = handler.getInfo()
#             return "{} -p {} -n {}".format(
#                 self._protocol, info.panID, info.name)

#         return "{} {}".format(self._protocol, str(self._info))


class ConnectorI(pe.ConnectorI):
    def __init__(self, communicator, protocol, info):
        pe.trace()

        pe.ConnectorI.__init__(self, communicator, protocol)
        self._info = info
        self._type = ICE_XENDP_TYPE

    def __del__(self):
        pe.trace()

    def connect(self):
        pe.trace()
        return ServiceTransceiverI(self._communicator, self._protocol, self._info, True)

#     def toString(self):
#         pe.trace()
#         return str(self._info)


# class ReaderI(IceXBeeHandler.Reader):
#     def __init__(self, transceiver):
#         pe.trace()
#         self.transceiver = transceiver

#     def __del__(self):
#         pe.trace()

#     def feed(self, data, current=None):
#         pe.trace()
#         self.transceiver.pushData(data)


class ServiceTransceiverI(pe.TransceiverI):
    def __init__(self, communicator, protocol, info, connect=False):
        pe.trace()

        pe.TransceiverI.__init__(self, communicator, protocol, connect)
        self.info = info
        self.connectionId = uuid.uuid4().get_hex()
        self.connect = connect

        self.setupFD()
        self.setupService(connect)

    def __del__(self):
        pe.trace()

    def bind(self):
        pe.trace()

    def getInfo(self):
        pe.trace()
        return pe.ConnectionInfo(False, "", self.connectionId)

    def setupFD(self):
        pe.trace()
        self.r_fifo, self.w_fifo = os.pipe()

    def setupService(self, connect):
        pe.trace()

        ic = self._communicator
        self.peer = ic.propertyToProxy("Peer.Proxy").ice_datagram()

    def toString(self):
        pe.trace()

        if hasattr(self, "_toString_result"):
            return self._toString_result

        if hasattr(self, "handler"):
            self._toString_result = str(self.handler.getInfo())
        else:
            self._toString_result = str(self.info)

        return self._toString_result

#     def toDetailedString(self):
#         return self.toString()

    def fd(self):
        pe.trace()
        return self.r_fifo

    def write(self, buff):
        pe.trace()
        self.peer.ice_ping()
        return True

#     def pushData(self, data):
#         pe.trace()

#         if not data:
#             return
#         self.in_data += data

#         os.write(self.w_fifo, "B")

#     def read(self, buff):
#         pe.trace()

#         # remove dummy byte from fifo
#         os.read(self.r_fifo, 1)

#         if len(self.in_data) == 0:
#             return True, 0

#         # just for debugging, feel free to remove or uncomment ;)
#         # from hexdump import hexdump
#         # hexdump(self.in_data)

#         # FIXME: if you know a better aproach, please fix me!
#         size = min(len(buff), len(self.in_data))
#         for i in range(size):
#             buff[i] = self.in_data[i]

#         self.in_data = self.in_data[size:]
#         return True, size

    def close(self):
        pe.trace()

        try:
            os.close(self.r_fifo)
        except OSError:
            pass

        try:
            os.close(self.w_fifo)
        except OSError:
            pass

#         if getattr(self, 'reader', None) is None:
#             return

#         try:
#             self.handler.removeReader(self.reader)
#         except Ice.Exception:
#             pass
