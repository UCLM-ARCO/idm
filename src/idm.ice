// -*- mode: c++; coding: utf-8 -*-

module IDM {

    // struct Context:
    //   int ttl;
    //   string source;
    dictionary<string, string> Context;
    sequence<byte> byteSeq;

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

    interface Router extends
        Routing::RouterAdmin,
        NeighborDiscovery::Listener {};

    interface Controller {
        void newNeighbor(string proxy, string routerAddr);
        void newRouter(string proxy);
        void matchingError(Message m);
    };
};
