"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.createServer = createServer;
const node_child_process_1 = require("node:child_process");
const node_path_1 = __importDefault(require("node:path"));
const cors_1 = __importDefault(require("cors"));
const express_1 = __importDefault(require("express"));
const http_proxy_middleware_1 = require("http-proxy-middleware");
const env_1 = require("./config/env");
const job_runner_1 = require("./services/job-runner");
const logger_1 = require("./services/logger");
const session_store_1 = require("./services/session-store");
function mcpCliCommand() {
    const packageRoot = node_path_1.default.resolve(__dirname, '..');
    const cliPath = node_path_1.default.resolve(packageRoot, 'node_modules', '@playwright', 'mcp', 'cli.js');
    return {
        command: process.execPath,
        args: [cliPath, '--host', '127.0.0.1'],
        shell: false,
    };
}
async function createServer() {
    const config = (0, env_1.loadConfig)();
    const logger = (0, logger_1.createLogger)(config);
    const runner = new job_runner_1.JobRunner(config);
    const app = (0, express_1.default)();
    const packageRoot = node_path_1.default.resolve(__dirname, '..');
    let mcpProcess;
    app.disable('x-powered-by');
    app.use((0, cors_1.default)());
    if (config.mcp.enabled) {
        const cli = mcpCliCommand();
        mcpProcess = (0, node_child_process_1.spawn)(cli.command, [...cli.args, '--port', String(config.mcp.port), '--browser', config.browser.browserName], {
            env: process.env,
            cwd: packageRoot,
            stdio: 'pipe',
            shell: cli.shell,
        });
        mcpProcess.stdout.on('data', (chunk) => {
            logger.info({ source: 'playwright-mcp', output: String(chunk).trim() }, 'mcp stdout');
        });
        mcpProcess.stderr.on('data', (chunk) => {
            logger.warn({ source: 'playwright-mcp', output: String(chunk).trim() }, 'mcp stderr');
        });
        mcpProcess.on('exit', (code) => {
            logger.warn({ code }, 'playwright-mcp child exited');
        });
        app.use(config.mcp.proxyPath, (0, http_proxy_middleware_1.createProxyMiddleware)({
            target: `http://${config.mcp.host}:${config.mcp.port}`,
            changeOrigin: true,
            ws: true,
            pathRewrite: { [`^${config.mcp.proxyPath}`]: '/mcp' },
        }));
        app.use(config.mcp.ssePath, (0, http_proxy_middleware_1.createProxyMiddleware)({
            target: `http://${config.mcp.host}:${config.mcp.port}`,
            changeOrigin: true,
            ws: true,
        }));
    }
    app.use(express_1.default.json({ limit: '5mb' }));
    app.get('/healthz', (_req, res) => {
        res.json({
            ok: true,
            mcpProxyEnabled: config.mcp.enabled,
        });
    });
    app.post('/api/v1/jobs/run-sync', async (req, res) => {
        const job = req.body;
        const response = await runner.runSync(job);
        const statusCode = response.status === 'failed' ? 500 : 200;
        res.status(statusCode).json(response);
    });
    app.post('/api/v1/jobs', (req, res) => {
        const job = req.body;
        runner.enqueue(job);
        res.status(202).json({ jobId: job.jobId, status: 'pending' });
    });
    app.get('/api/v1/jobs/:jobId', (req, res) => {
        const jobId = Array.isArray(req.params.jobId) ? req.params.jobId[0] : req.params.jobId;
        const job = runner.get(jobId);
        if (!job) {
            res.status(404).json({ error: 'Job not found' });
            return;
        }
        res.json({
            jobId: job.request.jobId,
            status: job.status,
            response: job.response,
        });
    });
    app.get('/api/v1/jobs/:jobId/runtime', (req, res) => {
        const jobId = Array.isArray(req.params.jobId) ? req.params.jobId[0] : req.params.jobId;
        res.json(runner.getRetainedRuntime(jobId));
    });
    app.delete('/api/v1/jobs/:jobId/runtime', async (req, res) => {
        const jobId = Array.isArray(req.params.jobId) ? req.params.jobId[0] : req.params.jobId;
        const released = await runner.releaseRetainedRuntime(jobId);
        res.json({ released });
    });
    app.get('/api/v1/jobs/:jobId/events', (req, res) => {
        const jobId = Array.isArray(req.params.jobId) ? req.params.jobId[0] : req.params.jobId;
        const job = runner.get(jobId);
        if (!job) {
            res.status(404).json({ error: 'Job not found' });
            return;
        }
        res.setHeader('Content-Type', 'text/event-stream');
        res.setHeader('Cache-Control', 'no-cache');
        res.setHeader('Connection', 'keep-alive');
        res.flushHeaders();
        const send = (event, payload) => {
            res.write(`event: ${event}\n`);
            res.write(`data: ${JSON.stringify(payload)}\n\n`);
        };
        send('status', { jobId: job.request.jobId, status: job.status });
        if (job.response) {
            send(job.status, job.response);
            res.end();
            return;
        }
        const onComplete = (payload) => {
            send('completed', payload);
            res.end();
        };
        const onFailed = (payload) => {
            send('failed', payload);
            res.end();
        };
        job.events.once('completed', onComplete);
        job.events.once('failed', onFailed);
        req.on('close', () => {
            job.events.off('completed', onComplete);
            job.events.off('failed', onFailed);
        });
    });
    app.get('/api/v1/sessions', async (_req, res) => {
        const sessions = await (0, session_store_1.listSessions)(config.browser.sessionsRoot);
        res.json({ sessions });
    });
    app.delete('/api/v1/sessions/:sessionRef', async (req, res) => {
        const deleted = await (0, session_store_1.deleteSession)(config.browser.sessionsRoot, req.params.sessionRef);
        res.json({ deleted });
    });
    return {
        app,
        config,
        logger,
        close: async () => {
            if (mcpProcess && !mcpProcess.killed) {
                mcpProcess.kill();
            }
        },
    };
}
