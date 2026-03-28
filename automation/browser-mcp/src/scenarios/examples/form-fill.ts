import type { ScenarioHandler } from '../../types';

export const formFillScenario: ScenarioHandler = async (ctx) => {
  const url = ctx.job.target?.url;
  const metadata = ctx.job.target?.metadata || {};
  const fields = Array.isArray(metadata.fields) ? metadata.fields : [];
  const submitSelector = String(metadata.submitSelector || 'button[type="submit"]');

  if (!url) {
    throw new Error('form-fill requires target.url');
  }

  await ctx.page.goto(url, { waitUntil: 'domcontentloaded' });
  for (const field of fields as Array<Record<string, unknown>>) {
    const selector = String(field.selector || '');
    const value = String(field.value || '');
    if (selector) {
      await ctx.page.locator(selector).fill(value);
    }
  }
  await ctx.captureSnapshot('before-submit');
  await ctx.page.locator(submitSelector).click();
  await ctx.page.waitForLoadState('networkidle');
  await ctx.captureScreenshot('after-submit');
  ctx.recordStep('form-fill', 'ok', { fieldCount: fields.length });
  return { fieldCount: fields.length };
};
