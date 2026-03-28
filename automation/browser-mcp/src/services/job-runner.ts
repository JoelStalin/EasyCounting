import { EventEmitter } from 'node:events';

import { createArtifactContext } from './artifact-store';
import { saveSessionState } from './session-store';
import { createScenarioContext } from '../scenarios/context';
import { getScenario } from '../scenarios';
import { createRuntime, finalizeResponse } from '../runtime/browser-runtime';
import type {
  AppConfig,
  BrowserMcpJobRequest,
  BrowserMcpJobResponse,
  JobStatus,
  RuntimeHandles,
} from '../types';

interface StoredJob {
  request: BrowserMcpJobRequest;
  status: JobStatus;
  response?: BrowserMcpJobResponse;
  events: EventEmitter;
}

interface RetainedRuntime {
  handles: RuntimeHandles;
  retainedAt: string;
}

export class JobRunner {
  private readonly jobs = new Map<string, StoredJob>();
  private readonly retainedRuntimes = new Map<string, RetainedRuntime>();

  constructor(private readonly config: AppConfig) {}

  private normalizeJob(job: BrowserMcpJobRequest): BrowserMcpJobRequest {
    return {
      ...job,
      browser: job.browser || this.config.browser.browserName,
      mode: job.mode || 'isolated_session',
      target: {
        metadata: {},
        ...(job.target || {}),
      },
      artifacts: {
        trace: this.config.artifacts.trace,
        screenshot: this.config.artifacts.screenshot,
        pdf: this.config.artifacts.pdf,
        snapshot: this.config.artifacts.snapshot,
        saveSession: this.config.artifacts.saveSession,
        ...(job.artifacts || {}),
      },
      networkPolicy: {
        allowedOrigins: [...this.config.browser.allowedOrigins],
        blockedOrigins: [...this.config.browser.blockedOrigins],
        mockRoutes: [],
        ...(job.networkPolicy || {}),
      },
      timeouts: {
        actionTimeoutMs: this.config.browser.actionTimeoutMs,
        navigationTimeoutMs: this.config.browser.navigationTimeoutMs,
        ...(job.timeouts || {}),
      },
      steps: job.steps || [],
    };
  }

