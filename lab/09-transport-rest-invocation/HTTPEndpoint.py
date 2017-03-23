# -*- mode: python; coding: utf-8 -*-

import os
from flask import Flask, request
from flask.json import JSONDecoder
from collections import deque, OrderedDict
from threading import Thread, Event

from pyendpoint import (
    EndpointFactoryI,
    EndpointI,
    Acceptor,
    TransceiverI,
    ConnectionInfo,

    trace,
    log,
)

log.activated = False


class EndpointInfo:
    def __init__(self, protocol, host, port, oaEndpoint):
        self.protocol = protocol
        self.host = host
        self.port = port
        self.oaEndpoint = oaEndpoint


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

        self._oaEndpoint = oaEndpoint
        self._host = "0.0.0.0"
        self._port = 8080

        if '-h' in args:
            self._host = args[args.index('-h') + 1]

        if '-p' in args:
            self._port = int(args[args.index('-p') + 1])

        self._info = EndpointInfo(self._protocol, self._host, self._port, self._oaEndpoint)

    def options(self):
        trace()
        return " -h {} -p {}".format(self._host, self._port)

    def transceiver(self):
        trace()
        return None

    def acceptor(self):
        trace()
        return HTTPAcceptor(self._communicator, self._info)

    def endpoint(self, acceptor):
        trace()

        args = self.options().split()
        endp = HTTPEndpointI(self._communicator, self._protocol)
        endp.initWithOptions(args, self._oaEndpoint)
        return endp

#     def connectors_async(self, callback):
#         trace()

#         connectors = [TwowayConnectorI(self._communicator, self._protocol)]
#         callback.connectors(connectors)

    def datagram(self):
        trace()
        return False


class HTTPAcceptor(Acceptor):
    def __init__(self, communicator, info):
        trace()

        Acceptor.__init__(self)
        self._communicator = communicator
        self._info = info
        self._request = None

    def listen(self):
        trace()

        self.create_flask_app()
        self._pipe_r, self._pipe_w = os.pipe()
        self._fd = self._pipe_r

    def close(self):
        trace()
        os.close(self._pipe_r)
        os.close(self._pipe_w)

    def accept(self):
        trace()
        self._request.accept()
        return HTTPTransceiverI(self._communicator, self._info, self._request, True)

    def create_flask_app(self):
        self._flask_app = Flask(__name__)

        def OrderedDictJSONDecoder(*args, **kwargs):
            kwargs['object_pairs_hook'] = OrderedDict
            return JSONDecoder(*args, **kwargs)

        self._flask_app.json_decoder = OrderedDictJSONDecoder

        @self._flask_app.route('/<identity>/<method>', methods=["GET"])
        def get_request(identity, method):
            self._request = PendingRequest(self, identity, method, success_code=200)
            self._request.notify()
            return self._request.wait_response()

        @self._flask_app.route('/<identity>/<method>/<int:item>', methods=["GET"])
        def get_by_id_request(identity, method, item):
            self._request = PendingRequest(self, identity, method, item, success_code=200)
            self._request.notify()
            return self._request.wait_response()

        @self._flask_app.route('/<identity>/<method>', methods=["POST"])
        def add_request(identity, method):
            self._request = PendingRequest(
                self, identity, method, params=request.get_json(), success_code=201)
            self._request.notify()
            return self._request.wait_response()

        @self._flask_app.route('/<identity>/<method>', methods=["PUT"])
        def update_request(identity, method):
            self._request = PendingRequest(
                self, identity, method, params=request.get_json(), success_code=200)
            self._request.notify()
            return self._request.wait_response()

        @self._flask_app.route('/<identity>/<method>/<int:item>', methods=["DELETE"])
        def delete_request(identity, method, item):
            self._request = PendingRequest(self, identity, method, item, success_code=200)
            self._request.notify()
            return self._request.wait_response()

        Thread(
            target = self._flask_app.run,
            kwargs = {'host': self._info.host, 'port': self._info.port, 'threaded': True},
            daemon = True).start()

    def toString(self):
        return "{}:{}".format(self._info.host, self._info.port)

    def toDetailedString(self):
        return "base url = http://{}:{}/".format(self._info.host, self._info.port)


