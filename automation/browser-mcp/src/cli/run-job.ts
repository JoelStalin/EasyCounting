import fs from 'node:fs';

import { loadConfig } from '../config/env';
import { JobRunner } from '../services/job-runner';
import type { BrowserMcpJobRequest } from '../types';

async function main() {
  const raw = fs.readFileSync(0, 'utf-8').trim();
  if (!raw) {
    throw new Error('Expected JSON job payload on stdin');
  }
  const job = JSON.parse(raw) as BrowserMcpJobRequest;
  const runner = new JobRunner(loadConfig());
  const response = await runner.runSync(job);
  process.stdout.write(`${JSON.stringify(response)}\n`);
}

void main();
