This package provides a set of nodes for Node-RED, to communicate with
IDM networks, and some other andy tools as well.

Nodes
=====

* IBool: this node provides acces to an IDM.DUO.IBool.W object, using
  IDM. It has two properties that should be set:

    * Destination: the IDM address (like 10:01)
    * IDM Router: the router to use (see below)

  When an input with payload "true" or "false" is connected, it will
  send a 'set' message to the given destination, with the proper
  payload value.

* idm-router: this node is a configuration node. It provides the IDM
  router that will be used for all messages. You need to provide, at
  lease, the host of the router. There are other settings too:

    * Name: a local name to easyly recognize the router
    * Host: the IP or hostname where the IDM router is running
    * Port: the IDM router's port (usually 6140)

References
==========

For a brief description of what IDM is, see: https://bitbucket.org/arco_group/idm
