// -*- mode: c++; coding: utf-8 -*-

module IDM {

    sequence<byte> Address;

    module NeighborDiscovery {

	interface Listener {
	    void adv(string proxy);
	    void bye(Address oid);
	};
    };

    module Ruting {

	enum ActionType {Forward};

	struct Matcher {
	    Address dst;
	};

	struct Action {
	    ActionType action;
	    string next;
	};

	interface Router {
	    void flowModify(Matcher m, Action a);
	};

    };

};
