import type { BrowserContext, BrowserContextOptions, BrowserType, Page, Route } from 'playwright';

export type BrowserName = 'chromium' | 'firefox' | 'webkit';
export type BrowserMode = 'persistent_profile' | 'isolated_session' | 'cdp_attach';
export type JobStatus = 'pending' | 'running' | 'completed' | 'failed';
export type RouteAction = 'abort' | 'continue' | 'fulfill';

export interface BrowserMcpTimeouts {
  actionTimeoutMs?: number;
  navigationTimeoutMs?: number;
}

export interface BrowserMcpArtifacts {
  screenshot?: boolean;
  pdf?: boolean;
  snapshot?: boolean;
  trace?: boolean;
  saveSession?: boolean;
}

export interface BrowserMcpMockRoute {
  pattern: string;
  action: RouteAction;
  status?: number;
  body?: string;
  contentType?: string;
  headers?: Record<string, string>;
}

export interface BrowserMcpNetworkPolicy {
  allowedOrigins?: string[];
  blockedOrigins?: string[];
  mockRoutes?: BrowserMcpMockRoute[];
}

export interface BrowserMcpTarget {
  url?: string;
  metadata?: Record<string, unknown>;
}

export interface BrowserMcpJobRequest {
  jobId: string;
  scenario: string;
  browser?: BrowserName;
  mode?: BrowserMode;
  headless?: boolean;
  keepOpenOnFailure?: boolean;
  target?: BrowserMcpTarget;
  storageStatePath?: string;
  userDataDir?: string;
  cdpEndpoint?: string;
  saveSession?: boolean;
  outputDir?: string;
  networkPolicy?: BrowserMcpNetworkPolicy;
  timeouts?: BrowserMcpTimeouts;
  trace?: boolean;
  artifacts?: BrowserMcpArtifacts;
  steps?: Record<string, unknown>[];
}

export interface BrowserMcpStepResult {
  name: string;
  status: 'ok' | 'error';
  details?: Record<string, unknown>;
}

export interface BrowserMcpJobResponse {
  jobId: string;
  status: JobStatus;
  finalUrl?: string;
  sessionRef?: string;
  artifacts: string[];
  result?: Record<string, unknown>;
  networkSummary?: Record<string, unknown>;
  consoleSummary?: Record<string, unknown>;
  stepResults: BrowserMcpStepResult[];
  error?: string;
}

export interface BrowserServiceConfig {
  host: string;
  port: number;
  logLevel: 'debug' | 'info' | 'warn' | 'error';
}

export interface BrowserMcpProxyConfig {
  enabled: boolean;
  host: string;
  port: number;
  proxyPath: string;
  ssePath: string;
}

export interface BrowserRuntimeConfig {
  browserName: BrowserName;
  chromiumChannel?: string;
  headless: boolean;
  viewport: { width: number; height: number };
  userAgent?: string;
  proxyServer?: string;
  allowedOrigins: string[];
  blockedOrigins: string[];
  actionTimeoutMs: number;
  navigationTimeoutMs: number;
  outputRoot: string;
  sessionsRoot: string;
}

export interface ArtifactDefaults {
  trace: boolean;
  screenshot: boolean;
  pdf: boolean;
  snapshot: boolean;
  saveSession: boolean;
}

export interface AppConfig {
  service: BrowserServiceConfig;
  mcp: BrowserMcpProxyConfig;
  browser: BrowserRuntimeConfig;
  artifacts: ArtifactDefaults;
}

export interface RuntimeHandles {
  browserType: BrowserType;
  context: BrowserContext;
  page: Page;
  close: () => Promise<void>;
}

export interface ScenarioContext {
  job: BrowserMcpJobRequest;
  config: AppConfig;
  context: BrowserContext;
  page: Page;
  outputDir: string;
  recordStep: (name: string, status: 'ok' | 'error', details?: Record<string, unknown>) => void;
  writeArtifact: (name: string, content: string | Buffer) => Promise<string>;
  registerArtifact: (artifactPath: string) => void;
  captureSnapshot: (label: string) => Promise<string | undefined>;
  captureScreenshot: (label: string) => Promise<string | undefined>;
  capturePdf: (label: string) => Promise<string | undefined>;
  saveStorageState: () => Promise<string | undefined>;
}

export type ScenarioHandler = (ctx: ScenarioContext) => Promise<Record<string, unknown> | void>;

export interface RouteHandlerContext {
  route: Route;
  requestUrl: URL;
}

export interface RuntimeContextOptions extends BrowserContextOptions {
  storageState?: string;
}
