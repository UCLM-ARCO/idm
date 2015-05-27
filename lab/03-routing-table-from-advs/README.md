
In this example, the XBee trasceiver will be used in an Object Adapter
and in a Proxy, so it will be needed the serial-handler service to
serialize the use of the transceiver.

To launch this demo, you will need at least three terminals. First,
launch the xbee-service, as follows:

    $ ./xbee-service.sh
    INFO:root:SerialHandler @ 'SerialHandler -t -e 1.1:tcp -h 127.0.0.1 -p 6141'
    Service ready, waiting events...

Then, in other terminal, run the router:

    $ ./router.py
    Router at 'Router -t -e 1.1:tcp -h 127.0.0.1 -p 6140:xbee -p idm -n router'
    Waiting events...

And finally, when an advertisement arrives, you can change the status
of the server, using the proxy of the router:

    $ ./client.py "Server -t:tcp -h 127.0.0.1 -p 6140" 1
