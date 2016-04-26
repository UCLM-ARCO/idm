// -*- mode: c++; coding: utf-8 -*-

module IDM {

    sequence<byte> Address;

    module NeighborDiscovery {

	interface Listener {
	    void adv(string proxy);
	    void bye(Address oid);
	};
    };

    module Routing {

	enum ActionType {Forward};

	struct Matcher {
	    Address dst;
	};

	struct Action {
	    ActionType action;
	    string next;
	};

	interface RouterAdmin {
	    void flowModify(Matcher m, Action a);
	};

    };

    interface Router extends Routing::RouterAdmin, NeighborDiscovery::Listener {};

};
