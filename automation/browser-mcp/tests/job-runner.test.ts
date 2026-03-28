import assert from 'node:assert/strict';
import http from 'node:http';
import { after, before, test } from 'node:test';
import fs from 'node:fs';
import path from 'node:path';

import { loadConfig } from '../src/config/env';
import { JobRunner } from '../src/services/job-runner';
import type { BrowserMcpJobRequest } from '../src/types';

const testRoot = path.resolve(__dirname, 'artifacts');
let server: http.Server;
let baseUrl = '';

before(async () => {
  server = http.createServer((req, res) => {
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.end('<html><head><title>Smoke</title></head><body><h1>Browser MCP</h1></body></html>');
  });
  await new Promise<void>((resolve) => {
    server.listen(0, '127.0.0.1', () => resolve());
  });
  const address = server.address();
  if (!address || typeof address === 'string') {
    throw new Error('Could not resolve test server address');
  }
  baseUrl = `http://127.0.0.1:${address.port}`;
  process.env.BROWSER_MCP_OUTPUT_ROOT = testRoot;
  process.env.BROWSER_MCP_SESSIONS_ROOT = path.join(testRoot, 'sessions');
  process.env.BROWSER_MCP_DEFAULT_HEADLESS = 'true';
});

after(async () => {
  await new Promise<void>((resolve, reject) => {
    server.close((error) => (error ? reject(error) : resolve()));
  });
});

test('runSync executes open-url-extract and writes run.json', async () => {
  const config = loadConfig();
  const runner = new JobRunner(config);
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
  } satisfies BrowserMcpJobRequest);

  assert.equal(response.status, 'completed');
  const runArtifact = response.artifacts.find((item) => item.endsWith('run.json'));
  assert.ok(runArtifact);
  assert.equal(fs.existsSync(runArtifact!), true);
});
