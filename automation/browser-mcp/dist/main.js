"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const server_1 = require("./server");
async function main() {
    const server = await (0, server_1.createServer)();
    const listener = server.app.listen(server.config.service.port, server.config.service.host, () => {
        server.logger.info({
            host: server.config.service.host,
            port: server.config.service.port,
            mcpProxyEnabled: server.config.mcp.enabled,
        }, 'browser-mcp service started');
    });
    const shutdown = async () => {
        listener.close();
        await server.close();
        process.exit(0);
    };
    process.on('SIGINT', shutdown);
    process.on('SIGTERM', shutdown);
}
void main();
