module.exports = function(RED) {

    function IDMRouterConfigNode(config) {
	RED.nodes.createNode(this, config);

	this.host = config.host;
	this.port = config.port;
    }

    RED.nodes.registerType("idm-router", IDMRouterConfigNode);
}
