"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const strict_1 = __importDefault(require("node:assert/strict"));
const node_http_1 = __importDefault(require("node:http"));
const node_test_1 = require("node:test");
const node_fs_1 = __importDefault(require("node:fs"));
const node_path_1 = __importDefault(require("node:path"));
const env_1 = require("../src/config/env");
const job_runner_1 = require("../src/services/job-runner");
const testRoot = node_path_1.default.resolve(__dirname, 'artifacts');
let server;
let baseUrl = '';
(0, node_test_1.before)(async () => {
    server = node_http_1.default.createServer((req, res) => {
        res.writeHead(200, { 'Content-Type': 'text/html' });
        res.end('<html><head><title>Smoke</title></head><body><h1>Browser MCP</h1></body></html>');
    });
    await new Promise((resolve) => {
        server.listen(0, '127.0.0.1', () => resolve());
    });
    const address = server.address();
    if (!address || typeof address === 'string') {
        throw new Error('Could not resolve test server address');
    }
    baseUrl = `http://127.0.0.1:${address.port}`;
    process.env.BROWSER_MCP_OUTPUT_ROOT = testRoot;
    process.env.BROWSER_MCP_SESSIONS_ROOT = node_path_1.default.join(testRoot, 'sessions');
    process.env.BROWSER_MCP_DEFAULT_HEADLESS = 'true';
});
(0, node_test_1.after)(async () => {
    await new Promise((resolve, reject) => {
        server.close((error) => (error ? reject(error) : resolve()));
    });
});
(0, node_test_1.test)('runSync executes open-url-extract and writes run.json', async () => {
    const config = (0, env_1.loadConfig)();
    const runner = new job_runner_1.JobRunner(config);
    const response = await runner.runSync({
        jobId: 'smoke-open-url',
        scenario: 'open-url-extract',
        target: { url: baseUrl },
        artifacts: {
            screenshot: true,
            snapshot: true,
            pdf: false,
            trace: false,
            saveSession: false,
        },
    });
    strict_1.default.equal(response.status, 'completed');
    const runArtifact = response.artifacts.find((item) => item.endsWith('run.json'));
    strict_1.default.ok(runArtifact);
    strict_1.default.equal(node_fs_1.default.existsSync(runArtifact), true);
});
