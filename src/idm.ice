// -*- mode: c++; coding: utf-8 -*-

module IDM {

    dictionary<string, string> Context;
    sequence<byte> byteSeq;
    sequence<string> stringSeq;

    module NeighborDiscovery {

        interface Listener {
            void adv(string proxy);
            void bye(string oid);
        };
    };

    struct Message {
        string destination;
        string operation;
        byteSeq inParams;
        Context theContext;
    };

    module Routing {

        enum ActionType {Forward};

        struct Matcher {
            string address;
	    byte netmask;
        };

        struct Action {
            ActionType type;
            string next;
        };

        struct Flow {
            int identifier;
            Matcher m;
            Action a;
        };

        sequence<Flow> FlowSeq;

        interface RouterAdmin {
            void flowAdd(Flow f);
            void flowDelete(int identifier);
            FlowSeq flowList();
        };

    };

    interface Router extends
        Routing::RouterAdmin,
        NeighborDiscovery::Listener {};

    interface Controller {
        void newNeighbor(string proxy, string routerAddress);
        void newRouter(string proxy, stringSeq addressList);
        void matchingError(Message m);
    };
};
