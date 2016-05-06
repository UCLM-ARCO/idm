module.exports = function(RED) {

    function BoolNode(config) {
	RED.nodes.createNode(this, config);
    }

    RED.nodes.registerType("bool-input", BoolNode);

    RED.httpAdmin.post("/bool-input/:id", RED.auth.needsPermission("inject.write"), function(req) {
        var node = RED.nodes.getNode(req.params.id);
        if (node == null)
            res.sendStatus(404);

	node.send(req.body);
    });
}
