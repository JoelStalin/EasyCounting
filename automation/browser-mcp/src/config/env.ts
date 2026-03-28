import fs from 'node:fs';
import path from 'node:path';
import { z } from 'zod';

import type { AppConfig } from '../types';

const configSchema = z.object({
  service: z.object({
    host: z.string().default('0.0.0.0'),
    port: z.number().int().positive().default(8930),
    logLevel: z.enum(['debug', 'info', 'warn', 'error']).default('info'),
  }),
  mcp: z.object({
    enabled: z.boolean().default(true),
    host: z.string().default('127.0.0.1'),
    port: z.number().int().positive().default(8931),
    proxyPath: z.string().default('/mcp'),
    ssePath: z.string().default('/sse'),
  }),
  browser: z.object({
    browserName: z.enum(['chromium', 'firefox', 'webkit']).default('chromium'),
    chromiumChannel: z.string().optional().default(''),
    headless: z.boolean().default(true),
    viewport: z.object({
      width: z.number().int().positive().default(1440),
      height: z.number().int().positive().default(900),
    }),
    userAgent: z.string().optional().default(''),
    proxyServer: z.string().optional().default(''),
    allowedOrigins: z.array(z.string()).default([]),
    blockedOrigins: z.array(z.string()).default([]),
    actionTimeoutMs: z.number().int().nonnegative().default(10000),
    navigationTimeoutMs: z.number().int().nonnegative().default(60000),
    outputRoot: z.string().default('../../tests/artifacts/browser-mcp'),
    sessionsRoot: z.string().default('../../tests/artifacts/browser-mcp/sessions'),
  }),
  artifacts: z.object({
    trace: z.boolean().default(true),
    screenshot: z.boolean().default(true),
    pdf: z.boolean().default(false),
    snapshot: z.boolean().default(true),
    saveSession: z.boolean().default(false),
  }),
});

function parseBoolean(value: string | undefined, fallback: boolean): boolean {
  if (value === undefined || value === '') {
    return fallback;
  }
  return ['1', 'true', 'yes', 'on'].includes(value.toLowerCase());
}

function parseCsv(value: string | undefined): string[] {
  if (!value) {
    return [];
  }
  return value
    .split(/[;,]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function resolveRoot(baseDir: string, relativeOrAbsolute: string): string {
  return path.isAbsolute(relativeOrAbsolute)
    ? relativeOrAbsolute
    : path.resolve(baseDir, relativeOrAbsolute);
}

export function loadConfig(): AppConfig {
  const repoRoot = path.resolve(__dirname, '..', '..');
  const configPath =
    process.env.BROWSER_MCP_CONFIG_PATH ||
    path.resolve(repoRoot, 'config', 'browser-mcp.config.json');
  const baseConfig = configSchema.parse(JSON.parse(fs.readFileSync(configPath, 'utf-8')));

  const merged: AppConfig = {
    service: {
      host: process.env.BROWSER_MCP_SERVICE_HOST || baseConfig.service.host,
      port: Number(process.env.BROWSER_MCP_SERVICE_PORT || baseConfig.service.port),
      logLevel:
        (process.env.BROWSER_MCP_LOG_LEVEL as AppConfig['service']['logLevel'] | undefined) ||
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
      browserName:
        (process.env.BROWSER_MCP_DEFAULT_BROWSER as AppConfig['browser']['browserName'] | undefined) ||
        baseConfig.browser.browserName,
      chromiumChannel: process.env.BROWSER_MCP_CHROMIUM_CHANNEL || baseConfig.browser.chromiumChannel,
      headless: parseBoolean(
        process.env.BROWSER_MCP_DEFAULT_HEADLESS,
        baseConfig.browser.headless,
      ),
      viewport: {
        width: Number(process.env.BROWSER_MCP_VIEWPORT_WIDTH || baseConfig.browser.viewport.width),
        height: Number(
          process.env.BROWSER_MCP_VIEWPORT_HEIGHT || baseConfig.browser.viewport.height,
        ),
      },
      userAgent: process.env.BROWSER_MCP_USER_AGENT || baseConfig.browser.userAgent,
      proxyServer: process.env.BROWSER_MCP_PROXY_SERVER || baseConfig.browser.proxyServer,
      allowedOrigins:
        parseCsv(process.env.BROWSER_MCP_ALLOWED_ORIGINS).length > 0
          ? parseCsv(process.env.BROWSER_MCP_ALLOWED_ORIGINS)
          : baseConfig.browser.allowedOrigins,
      blockedOrigins:
        parseCsv(process.env.BROWSER_MCP_BLOCKED_ORIGINS).length > 0
          ? parseCsv(process.env.BROWSER_MCP_BLOCKED_ORIGINS)
          : baseConfig.browser.blockedOrigins,
      actionTimeoutMs: Number(
        process.env.BROWSER_MCP_ACTION_TIMEOUT_MS || baseConfig.browser.actionTimeoutMs,
      ),
      navigationTimeoutMs: Number(
        process.env.BROWSER_MCP_NAVIGATION_TIMEOUT_MS || baseConfig.browser.navigationTimeoutMs,
      ),
      outputRoot: resolveRoot(
        repoRoot,
        process.env.BROWSER_MCP_OUTPUT_ROOT || baseConfig.browser.outputRoot,
      ),
      sessionsRoot: resolveRoot(
        repoRoot,
        process.env.BROWSER_MCP_SESSIONS_ROOT || baseConfig.browser.sessionsRoot,
      ),
    },
    artifacts: {
      trace: parseBoolean(process.env.BROWSER_MCP_TRACE_DEFAULT, baseConfig.artifacts.trace),
      screenshot: parseBoolean(
        process.env.BROWSER_MCP_SCREENSHOT_DEFAULT,
        baseConfig.artifacts.screenshot,
      ),
      pdf: parseBoolean(process.env.BROWSER_MCP_PDF_DEFAULT, baseConfig.artifacts.pdf),
      snapshot: parseBoolean(process.env.BROWSER_MCP_SNAPSHOT_DEFAULT, baseConfig.artifacts.snapshot),
      saveSession: parseBoolean(
        process.env.BROWSER_MCP_SAVE_SESSION_DEFAULT,
        baseConfig.artifacts.saveSession,
      ),
    },
  };

  fs.mkdirSync(merged.browser.outputRoot, { recursive: true });
  fs.mkdirSync(merged.browser.sessionsRoot, { recursive: true });
  return merged;
}
