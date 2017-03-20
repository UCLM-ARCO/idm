// -*- mode: c++; coding: utf-8 -*-

#include <IceC/IceC.h>

#define ROUTER_PORT "6140"


class RouterServer {
public:
    void begin();
    void loop_iteration();

private:
    Ice_Communicator _ic;
    Ice_ObjectAdapter _adapter;
};
