import path from 'node:path';

import type { Locator, Page } from 'playwright';

import type { ScenarioContext } from '../../types';

const DEFAULT_OFV_URL = 'https://dgii.gov.do/OFV/home.aspx';
const DEFAULT_FE_ACCESS_URL = 'https://dgii.gov.do/OFV/FacturaElectronica/FE_Facturador_Electronico.aspx';
const DEFAULT_POSTULACION_FALLBACK_URLS = [
  'https://ecf.dgii.gov.do/certecf/portalcertificacion/Postulacion/Registrado',
  'https://ecf.dgii.gov.do/CerteCF/PortalCertificacion/Postulacion/Registrado',
  'https://ecf.dgii.gov.do/certecf/portalcertificacion',
  'https://ecf.dgii.gov.do/CerteCF/PortalCertificacion',
];

type AuthStrategy = 'session_reuse' | 'portal_credentials' | 'manual_seed';
type PortalAuthResult =
  | 'not_attempted'
  | 'authenticated'
  | 'invalid_credentials'
  | 'login_required'
  | 'manual_seed_timeout'
  | 'unknown';

export interface DgiiPortalCredentials {
  username: string;
  password: string;
  portalUsername: string;
  portalPassword: string;
}

export interface PortalAuthTrace {
  strategy: AuthStrategy | 'portal_state_probe' | 'view_postulacion';
  status: 'ok' | 'error';
  currentUrl: string;
  pageState: string;
  portalAuthResult: PortalAuthResult;
  details?: Record<string, unknown>;
}

export interface PostulacionOpenResult {
  page: Page;
  authFlow: PortalAuthTrace[];
  portalAuthResult: PortalAuthResult;
}

function getString(metadata: Record<string, unknown>, key: string, fallback = ''): string {
  const value = metadata[key];
  return typeof value === 'string' && value.trim() ? value.trim() : fallback;
}

