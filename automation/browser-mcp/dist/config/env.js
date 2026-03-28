"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.loadConfig = loadConfig;
const node_fs_1 = __importDefault(require("node:fs"));
const node_path_1 = __importDefault(require("node:path"));
const zod_1 = require("zod");
const configSchema = zod_1.z.object({
    service: zod_1.z.object({
        host: zod_1.z.string().default('0.0.0.0'),
        port: zod_1.z.number().int().positive().default(8930),
        logLevel: zod_1.z.enum(['debug', 'info', 'warn', 'error']).default('info'),
    }),
    mcp: zod_1.z.object({
        enabled: zod_1.z.boolean().default(true),
        host: zod_1.z.string().default('127.0.0.1'),
        port: zod_1.z.number().int().positive().default(8931),
        proxyPath: zod_1.z.string().default('/mcp'),
        ssePath: zod_1.z.string().default('/sse'),
    }),
    browser: zod_1.z.object({
        browserName: zod_1.z.enum(['chromium', 'firefox', 'webkit']).default('chromium'),
        chromiumChannel: zod_1.z.string().optional().default(''),
        headless: zod_1.z.boolean().default(true),
        viewport: zod_1.z.object({
            width: zod_1.z.number().int().positive().default(1440),
            height: zod_1.z.number().int().positive().default(900),
        }),
        userAgent: zod_1.z.string().optional().default(''),
        proxyServer: zod_1.z.string().optional().default(''),
        allowedOrigins: zod_1.z.array(zod_1.z.string()).default([]),
        blockedOrigins: zod_1.z.array(zod_1.z.string()).default([]),
        actionTimeoutMs: zod_1.z.number().int().nonnegative().default(10000),
        navigationTimeoutMs: zod_1.z.number().int().nonnegative().default(60000),
        outputRoot: zod_1.z.string().default('../../tests/artifacts/browser-mcp'),
        sessionsRoot: zod_1.z.string().default('../../tests/artifacts/browser-mcp/sessions'),
    }),
    artifacts: zod_1.z.object({
        trace: zod_1.z.boolean().default(true),
        screenshot: zod_1.z.boolean().default(true),
        pdf: zod_1.z.boolean().default(false),
        snapshot: zod_1.z.boolean().default(true),
        saveSession: zod_1.z.boolean().default(false),
    }),
});
function parseBoolean(value, fallback) {
    if (value === undefined || value === '') {
        return fallback;
    }
    return ['1', 'true', 'yes', 'on'].includes(value.toLowerCase());
}
function parseCsv(value) {
    if (!value) {
        return [];
    }
    return value
        .split(/[;,]/)
        .map((item) => item.trim())
        .filter(Boolean);
}
function resolveRoot(baseDir, relativeOrAbsolute) {
    return node_path_1.default.isAbsolute(relativeOrAbsolute)
        ? relativeOrAbsolute
        : node_path_1.default.resolve(baseDir, relativeOrAbsolute);
}
function loadConfig() {
    const repoRoot = node_path_1.default.resolve(__dirname, '..', '..');
    const configPath = process.env.BROWSER_MCP_CONFIG_PATH ||
        node_path_1.default.resolve(repoRoot, 'config', 'browser-mcp.config.json');
    const baseConfig = configSchema.parse(JSON.parse(node_fs_1.default.readFileSync(configPath, 'utf-8')));
    const merged = {
        service: {
            host: process.env.BROWSER_MCP_SERVICE_HOST || baseConfig.service.host,
            port: Number(process.env.BROWSER_MCP_SERVICE_PORT || baseConfig.service.port),
            logLevel: process.env.BROWSER_MCP_LOG_LEVEL ||
                baseConfig.service.logLevel,
        },
        mcp: {
            enabled: parseBoolean(process.env.BROWSER_MCP_PROXY_ENABLED, baseConfig.mcp.enabled),
            host: process.env.BROWSER_MCP_PROXY_HOST || baseConfig.mcp.host,
            port: Number(process.env.BROWSER_MCP_PROXY_PORT || baseConfig.mcp.port),
            proxyPath: process.env.BROWSER_MCP_PROXY_PATH || baseConfig.mcp.proxyPath,
            ssePath: process.env.BROWSER_MCP_PROXY_SSE_PATH || baseConfig.mcp.ssePath,
        },
        browser: {
            browserName: process.env.BROWSER_MCP_DEFAULT_BROWSER ||
                baseConfig.browser.browserName,
            chromiumChannel: process.env.BROWSER_MCP_CHROMIUM_CHANNEL || baseConfig.browser.chromiumChannel,
            headless: parseBoolean(process.env.BROWSER_MCP_DEFAULT_HEADLESS, baseConfig.browser.headless),
            viewport: {
                width: Number(process.env.BROWSER_MCP_VIEWPORT_WIDTH || baseConfig.browser.viewport.width),
                height: Number(process.env.BROWSER_MCP_VIEWPORT_HEIGHT || baseConfig.browser.viewport.height),
            },
            userAgent: process.env.BROWSER_MCP_USER_AGENT || baseConfig.browser.userAgent,
            proxyServer: process.env.BROWSER_MCP_PROXY_SERVER || baseConfig.browser.proxyServer,
            allowedOrigins: parseCsv(process.env.BROWSER_MCP_ALLOWED_ORIGINS).length > 0
                ? parseCsv(process.env.BROWSER_MCP_ALLOWED_ORIGINS)
                : baseConfig.browser.allowedOrigins,
            blockedOrigins: parseCsv(process.env.BROWSER_MCP_BLOCKED_ORIGINS).length > 0
                ? parseCsv(process.env.BROWSER_MCP_BLOCKED_ORIGINS)
                : baseConfig.browser.blockedOrigins,
            actionTimeoutMs: Number(process.env.BROWSER_MCP_ACTION_TIMEOUT_MS || baseConfig.browser.actionTimeoutMs),
            navigationTimeoutMs: Number(process.env.BROWSER_MCP_NAVIGATION_TIMEOUT_MS || baseConfig.browser.navigationTimeoutMs),
            outputRoot: resolveRoot(repoRoot, process.env.BROWSER_MCP_OUTPUT_ROOT || baseConfig.browser.outputRoot),
            sessionsRoot: resolveRoot(repoRoot, process.env.BROWSER_MCP_SESSIONS_ROOT || baseConfig.browser.sessionsRoot),
        },
        artifacts: {
            trace: parseBoolean(process.env.BROWSER_MCP_TRACE_DEFAULT, baseConfig.artifacts.trace),
            screenshot: parseBoolean(process.env.BROWSER_MCP_SCREENSHOT_DEFAULT, baseConfig.artifacts.screenshot),
            pdf: parseBoolean(process.env.BROWSER_MCP_PDF_DEFAULT, baseConfig.artifacts.pdf),
            snapshot: parseBoolean(process.env.BROWSER_MCP_SNAPSHOT_DEFAULT, baseConfig.artifacts.snapshot),
            saveSession: parseBoolean(process.env.BROWSER_MCP_SAVE_SESSION_DEFAULT, baseConfig.artifacts.saveSession),
        },
    };
    node_fs_1.default.mkdirSync(merged.browser.outputRoot, { recursive: true });
    node_fs_1.default.mkdirSync(merged.browser.sessionsRoot, { recursive: true });
    return merged;
}
