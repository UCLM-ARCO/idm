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
};
