module.exports = function(RED) {

    function DUOIBoolClientNode(config) {
	RED.nodes.createNode(this, config);

	var node = this;
	this.on('input', function(msg) {
	    var state = msg.state == "true";
	    console.info("state:", state, node.dst);
	});
    }

    RED.nodes.registerType("IBool", DUOIBoolClientNode);
}
