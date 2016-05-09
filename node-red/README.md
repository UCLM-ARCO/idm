This package provides a set of nodes for Node-RED, to communicate with
IDM networks, and some other andy tools as well.

Nodes
=====

* `IBool`: this node provides access to an *IDM.DUO.IBool.W* object, using
  IDM. It has two properties that should be set:

    * **Destination**: the IDM address (like 10:01)
    * **IDM Router**: the router to use (see below)

  When an input with payload "true" or "false" is connected, it will
  send a 'set' message to the given destination, with the proper
  payload value. The `IBool.W` interface is the following:

  ```cpp
  module IBool {
    interface W {
      void set(bool v, IDM::Address source);
    };
  };
  ```

* `idm-router`: this node is a configuration node. It provides the IDM
  router that will be used for all messages. You need to set, at
  least, the host of the router. There are other settings too:

    * **Name**: a local name to easyly recognize the router (not required)
    * **Host**: the IP or hostname where the IDM router is running (required)
    * **Port**: the IDM router's port (required, usually 6140)

* `bool-input`: a simple toggle button to provide input from the
  Node-RED editor. It does not send a predefinded state, but changes
  its state on each click.

References
==========

For a brief description of what IDM is, see: https://bitbucket.org/arco_group/idm
