import fs from 'node:fs';
import path from 'node:path';

import type { BrowserContext, Page } from 'playwright';

import type {
  AppConfig,
  BrowserMcpJobRequest,
  BrowserMcpStepResult,
  ScenarioContext,
} from '../types';

export function createScenarioContext(args: {
  job: BrowserMcpJobRequest;
  config: AppConfig;
  context: BrowserContext;
  page: Page;
  outputDir: string;
  recordStepResults: BrowserMcpStepResult[];
  writeText: (name: string, content: string) => Promise<string>;
  writeJson: (name: string, content: unknown) => Promise<string>;
  writeBuffer: (name: string, content: Buffer) => Promise<string>;
  registerArtifact: (artifactPath: string) => void;
}): ScenarioContext {
  const {
    job,
    config,
    context,
    page,
    outputDir,
    recordStepResults,
    writeText,
    writeJson,
    writeBuffer,
    registerArtifact,
  } = args;

  return {
    job,
    config,
    context,
    page,
    outputDir,
    recordStep(name, status, details) {
      recordStepResults.push({ name, status, details });
    },
    async writeArtifact(name, content) {
      if (typeof content === 'string') {
        return writeText(name, content);
      }
      return writeBuffer(name, content);
    },
    registerArtifact,
    async captureSnapshot(label) {
      if (job.artifacts?.snapshot === false) {
        return undefined;
      }
      const snapshot = {
        url: page.url(),
        title: await page.title(),
        aria: await page.locator('body').ariaSnapshot().catch(() => null),
      };
      return writeJson(`snapshot-${label}.json`, snapshot);
    },
    async captureScreenshot(label) {
      if (job.artifacts?.screenshot === false) {
        return undefined;
      }
      const target = path.join(outputDir, `screenshot-${label}.png`);
      await page.screenshot({ path: target, fullPage: true });
      registerArtifact(target);
      return target;
    },
    async capturePdf(label) {
      if (job.artifacts?.pdf === false) {
        return undefined;
      }
      if (page.context().browser()?.browserType().name() !== 'chromium') {
        return undefined;
      }
      const target = path.join(outputDir, `page-${label}.pdf`);
      await fs.promises.mkdir(path.dirname(target), { recursive: true });
      await page.pdf({ path: target, printBackground: true });
      registerArtifact(target);
      return target;
    },
    async saveStorageState() {
      if (!job.saveSession && job.artifacts?.saveSession === false) {
        return undefined;
      }
      const target = path.join(outputDir, 'storage-state.json');
      await context.storageState({ path: target });
      registerArtifact(target);
      return target;
    },
  };
}
