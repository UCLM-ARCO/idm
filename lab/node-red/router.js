_ = console.info.bind(console);

module.exports = function(RED) {

    function RouterNode(config) {
        RED.nodes.createNode(this,config);

        var node = this;
        this.on('input', function(msg) {
        });
    }

    RED.nodes.registerType("router", RouterNode);
}