  async runSync(job: BrowserMcpJobRequest): Promise<BrowserMcpJobResponse> {
    const normalizedJob = this.normalizeJob(job);
    const events = new EventEmitter();
    this.jobs.set(normalizedJob.jobId, {
      request: normalizedJob,
      status: 'running',
      events,
    });

    const artifactContext = createArtifactContext(this.config.browser.outputRoot, normalizedJob);
    const pendingArtifactWrites: Promise<unknown>[] = [];
    const queueArtifactWrite = (promise: Promise<unknown>) => {
      pendingArtifactWrites.push(promise.catch(() => null));
    };
    let runtime: Awaited<ReturnType<typeof createRuntime>> | null = null;
    let sessionRef: string | undefined;
    let tracingStarted = false;
    let retainRuntime = false;

    try {
      runtime = await createRuntime(normalizedJob, this.config, {
        onConsoleEntry: (entry) => {
          queueArtifactWrite(artifactContext.appendJsonl('console.jsonl', entry));
        },
        onNetworkEntry: (entry) => {
          queueArtifactWrite(artifactContext.appendJsonl('network.jsonl', entry));
        },
      });

      if (normalizedJob.trace || normalizedJob.artifacts?.trace) {
        await runtime.handles.context.tracing.start({ screenshots: true, snapshots: true });
        tracingStarted = true;
      }

      const scenario = getScenario(normalizedJob.scenario);
      const ctx = createScenarioContext({
        job: normalizedJob,
        config: this.config,
        context: runtime.handles.context,
        page: runtime.handles.page,
        outputDir: artifactContext.outputDir,
        recordStepResults: runtime.telemetry.stepResults,
        writeText: artifactContext.writeText,
        writeJson: artifactContext.writeJson,
        writeBuffer: artifactContext.writeBuffer,
        registerArtifact: (artifactPath) => {
          if (!artifactContext.artifacts.includes(artifactPath)) {
            artifactContext.artifacts.push(artifactPath);
          }
        },
      });

      const scenarioResult = await scenario(ctx);

      if (normalizedJob.saveSession || normalizedJob.artifacts?.saveSession) {
        const storageState = await runtime.handles.context.storageState();
        const saved = await saveSessionState(
          this.config.browser.sessionsRoot,
          normalizedJob.jobId,
          storageState,
        );
        sessionRef = saved.sessionRef;
        artifactContext.artifacts.push(saved.storageStatePath);
      }

      if (tracingStarted) {
        const tracePath = await artifactContext.writeBuffer(
          'trace-placeholder.txt',
          Buffer.from('Trace path written after context stop.'),
        );
        const finalTracePath = tracePath.replace('trace-placeholder.txt', 'trace.zip');
        await runtime.handles.context.tracing.stop({ path: finalTracePath });
        tracingStarted = false;
        artifactContext.artifacts.splice(artifactContext.artifacts.indexOf(tracePath), 1, finalTracePath);
      }

      const retainOnSuccess = Boolean(
        normalizedJob.keepOpenOnSuccess &&
          normalizedJob.mode === 'persistent_profile' &&
          normalizedJob.headless === false,
      );
      if (retainOnSuccess) {
        this.retainedRuntimes.set(normalizedJob.jobId, {
          handles: runtime.handles,
          retainedAt: new Date().toISOString(),
        });
        retainRuntime = true;
      }

      await artifactContext.writeJson('run.json', {
        job: normalizedJob,
        scenarioResult,
        telemetry: runtime.telemetry,
      });
      await Promise.allSettled(pendingArtifactWrites);

      const response = finalizeResponse(
        {
          jobId: normalizedJob.jobId,
          status: 'completed',
          finalUrl: runtime.handles.page.url(),
          sessionRef,
          artifacts: artifactContext.artifacts,
          result: {
            ...(((scenarioResult as Record<string, unknown> | undefined) || {}) as Record<string, unknown>),
            browserRetained: retainOnSuccess,
          },
        },
        runtime.telemetry,
      );
      this.jobs.set(normalizedJob.jobId, {
        request: normalizedJob,
        status: 'completed',
        response,
        events,
      });
      events.emit('completed', response);
      return response;
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      const failureTelemetry = runtime?.telemetry ?? {
        stepResults: [],
        consoleMessages: {},
        networkRequests: 0,
      };
      retainRuntime = Boolean(
        normalizedJob.keepOpenOnFailure &&
          normalizedJob.mode === 'persistent_profile' &&
          normalizedJob.headless === false,
      );
      if (retainRuntime && runtime) {
        this.retainedRuntimes.set(normalizedJob.jobId, {
          handles: runtime.handles,
          retainedAt: new Date().toISOString(),
        });
      }
      const response = finalizeResponse(
        {
          jobId: normalizedJob.jobId,
          status: 'failed',
          finalUrl: runtime?.handles.page.url(),
          sessionRef,
          artifacts: artifactContext.artifacts,
          result: {
            browserRetained: retainRuntime,
            userDataDir: normalizedJob.userDataDir,
          },
          error: message,
        },
        failureTelemetry,
      );
      await artifactContext.writeJson('run.json', {
        job: normalizedJob,
        error: message,
        browserRetained: retainRuntime,
        telemetry: failureTelemetry,
      });
      await Promise.allSettled(pendingArtifactWrites);
      this.jobs.set(normalizedJob.jobId, {
        request: normalizedJob,
        status: 'failed',
        response,
        events,
      });
      events.emit('failed', response);
      return response;
    } finally {
      if (tracingStarted && runtime) {
        try {
          const finalTracePath = `${artifactContext.outputDir}/trace.zip`;
          await runtime.handles.context.tracing.stop({ path: finalTracePath });
          artifactContext.artifacts.push(finalTracePath);
        } catch {
          // no-op: keep the original job error
        }
      }
      if (runtime && !retainRuntime) {
        await runtime.handles.close();
      }
    }
  }

  enqueue(job: BrowserMcpJobRequest): StoredJob {
    const normalizedJob = this.normalizeJob(job);
    const events = new EventEmitter();
    const stored: StoredJob = {
      request: normalizedJob,
      status: 'pending',
      events,
    };
    this.jobs.set(normalizedJob.jobId, stored);
    void this.runSync(normalizedJob).then((response) => {
      const existing = this.jobs.get(normalizedJob.jobId);
      if (!existing) {
        return;
      }
      this.jobs.set(normalizedJob.jobId, {
        ...existing,
        status: response.status,
        response,
      });
    });
    return stored;
  }

  get(jobId: string): StoredJob | undefined {
    return this.jobs.get(jobId);
  }

  getRetainedRuntime(jobId: string): { retained: boolean; retainedAt?: string; currentUrl?: string } {
    const retained = this.retainedRuntimes.get(jobId);
    if (!retained) {
      return { retained: false };
    }
    return {
      retained: true,
      retainedAt: retained.retainedAt,
      currentUrl: retained.handles.page.url(),
    };
  }

  async releaseRetainedRuntime(jobId: string): Promise<boolean> {
    const retained = this.retainedRuntimes.get(jobId);
    if (!retained) {
      return false;
    }
    await retained.handles.close();
    this.retainedRuntimes.delete(jobId);
    return true;
  }
}
