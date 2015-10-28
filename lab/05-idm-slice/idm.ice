// -*- mode: c++; coding: utf-8 -*-

module IDM {

    sequence<byte> IDMId;

    interface Listener {
     	void adv(string prx);   // 'prx' is an stringfied proxy
	void bye(IDMId oid);
    };

    module Active {
	interface R {
	    IDMId getObserver();
	};

	interface W {
	    void setObserver(IDMId observer);
	};
    };

};
