import path from 'node:path';

import {
  chromium,
  firefox,
  webkit,
  type BrowserContext,
  type BrowserType,
  type ConsoleMessage,
  type Page,
} from 'playwright';

import { applyNetworkPolicy } from '../services/network-policy';
import type {
  AppConfig,
  BrowserMcpJobRequest,
  BrowserMcpJobResponse,
  BrowserMcpStepResult,
  RuntimeHandles,
} from '../types';

function getBrowserType(name: BrowserMcpJobRequest['browser'] | undefined): BrowserType {
  switch (name) {
    case 'firefox':
      return firefox;
    case 'webkit':
      return webkit;
    case 'chromium':
    default:
      return chromium;
  }
}

export interface RuntimeTelemetry {
  stepResults: BrowserMcpStepResult[];
  consoleMessages: Record<string, number>;
  networkRequests: number;
  finalUrl?: string;
}

export interface RuntimeBootstrap {
  handles: RuntimeHandles;
  telemetry: RuntimeTelemetry;
  bindTelemetry: (context: BrowserContext, page: Page) => void;
}

export interface RuntimeEventSinks {
  onConsoleEntry?: (entry: Record<string, unknown>) => void;
  onNetworkEntry?: (entry: Record<string, unknown>) => void;
}

export async function createRuntime(
  job: BrowserMcpJobRequest,
  config: AppConfig,
  sinks: RuntimeEventSinks = {},
): Promise<RuntimeBootstrap> {
  const browserType = getBrowserType(job.browser || config.browser.browserName);
  const stepResults: BrowserMcpStepResult[] = [];
  const consoleMessages: Record<string, number> = {};
  let networkRequests = 0;
  let contextTelemetryBound = false;
  const boundPages = new WeakSet<Page>();

  let context: BrowserContext;
  let page: Page;
  let close: () => Promise<void>;

  const headless = job.headless ?? config.browser.headless;
  const viewport = config.browser.viewport;
  const actionTimeout = job.timeouts?.actionTimeoutMs || config.browser.actionTimeoutMs;
  const navigationTimeout =
    job.timeouts?.navigationTimeoutMs || config.browser.navigationTimeoutMs;
  const chromiumChannel =
    browserType.name() === 'chromium' && config.browser.chromiumChannel
      ? config.browser.chromiumChannel
      : undefined;

  if (job.mode === 'cdp_attach') {
    if (!job.cdpEndpoint) {
      throw new Error('cdp_attach mode requires cdpEndpoint');
    }
    if (browserType.name() !== 'chromium') {
      throw new Error('cdp_attach mode is only supported with chromium');
    }
    const connected = await chromium.connectOverCDP(job.cdpEndpoint);
    context =
      connected.contexts()[0] || (await connected.newContext({ viewport, acceptDownloads: true }));
    page = context.pages()[0] || (await context.newPage());
    close = async () => {
      await connected.close();
    };
  } else if (job.mode === 'persistent_profile') {
    const userDataDir =
      job.userDataDir || path.join(config.browser.sessionsRoot, `${job.jobId}-profile`);
    context = await browserType.launchPersistentContext(userDataDir, {
      headless,
      channel: chromiumChannel,
      viewport,
      userAgent: config.browser.userAgent || undefined,
      proxy: config.browser.proxyServer ? { server: config.browser.proxyServer } : undefined,
      acceptDownloads: true,
    });
    page = context.pages()[0] || (await context.newPage());
    close = async () => {
      await context.close();
    };
  } else {
    const browser = await browserType.launch({
      headless,
      channel: chromiumChannel,
      proxy: config.browser.proxyServer ? { server: config.browser.proxyServer } : undefined,
    });
    context = await browser.newContext({
      viewport,
      userAgent: config.browser.userAgent || undefined,
      storageState: job.storageStatePath || undefined,
      acceptDownloads: true,
    });
    page = await context.newPage();
    close = async () => {
      await context.close();
      await browser.close();
    };
  }

  context.setDefaultTimeout(actionTimeout);
  context.setDefaultNavigationTimeout(navigationTimeout);
  page.setDefaultTimeout(actionTimeout);
  page.setDefaultNavigationTimeout(navigationTimeout);
  await applyNetworkPolicy(context, {
    allowedOrigins: job.networkPolicy?.allowedOrigins || config.browser.allowedOrigins,
    blockedOrigins: job.networkPolicy?.blockedOrigins || config.browser.blockedOrigins,
    mockRoutes: job.networkPolicy?.mockRoutes || [],
  });

  const bindTelemetry = (boundContext: BrowserContext, boundPage: Page) => {
    if (!contextTelemetryBound) {
      contextTelemetryBound = true;
      boundContext.on('request', (request) => {
        const requestUrl = request.url();
        networkRequests += 1;
        telemetry.networkRequests = networkRequests;
        sinks.onNetworkEntry?.({
          event: 'request',
          url: requestUrl,
          method: request.method(),
          resourceType: request.resourceType(),
        });
      });
      boundContext.on('response', (response) => {
        sinks.onNetworkEntry?.({
          event: 'response',
          url: response.url(),
          status: response.status(),
        });
      });
      boundContext.on('requestfailed', (request) => {
        sinks.onNetworkEntry?.({
          event: 'requestfailed',
          url: request.url(),
          method: request.method(),
          resourceType: request.resourceType(),
          failureText: request.failure()?.errorText || '',
        });
      });
      boundContext.on('page', (newPage) => {
        newPage.setDefaultTimeout(actionTimeout);
        newPage.setDefaultNavigationTimeout(navigationTimeout);
        bindTelemetry(boundContext, newPage);
      });
    }

    if (boundPages.has(boundPage)) {
      return;
    }
    boundPages.add(boundPage);
    boundPage.on('console', (message: ConsoleMessage) => {
      const type = message.type();
      consoleMessages[type] = (consoleMessages[type] || 0) + 1;
      sinks.onConsoleEntry?.({
        type,
        text: message.text(),
        location: message.location(),
      });
    });
    boundPage.on('framenavigated', (frame) => {
      if (frame === boundPage.mainFrame()) {
        telemetry.finalUrl = frame.url();
      }
    });
  };

  const telemetry: RuntimeTelemetry = {
    stepResults,
    consoleMessages,
    networkRequests,
  };
  bindTelemetry(context, page);

  return {
    handles: {
      browserType,
      context,
      page,
      close,
    },
    telemetry,
    bindTelemetry,
  };
}

export function finalizeResponse(
  base: Omit<BrowserMcpJobResponse, 'networkSummary' | 'consoleSummary' | 'stepResults'>,
  telemetry: RuntimeTelemetry,
): BrowserMcpJobResponse {
  return {
    ...base,
    finalUrl: base.finalUrl || telemetry.finalUrl,
    networkSummary: {
      requests: telemetry.networkRequests,
    },
    consoleSummary: telemetry.consoleMessages,
    stepResults: telemetry.stepResults,
  };
}
