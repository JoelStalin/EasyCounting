import type { BrowserContext } from 'playwright';

import type { BrowserMcpNetworkPolicy } from '../types';

function isAllowed(url: URL, allowedOrigins: string[]): boolean {
  if (allowedOrigins.length === 0) {
    return true;
  }
  return allowedOrigins.includes(url.origin);
}

function isBlocked(url: URL, blockedOrigins: string[]): boolean {
  return blockedOrigins.includes(url.origin);
}

export async function applyNetworkPolicy(
  context: BrowserContext,
  policy: BrowserMcpNetworkPolicy | undefined,
): Promise<void> {
  if (!policy) {
    return;
  }

  await context.route('**/*', async (route) => {
    const requestUrl = new URL(route.request().url());
    const blocked = policy.blockedOrigins || [];
    const allowed = policy.allowedOrigins || [];

    if (isBlocked(requestUrl, blocked)) {
      await route.abort('blockedbyclient');
      return;
    }

    if (!isAllowed(requestUrl, allowed)) {
      await route.abort('blockedbyclient');
      return;
    }

    for (const mock of policy.mockRoutes || []) {
      if (route.request().url().includes(mock.pattern)) {
        if (mock.action === 'abort') {
          await route.abort('blockedbyclient');
          return;
        }
        if (mock.action === 'fulfill') {
          await route.fulfill({
            status: mock.status || 200,
            body: mock.body || '',
            contentType: mock.contentType || 'application/json',
            headers: mock.headers,
          });
          return;
        }
      }
    }

    await route.continue();
  });
}
