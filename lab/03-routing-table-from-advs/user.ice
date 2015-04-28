// -*- mode: c++; coding: utf-8 -*-

module DUO {

    struct Identity {
	string name;
	string category;
    };

    module IBool {
	interface W {
	    void set(bool v, Identity oid);
	};
    };

    interface Listener {
	idempotent void adv(Object* prx);
	idempotent void bye(Identity oid);
    };
};
