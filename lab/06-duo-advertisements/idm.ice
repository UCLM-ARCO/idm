// -*- mode: c++; coding: utf-8 -*-

module IDM {

    sequence<byte> Address;

    module NeighborDiscovery {

	interface Listener {
	    void adv(string proxy);
	    void bye(Address oid);
	};
    };
};