class PendingRequest:
    TOKEN = b"wakeup"

    def __init__(self, acceptor, identity, method, item=None, params={}, success_code=200):
        trace()

        self.acceptor = acceptor
        self.ready = Event()
        self.ice_message = b""
        self.response = b"<unknown>"
        self.success_code = success_code
        self.response_code = 400

        self.build_ice_message(identity, method, item, params)

    def notify(self):
        trace()
        os.write(self.acceptor._pipe_w, self.TOKEN)

    def accept(self):
        trace()
        assert(os.read(self.acceptor._pipe_r, len(self.TOKEN)) == self.TOKEN)

    def build_ice_message(self, identity, method, item, params):
        trace()

        # struct HeaderData
        header = [
            73, 99, 101, 80,            # int  magic
            1,                          # byte protocolMajor
            0,                          # byte protocolMinor
            1,                          # byte encodingMajor
            0,                          # byte encodingMinor
            0,                          # byte messageType - 0: request
            0,                          # byte compressionStatus - 0: no compression
            0, 0, 0, 0,                 # int  messageSize - placeholder
        ]

        # struct RequestData
        body = [
            1, 0, 0, 0,                 # int requestId - x, not reused connection
            * self.pack_oid(identity),  # Ice::Identity id
            0,                          # Ice::StringSeq facet - 0: no facet
            * self.pack_str(method),    # string operation
            0,                          # byte mode - 0: normal
            0,                          # Ice::Context context - 0: no context
        ]

        # encapsulation params
        encap = [
            0, 0, 0, 0,                 # int size - placeholder
            1,                          # byte major
            0,                          # byte minor
        ]

        # if 'item' is given, include it on encapsulation (as an integer)
        if item is not None:
            encap += self.pack_int(int(item))

        # append params (if any) to encapsulation
        for k, v in params.items():
            encap += {
                int: self.pack_int,
                str: self.pack_str,
                bool: self.pack_bool
            }[type(v)](v)

        # update sizes
        encap[:4] = self.pack_int(len(encap))
        header[10:14] = self.pack_int(len(header) + len(body) + len(encap))
        self.ice_message = bytes(header + body + encap)

    def pack_oid(self, name):
        return self.pack_str(name) + [0]

    def pack_str(self, s):
        return [len(s)] + list(bytes(s, "utf-8"))

    def pack_int(self, i):
        return [i & 0xff, (i >> 8) & 0xff, (i >> 16) & 0xff, (i >> 24) & 0xff]

    def pack_bool(self, b):
        return [1 if b else 0]

    def wait_response(self):
        trace()
        self.ready.wait()
        return self.response, self.response_code

    def set_response(self, buff):
        trace()

        # validate message header
        header = [73, 99, 101, 80, 1, 0, 1, 0]
        assert (list(buff[:len(header)]) == header), "Invalid message format on reply!"
        i = len(header)

        # process rest of message
        if buff[i] == 2:
            return self.parse_reply(buff, i + 1)
        elif buff[i] == 4:
            return self.parse_close_connection(buff, i + 1)

    def parse_close_connection(self, buff, i):
        pass

    def parse_reply(self, buff, i):
        assert buff[i] == 0, "ERROR: no compression supported!"

        # check reply status
        i += 1 + 4 + 4  # compression + message size + requestId
        status = buff[i]
        i += 1

        # ok, get response (if any), only string supported, no out params supported
        if status == 0:

            # if first byte of encap size is 6, there is no return value
            if buff[i] == 6:
                self.response = b""
                self.response_code = 204

            else:
                i += 6  # encap size + major + minor
                size = buff[i]

                i += 1  # string size
                if size == 255:
                    size = buff[i] << 24 + buff[i + 1] << 16 + buff[i + 2] << 8 + buff[i + 3]
                    i += 4

                self.response = bytes(buff[i:])
                self.response_code = self.success_code

        elif status == 1:
            self.response = "ERROR: User exception"
        elif status == 2:
            self.response = "ERROR: Object does not exist"
            self.response_code = 404
        elif status == 3:
            self.response = "ERROR: Facet does not exist"
            self.response_code = 404
        elif status == 4:
            self.response = "ERROR: Operation does not exist"
            self.response_code = 404
        elif status in [5, 6, 7]:
            i += 5 if buff[i] == 255 else 1
            self.response = b"ERROR: Exception raised:\n------\n\n" + bytes(buff[i:])

        self.ready.set()

    def size(self):
        trace()
        return len(self.ice_message)

    def write_into(self, buff):
        trace()
        size = min(len(buff), len(self.ice_message))
        buff[:size] = self.ice_message
        self.ice_message = self.ice_message[size:]

        return size


# class TwowayConnectorI(ConnectorI):
#     def __init__(self, communicator, protocol):
#         trace()
#         ConnectorI.__init__(self, communicator, protocol)
#         self._sock = socket.socket(type=socket.SOCK_STREAM)

#     def connect(self):
#         trace()
#         self._sock.connect(("127.0.0.1", 9000))
#         return TwowayTransceiverI(self._communicator, self._protocol, self._sock, False)


class HTTPTransceiverI(TransceiverI):
    def __init__(self, communicator, info, request, incoming=False):
        trace()

        TransceiverI.__init__(self, communicator, info.protocol)
        self._info = info
        self._incoming = incoming
        self._request = request
        self._validated = False

        self._pipe_r, self._pipe_w = os.pipe()
        self._fd = self._pipe_r

    def toString(self):
        trace()
        return "{} -h {} -p {}".format(
            self._info.protocol, self._info.host, self._info.port)

    def getInfo(self):
        trace()
        adapterName = ""
        connectionId = ""
        return ConnectionInfo(self._incoming, adapterName, connectionId)

    def closing(self, initiator):
        trace()
        return initiator

    def write(self, buff):
        trace()

        # first message sent is a validate connection, ack it
        if not self._validated:
            validate_msg = [73, 99, 101, 80, 1, 0, 1, 0, 3, 0, 14, 0, 0, 0]
            assert (list(buff) == validate_msg), "Invalid validation message!"
            self._validated = True

            # notify IC that we have a pending message
            os.write(self._pipe_w, PendingRequest.TOKEN)

            return True

        # otherwise, is a reply
        self._request.set_response(buff)
        return True

    def read(self, buff):
        trace()
        size = self._request.write_into(buff)

        # remove notification if message is sent completly
        if self._request.size() == 0:
            os.read(self._pipe_r, len(PendingRequest.TOKEN))

        return True, size

    def close(self):
        trace()
        os.close(self._pipe_r)
        os.close(self._pipe_w)