function normalizeApiBase(raw: string): string {
  const candidate = raw.trim().replace(/\/+$/, '');
  if (!candidate) {
    return '';
  }
  const withScheme = /^https?:\/\//i.test(candidate) ? candidate : `https://${candidate}`;
  try {
    const parsed = new URL(withScheme);
    return `${parsed.host}`;
  } catch {
    return candidate.replace(/^https?:\/\//i, '').replace(/\/+$/, '');
  }
}

function parseAuthStrategies(ctx: ScenarioContext): AuthStrategy[] {
  const raw = ctx.job.target?.metadata?.authStrategies;
  const defaultStrategies: AuthStrategy[] = ['session_reuse', 'portal_credentials', 'manual_seed'];
  const source = Array.isArray(raw)
    ? raw
    : typeof raw === 'string'
      ? raw.split(',')
      : defaultStrategies;
  const normalized = source
    .map((item) => String(item).trim().toLowerCase())
    .filter((item): item is AuthStrategy =>
      item === 'session_reuse' || item === 'portal_credentials' || item === 'manual_seed',
    );
  return normalized.length > 0 ? normalized : defaultStrategies;
}

function manualSeedTimeoutMs(ctx: ScenarioContext): number {
  const raw = Number.parseInt(String(ctx.job.target?.metadata?.manualSeedTimeoutSeconds ?? '60'), 10);
  if (!Number.isFinite(raw)) {
    return 60_000;
  }
  return Math.min(Math.max(raw, 10), 900) * 1000;
}

async function firstExisting(page: Page, selectors: string[]): Promise<Locator | null> {
  for (const selector of selectors) {
    const locator = page.locator(selector).first();
    if ((await locator.count()) > 0) {
      return locator;
    }
  }
  return null;
}

async function bodyText(page: Page): Promise<string> {
  try {
    return ((await page.locator('body').innerText()) || '').toLowerCase();
  } catch {
    return '';
  }
}

async function classifyPageState(page: Page): Promise<string> {
  const current = page.url().toLowerCase();
  const body = await bodyText(page);
  if (
    current.includes('/postulacion/') ||
    body.includes('archivo de postulacion firmado') ||
    body.includes('formulario de postulacion')
  ) {
    return 'postulacion_open';
  }
  if (current.includes('portalcertificacion/login')) {
    return 'portal_login';
  }
  if (current.includes('/ofv/home.aspx')) {
    return 'ofv_home';
  }
  if (current.includes('portalcertificacion')) {
    return 'portal_home';
  }
  return 'unknown';
}

async function classifyPortalAuthResult(page: Page): Promise<PortalAuthResult> {
  const state = await classifyPageState(page);
  if (state === 'postulacion_open') {
    return 'authenticated';
  }
  if (state !== 'portal_login') {
    return 'unknown';
  }
  const body = await bodyText(page);
  if (body.includes('autenticación fallida') || body.includes('credenciales proporcionadas no son válidas')) {
    return 'invalid_credentials';
  }
  return 'login_required';
}

function recordAuthStep(
  ctx: ScenarioContext,
  authFlow: PortalAuthTrace[],
  step: PortalAuthTrace,
): void {
  authFlow.push(step);
  ctx.recordStep(step.strategy, step.status, {
    currentUrl: step.currentUrl,
    pageState: step.pageState,
    portalAuthResult: step.portalAuthResult,
    ...(step.details || {}),
  });
}

export async function capturePageState(
  ctx: ScenarioContext,
  page: Page,
  label: string,
): Promise<void> {
  const title = await page.title().catch(() => '');
  const html = await page.content().catch(() => '');
  const aria = await page.locator('body').ariaSnapshot().catch(() => null);
  await ctx.writeArtifact(`${label}.html`, html);
  await ctx.writeArtifact(
    `${label}.json`,
    JSON.stringify(
      {
        title,
        url: page.url(),
        aria,
        bodyPreview: (await bodyText(page)).slice(0, 6000),
      },
      null,
      2,
    ),
  );
  const screenshotPath = path.join(ctx.outputDir, `${label}.png`);
  await page.screenshot({ path: screenshotPath, fullPage: true });
  ctx.registerArtifact(screenshotPath);
}

export function loadCredentials(ctx: ScenarioContext): DgiiPortalCredentials {
  const metadata = ctx.job.target?.metadata || {};
  const username = getString(metadata, 'username');
  const password = getString(metadata, 'password');
  let portalUsername = getString(metadata, 'portalUsername');
  let portalPassword = getString(metadata, 'portalPassword');
  const fallbackPolicy = getString(metadata, 'portalCredentialFallback', 'none').toLowerCase();
  if (fallbackPolicy === 'ofv') {
    portalUsername = portalUsername || username;
    portalPassword = portalPassword || password;
  }
  if (!username || !password) {
    throw new Error('DGII scenario requires target.metadata.username and target.metadata.password');
  }
  return { username, password, portalUsername, portalPassword };
}

export async function isPostulacionOpen(page: Page): Promise<boolean> {
  return (await classifyPageState(page)) === 'postulacion_open';
}

export async function loginCertPortalIfNeeded(
  ctx: ScenarioContext,
  page: Page,
  credentials: DgiiPortalCredentials,
  authFlow: PortalAuthTrace[],
): Promise<PortalAuthResult> {
  const state = await classifyPageState(page);
  if (state !== 'portal_login') {
    return 'not_attempted';
  }

  const userLocator = await firstExisting(page, [
    '#inputUserName',
    '#inputRnc',
    '#username',
    '#inputUsuario',
    'input[name="username"]',
  ]);
  const passLocator = await firstExisting(page, [
    '#inputClave',
    '#inputPassword',
    '#password',
    'input[name="password"]',
  ]);
  const submitLocator = await firstExisting(page, [
    '#btningresar',
    '#btnIngresar',
    '#btnLogin',
    'button[type="submit"]',
  ]);

  if (!userLocator || !passLocator || !submitLocator) {
    recordAuthStep(ctx, authFlow, {
      strategy: 'portal_credentials',
      status: 'error',
      currentUrl: page.url(),
      pageState: state,
      portalAuthResult: 'unknown',
      details: { reason: 'login_form_not_detected' },
    });
    return 'unknown';
  }

  if (!credentials.portalUsername || !credentials.portalPassword) {
    recordAuthStep(ctx, authFlow, {
      strategy: 'portal_credentials',
      status: 'error',
      currentUrl: page.url(),
      pageState: state,
      portalAuthResult: 'login_required',
      details: { reason: 'missing_explicit_portal_credentials' },
    });
    return 'login_required';
  }

  await userLocator.fill(credentials.portalUsername);
  await passLocator.fill(credentials.portalPassword);
  type SignInPostCapture = {
    posted: boolean;
    statusCode?: number;
    location?: string;
    setCookiePresent?: boolean;
  };
  const waitForSignInPost = () =>
    page
      .waitForResponse(
        (response) =>
          response.request().method().toUpperCase() === 'POST' &&
          response.url().toLowerCase().includes('/portalcertificacion/login/signin'),
        { timeout: 8000 },
      )
      .then<SignInPostCapture>((response) => {
        const headers = response.headers();
        return {
          posted: true,
          statusCode: response.status(),
          location: headers.location || '',
          setCookiePresent: Boolean(headers['set-cookie']),
        };
      })
      .catch<SignInPostCapture>(() => ({ posted: false }));

  let signInCapture: SignInPostCapture = { posted: false };
  const postWaitPromise = waitForSignInPost();
  await submitLocator.click({ force: true }).catch(() => null);
  signInCapture = await postWaitPromise;

  if (!signInCapture.posted) {
    const fallbackPostWaitPromise = waitForSignInPost();
    await page.evaluate(() => {
      const form = document.querySelector('#formularioLogin') as HTMLFormElement | null;
      if (form) {
        form.submit();
      }
    });
    signInCapture = await fallbackPostWaitPromise;
  }

  await page.waitForTimeout(4000);
  await page.waitForLoadState('domcontentloaded').catch(() => null);
  await capturePageState(ctx, page, 'postulacion_after_cert_login');
  let result = await classifyPortalAuthResult(page);
  if (result === 'login_required') {
    await page.waitForTimeout(2000);
    result = await classifyPortalAuthResult(page);
  }
  recordAuthStep(ctx, authFlow, {
    strategy: 'portal_credentials',
    status: result === 'authenticated' ? 'ok' : 'error',
    currentUrl: page.url(),
    pageState: await classifyPageState(page),
    portalAuthResult: result,
    details: {
      postedToSignIn: signInCapture.posted,
      signInStatusCode: signInCapture.statusCode ?? null,
      signInLocation: signInCapture.location ?? null,
      signInSetCookiePresent: signInCapture.setCookiePresent ?? false,
    },
  });
  return result;
}

export async function ensureOfvAuthenticated(
  ctx: ScenarioContext,
  page: Page,
  credentials: DgiiPortalCredentials,
): Promise<void> {
  if (await isPostulacionOpen(page)) {
    ctx.recordStep('ofv_session_reuse', 'ok', {
      currentUrl: page.url(),
      pageState: 'postulacion_open',
    });
    return;
  }

  await page.goto(DEFAULT_OFV_URL, { waitUntil: 'domcontentloaded' });
  await capturePageState(ctx, page, 'ofv_login');
  if (await isPostulacionOpen(page)) {
    ctx.recordStep('ofv_session_reuse', 'ok', {
      currentUrl: page.url(),
      pageState: 'postulacion_open',
      reusedExistingSession: true,
    });
    return;
  }

  const usernameInput = page.locator('#ctl00_ContentPlaceHolder1_txtUsuario').first();
  const passwordInput = page.locator('#ctl00_ContentPlaceHolder1_txtPassword').first();
  const submitButton = page.locator('#ctl00_ContentPlaceHolder1_BtnAceptar').first();

  if ((await usernameInput.count()) > 0 && (await passwordInput.count()) > 0 && (await submitButton.count()) > 0) {
    await usernameInput.fill(credentials.username);
    await passwordInput.fill(credentials.password);
    await submitButton.click();
    await page.waitForLoadState('domcontentloaded').catch(() => null);
    await page.waitForTimeout(5000);
  }

  const current = page.url().toLowerCase();
  if (
    current.includes('/ofv/home.aspx') ||
    current.includes('portalcertificacion') ||
    (await isPostulacionOpen(page))
  ) {
    await capturePageState(ctx, page, 'ofv_authenticated');
    ctx.recordStep('ofv_session_reuse', 'ok', {
      currentUrl: page.url(),
      pageState: await classifyPageState(page),
      reusedExistingSession: current.includes('/ofv/home.aspx'),
    });
    return;
  }

  ctx.recordStep('ofv_session_reuse', 'error', {
    currentUrl: page.url(),
    pageState: await classifyPageState(page),
  });
  throw new Error(`No fue posible autenticar OFV. URL=${page.url()} title=${await page.title()}`);
}

async function attemptSessionReuseFallbacks(
  ctx: ScenarioContext,
  portalPage: Page,
  authFlow: PortalAuthTrace[],
): Promise<boolean> {
  for (const [index, url] of DEFAULT_POSTULACION_FALLBACK_URLS.entries()) {
    await portalPage.goto(url, { waitUntil: 'domcontentloaded' });
    await portalPage.waitForTimeout(5000);
    await capturePageState(ctx, portalPage, `postulacion_direct_fallback_${index + 1}`);
    const state = await classifyPageState(portalPage);
    const authResult = await classifyPortalAuthResult(portalPage);
    recordAuthStep(ctx, authFlow, {
      strategy: 'session_reuse',
      status: state === 'postulacion_open' ? 'ok' : 'error',
      currentUrl: portalPage.url(),
      pageState: state,
      portalAuthResult: authResult,
      details: { fallbackUrl: url, fallbackIndex: index + 1 },
    });
    if (state === 'postulacion_open') {
      await capturePageState(ctx, portalPage, `postulacion_direct_fallback_${index + 1}_open`);
      return true;
    }
  }
  return false;
}

async function attemptManualSeed(
  ctx: ScenarioContext,
  portalPage: Page,
  authFlow: PortalAuthTrace[],
): Promise<boolean> {
  const state = await classifyPageState(portalPage);
  if (state !== 'portal_login') {
    return false;
  }

  await capturePageState(ctx, portalPage, 'postulacion_manual_seed_hold_start');
  await portalPage.waitForTimeout(manualSeedTimeoutMs(ctx));
  await portalPage.waitForLoadState('domcontentloaded').catch(() => null);
  await capturePageState(ctx, portalPage, 'postulacion_manual_seed_hold_end');
  const endState = await classifyPageState(portalPage);
  const authResult = endState === 'postulacion_open' ? 'authenticated' : 'manual_seed_timeout';
  recordAuthStep(ctx, authFlow, {
    strategy: 'manual_seed',
    status: endState === 'postulacion_open' ? 'ok' : 'error',
    currentUrl: portalPage.url(),
    pageState: endState,
    portalAuthResult: authResult,
  });
  return endState === 'postulacion_open';
}

export async function openPostulacionPage(
  ctx: ScenarioContext,
  page: Page,
  credentials: DgiiPortalCredentials,
): Promise<PostulacionOpenResult> {
  const authFlow: PortalAuthTrace[] = [];
  if (await isPostulacionOpen(page)) {
    recordAuthStep(ctx, authFlow, {
      strategy: 'session_reuse',
      status: 'ok',
      currentUrl: page.url(),
      pageState: 'postulacion_open',
      portalAuthResult: 'authenticated',
      details: { onExistingPage: true },
    });
    return { page, authFlow, portalAuthResult: 'authenticated' };
  }

  const clickedMenuEntry = await page.evaluate(() => {
    const direct = document.getElementById('2786');
    if (direct instanceof HTMLElement) {
      direct.click();
      return true;
    }
    const fallback = Array.from(document.querySelectorAll('td.menu')).find((element) =>
      (element.textContent || '').includes('Solicitud para ser Emisor Electrónico'),
    );
    if (fallback instanceof HTMLElement) {
      fallback.click();
      return true;
    }
    return false;
  });
  if (clickedMenuEntry) {
    await page.waitForLoadState('domcontentloaded').catch(() => null);
    await page.waitForTimeout(2000);
  } else {
    await page.goto(DEFAULT_FE_ACCESS_URL, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2000);
  }
  await capturePageState(ctx, page, 'postulacion_fe_access');

  const accessButton = page.locator('#ctl00_ContentPlaceHolder1_btnAcceso').first();
  if ((await accessButton.count()) === 0) {
    await capturePageState(ctx, page, 'postulacion_missing_access_button');
    throw new Error('No se encontro el boton de acceso al portal de certificacion en OFV');
  }

  let portalPage = page;
  const popupPromise = page.context().waitForEvent('page', { timeout: 15000 }).catch(() => null);
  await accessButton.click();
  const popup = await popupPromise;
  if (popup) {
    await popup.waitForLoadState('domcontentloaded').catch(() => null);
    portalPage = popup;
  } else {
    await page.waitForTimeout(4000);
  }

  let pageState = await classifyPageState(portalPage);
  recordAuthStep(ctx, authFlow, {
    strategy: 'portal_state_probe',
    status: pageState === 'postulacion_open' ? 'ok' : 'error',
    currentUrl: portalPage.url(),
    pageState,
    portalAuthResult: await classifyPortalAuthResult(portalPage),
    details: { stage: 'after_fe_access' },
  });

  if (pageState === 'postulacion_open') {
    return { page: portalPage, authFlow, portalAuthResult: 'authenticated' };
  }

  if (portalPage.url().toLowerCase().includes('portalcertificacion')) {
    const viewButton = portalPage.locator('#btnVerPostulacionEmisor').first();
    if ((await viewButton.count()) > 0) {
      await viewButton.click();
      await portalPage.waitForTimeout(4000);
      await capturePageState(ctx, portalPage, 'postulacion_after_view_button');
      pageState = await classifyPageState(portalPage);
      recordAuthStep(ctx, authFlow, {
        strategy: 'view_postulacion',
        status: pageState === 'postulacion_open' ? 'ok' : 'error',
        currentUrl: portalPage.url(),
        pageState,
        portalAuthResult: await classifyPortalAuthResult(portalPage),
      });
      if (pageState === 'postulacion_open') {
        return { page: portalPage, authFlow, portalAuthResult: 'authenticated' };
      }
    }
  }

  const strategies = parseAuthStrategies(ctx);
  let lastAuthResult: PortalAuthResult = await classifyPortalAuthResult(portalPage);

  for (const strategy of strategies) {
    if (strategy === 'session_reuse') {
      if (await attemptSessionReuseFallbacks(ctx, portalPage, authFlow)) {
        return { page: portalPage, authFlow, portalAuthResult: 'authenticated' };
      }
      lastAuthResult = await classifyPortalAuthResult(portalPage);
      continue;
    }

    if (strategy === 'portal_credentials') {
      lastAuthResult = await loginCertPortalIfNeeded(ctx, portalPage, credentials, authFlow);
      if (lastAuthResult === 'authenticated' || (await classifyPageState(portalPage)) === 'postulacion_open') {
        return { page: portalPage, authFlow, portalAuthResult: 'authenticated' };
      }
      continue;
    }

    if (strategy === 'manual_seed') {
      const manualSeedOk = await attemptManualSeed(ctx, portalPage, authFlow);
      lastAuthResult = manualSeedOk ? 'authenticated' : 'manual_seed_timeout';
      if (manualSeedOk) {
        return { page: portalPage, authFlow, portalAuthResult: 'authenticated' };
      }
    }
  }

  await capturePageState(ctx, portalPage, 'postulacion_unknown_state');
  throw new Error(
    `Portal de certificacion abierto pero no se detecto formulario de postulacion. URL=${portalPage.url()} portalAuthResult=${lastAuthResult}`,
  );
}

export function postulacionFormData(ctx: ScenarioContext): Record<string, string> {
  const metadata = ctx.job.target?.metadata || {};
  const apiBase = normalizeApiBase(getString(metadata, 'apiBase'));
  const softwareName = getString(metadata, 'softwareName', 'getupsoft');
  const softwareVersion = getString(metadata, 'softwareVersion', '1.0');
  const endpointMode = getString(metadata, 'endpointMode', 'api').toLowerCase();

  if (!apiBase) {
    throw new Error('DGII postulacion requires target.metadata.apiBase');
  }

  const contract = endpointMode === 'fe' ? 'fe' : 'api';
  if (contract === 'fe') {
    return {
      inputNombreSoftware: softwareName,
      inputVersionSoftware: softwareVersion,
      inputUrlRecepcion: `${apiBase}/fe/recepcion/api/ecf`,
      inputUrlAprobacionComercial: `${apiBase}/fe/aprobacioncomercial/api/ecf`,
      inputUrlAutenticacion: `${apiBase}/fe/autenticacion/api/semilla`,
    };
  }

  return {
    inputNombreSoftware: softwareName,
    inputVersionSoftware: softwareVersion,
    inputUrlRecepcion: `${apiBase}/api/ecf/receive`,
    inputUrlAprobacionComercial: `${apiBase}/api/ecf/approve`,
    inputUrlAutenticacion: `${apiBase}/api/auth`,
  };
}

export function classifyPortalResponse(bodyPreview: string): { classification: string; message: string } {
  const lower = bodyPreview.toLowerCase();
  if (lower.includes('firma inválida') || lower.includes('firma invalida')) {
    return { classification: 'signature_invalid', message: 'DGII rechazo la firma del XML.' };
  }
  if (lower.includes('versionsoftware')) {
    return { classification: 'version_software_invalid', message: 'DGII rechazo VersionSoftware.' };
  }
  if (lower.includes('autenticación fallida') || lower.includes('credenciales proporcionadas no son válidas')) {
    return { classification: 'portal_credentials_invalid', message: 'Portal DGII rechazo las credenciales.' };
  }
  return { classification: 'unknown', message: 'Sin clasificacion especifica.' };
}
