import { spawn, type ChildProcessWithoutNullStreams } from 'node:child_process';
import path from 'node:path';

import cors from 'cors';
import express, { type Request, type Response } from 'express';
import { createProxyMiddleware } from 'http-proxy-middleware';

import { loadConfig } from './config/env';
import { JobRunner } from './services/job-runner';
import { createLogger } from './services/logger';
import { deleteSession, listSessions } from './services/session-store';
import type { BrowserMcpJobRequest } from './types';

function mcpCliCommand(): { command: string; args: string[]; shell: boolean } {
  const packageRoot = path.resolve(__dirname, '..');
  const cliPath = path.resolve(
    packageRoot,
    'node_modules',
    '@playwright',
    'mcp',
    'cli.js',
  );
  return {
    command: process.execPath,
    args: [cliPath, '--host', '127.0.0.1'],
    shell: false,
  };
}

export async function createServer() {
  const config = loadConfig();
  const logger = createLogger(config);
  const runner = new JobRunner(config);
  const app = express();
  const packageRoot = path.resolve(__dirname, '..');
  let mcpProcess: ChildProcessWithoutNullStreams | undefined;

  app.disable('x-powered-by');
  app.use(cors());

  if (config.mcp.enabled) {
    const cli = mcpCliCommand();
    mcpProcess = spawn(
      cli.command,
      [...cli.args, '--port', String(config.mcp.port), '--browser', config.browser.browserName],
      {
        env: process.env,
        cwd: packageRoot,
        stdio: 'pipe',
        shell: cli.shell,
      },
    );
    mcpProcess.stdout.on('data', (chunk) => {
      logger.info({ source: 'playwright-mcp', output: String(chunk).trim() }, 'mcp stdout');
    });
    mcpProcess.stderr.on('data', (chunk) => {
      logger.warn({ source: 'playwright-mcp', output: String(chunk).trim() }, 'mcp stderr');
    });
    mcpProcess.on('exit', (code) => {
      logger.warn({ code }, 'playwright-mcp child exited');
    });

    app.use(
      config.mcp.proxyPath,
      createProxyMiddleware({
        target: `http://${config.mcp.host}:${config.mcp.port}`,
        changeOrigin: true,
        ws: true,
        pathRewrite: { [`^${config.mcp.proxyPath}`]: '/mcp' },
      }),
    );
    app.use(
      config.mcp.ssePath,
      createProxyMiddleware({
        target: `http://${config.mcp.host}:${config.mcp.port}`,
        changeOrigin: true,
        ws: true,
      }),
    );
  }

  app.use(express.json({ limit: '5mb' }));

  app.get('/healthz', (_req, res) => {
    res.json({
      ok: true,
      mcpProxyEnabled: config.mcp.enabled,
    });
  });

  app.post('/api/v1/jobs/run-sync', async (req: Request, res: Response) => {
    const job = req.body as BrowserMcpJobRequest;
    const response = await runner.runSync(job);
    const statusCode = response.status === 'failed' ? 500 : 200;
    res.status(statusCode).json(response);
  });

  app.post('/api/v1/jobs', (req: Request, res: Response) => {
    const job = req.body as BrowserMcpJobRequest;
    runner.enqueue(job);
    res.status(202).json({ jobId: job.jobId, status: 'pending' });
  });

  app.get('/api/v1/jobs/:jobId', (req: Request, res: Response) => {
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

  app.get('/api/v1/jobs/:jobId/runtime', (req: Request, res: Response) => {
    const jobId = Array.isArray(req.params.jobId) ? req.params.jobId[0] : req.params.jobId;
    res.json(runner.getRetainedRuntime(jobId));
  });

  app.delete('/api/v1/jobs/:jobId/runtime', async (req: Request, res: Response) => {
    const jobId = Array.isArray(req.params.jobId) ? req.params.jobId[0] : req.params.jobId;
    const released = await runner.releaseRetainedRuntime(jobId);
    res.json({ released });
  });

  app.get('/api/v1/jobs/:jobId/events', (req: Request, res: Response) => {
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

    const send = (event: string, payload: unknown) => {
      res.write(`event: ${event}\n`);
      res.write(`data: ${JSON.stringify(payload)}\n\n`);
    };

    send('status', { jobId: job.request.jobId, status: job.status });
    if (job.response) {
      send(job.status, job.response);
      res.end();
      return;
    }

    const onComplete = (payload: unknown) => {
      send('completed', payload);
      res.end();
    };
    const onFailed = (payload: unknown) => {
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
    const sessions = await listSessions(config.browser.sessionsRoot);
    res.json({ sessions });
  });

  app.delete('/api/v1/sessions/:sessionRef', async (req, res) => {
    const deleted = await deleteSession(config.browser.sessionsRoot, req.params.sessionRef);
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
