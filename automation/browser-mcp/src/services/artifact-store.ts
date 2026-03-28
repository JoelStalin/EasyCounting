import fs from 'node:fs';
import path from 'node:path';

import type { BrowserMcpJobRequest } from '../types';

export interface JobArtifactContext {
  outputDir: string;
  artifacts: string[];
  writeText: (name: string, content: string) => Promise<string>;
  writeJson: (name: string, content: unknown) => Promise<string>;
  writeBuffer: (name: string, content: Buffer) => Promise<string>;
  appendJsonl: (name: string, line: unknown) => Promise<string>;
}

function sanitizeName(value: string): string {
  return value.replace(/[^a-zA-Z0-9._-]+/g, '-');
}

export function createArtifactContext(root: string, job: BrowserMcpJobRequest): JobArtifactContext {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const scenario = sanitizeName(job.scenario);
  const jobId = sanitizeName(job.jobId);
  const outputDir = job.outputDir || path.join(root, `${timestamp}_${jobId}_${scenario}`);
  fs.mkdirSync(outputDir, { recursive: true });
  const artifacts: string[] = [];

  async function writeFile(name: string, content: string | Buffer): Promise<string> {
    const filePath = path.join(outputDir, sanitizeName(name));
    await fs.promises.mkdir(path.dirname(filePath), { recursive: true });
    await fs.promises.writeFile(filePath, content);
    artifacts.push(filePath);
    return filePath;
  }

  return {
    outputDir,
    artifacts,
    writeText: (name, content) => writeFile(name, content),
    writeJson: (name, content) => writeFile(name, JSON.stringify(content, null, 2)),
    writeBuffer: (name, content) => writeFile(name, content),
    appendJsonl: async (name, line) => {
      const filePath = path.join(outputDir, sanitizeName(name));
      await fs.promises.mkdir(path.dirname(filePath), { recursive: true });
      await fs.promises.appendFile(filePath, `${JSON.stringify(line)}\n`, 'utf-8');
      if (!artifacts.includes(filePath)) {
        artifacts.push(filePath);
      }
      return filePath;
    },
  };
}
