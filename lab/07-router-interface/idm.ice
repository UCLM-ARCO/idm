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

	struct Flow {
	  int identifier;
	  Matcher m;
	  Action a;
	  // long idle_timeout;
	  // Stats;
	};

	sequence<Flow> FlowSeq;

	interface RouterAdmin {
	  void flowAdd(Flow f);
	  void flowDelete(int identifier);
	  FlowSeq flowList();
	};

    };

    interface Router extends Routing::RouterAdmin, NeighborDiscovery::Listener {};

};
