_ = console.info.bind(console);

module.exports = function(RED) {

    // load Ice and duo_idm.ice
    var Ice = require("ice").Ice;
    var DUO = require("duo_idm").DUO;

    function DUOIBoolClientNode(config) {
	RED.nodes.createNode(this, config);
	var router_config = RED.nodes.getNode(config.router);

	// create communicator
	var ic = Ice.initialize();

	// get proxy to IDM router
	var router_prx = "ROUTER -o:tcp -h " + router_config.host + " -p " + router_config.port;
	var proxy = ic.stringToProxy(router_prx);

	// create proxy to destination
	var dst_oid = config.dst.toUpperCase().replace(":", "");
	dst_oid = ic.stringToIdentity(dst_oid);
	proxy = proxy.ice_identity(dst_oid);

	// cast to DUO.IDM.IBool.W
	proxy = DUO.IDM.IBool.WPrx.uncheckedCast(proxy);
	this.log("using proxy: " + proxy.toString());

	var node = this;
	this.on('input', function(msg) {
	    // call set(state) on proxy
	    proxy.set(msg.payload, "");
	});
    }

    RED.nodes.registerType("IBool", DUOIBoolClientNode);
}
