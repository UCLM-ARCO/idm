# -*- mode: python; coding: utf-8 -*-

import os
from flask import Flask

from pyendpoint import (
    EndpointFactoryI,
    EndpointI,
    Acceptor,

    trace,
    log,
)

log.activated = True


class HTTPEndpointFactory(EndpointFactoryI):
    def __init__(self, communicator):
        trace()
        EndpointFactoryI.__init__(self, communicator)

        self._type = 25
        self._protocol = "http"

    def create(self):
        trace()
        return HTTPEndpointI(self._communicator, self._protocol)


class HTTPEndpointI(EndpointI):
    def initWithOptions(self, args, oaEndpoint):
        trace()

        self.oaEndpoint = oaEndpoint
        self.host = "0.0.0.0"
        self.port = 8080

        if '-h' in args:
            self.host = args[args.index('-h') + 1]

        if '-p' in args:
            self.port = int(args[args.index('-p') + 1])

    def options(self):
        trace()
        return " -h {} -p {}".format(self.host, self.port)

    def transceiver(self):
        trace()
        return None

    def acceptor(self):
        trace()
        return HTTPAcceptor(self._communicator, self._protocol)

    def endpoint(self, acceptor):
        trace()

        args = self.options().split()
        endp = HTTPEndpointI(self._communicator, self._protocol)
        endp.initWithOptions(args, self.oaEndpoint)
        return endp

#     def connectors_async(self, callback):
#         trace()

#         connectors = [TwowayConnectorI(self._communicator, self._protocol)]
#         callback.connectors(connectors)

    def datagram(self):
        trace()
        return False


class HTTPAcceptor(Acceptor):
    def __init__(self, communicator, protocol):
        trace()

        Acceptor.__init__(self)
        self._communicator = communicator
        self._protocol = protocol

        # self.client = None
        # self.sock = socket.socket(type=socket.SOCK_STREAM)
        # self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # self.sock.bind(("127.0.0.1", 9000))

    def listen(self):
        trace()

        # self.sock.listen(1)
        # self._fd = self.sock.fileno()

        self.create_flask_app()
        self.pipe_r, self.pipe_w = os.pipe()
        self._fd = self.pipe_r

    def close(self):
        trace()
        os.close(self.pipe_r)
        os.close(self.pipe_w)

#     def accept(self):
#         trace()

#         self.client, addr = self.sock.accept()
#         self._fd = self.client.fileno()
#         return TwowayTransceiverI(self._communicator, self._protocol, self.client, True)

    def create_flask_app(self):
        self.flask_app = Flask(__name__)


# class TwowayConnectorI(ConnectorI):
#     def __init__(self, communicator, protocol):
#         trace()
#         ConnectorI.__init__(self, communicator, protocol)
#         self.sock = socket.socket(type=socket.SOCK_STREAM)

#     def connect(self):
#         trace()
#         self.sock.connect(("127.0.0.1", 9000))
#         return TwowayTransceiverI(self._communicator, self._protocol, self.sock, False)

# class TwowayTransceiverI(TransceiverI):
#     def __init__(self, communicator, protocol, sock, incoming=False):
#         trace()

#         TransceiverI.__init__(self, communicator, protocol, fd=sock.fileno())
#         self.incoming = incoming
#         self.sock = sock

#     def toString(self):
#         trace()
#         return "twowayEndp -h 127.0.0.1 -p 9000"

#     def getInfo(self):
#         trace()
#         adapterName = ""
#         connectionId = ""
#         return ConnectionInfo(self.incoming, adapterName, connectionId)

#     def closing(self, initiator):
#         trace()
#         return initiator

#     def write(self, buff):
#         trace()

#         self.sock.send(buff)
#         return True

#     def read(self, buff):
#         trace()

#         size = self.sock.recv_into(buff, len(buff))
#         return True, size

#     def close(self):
#         trace()
#         self.sock.close()
