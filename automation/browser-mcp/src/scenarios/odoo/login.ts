import type { ScenarioHandler } from '../../types';

export const odooLoginScenario: ScenarioHandler = async (ctx) => {
  const url = ctx.job.target?.url;
  if (!url) {
    throw new Error('odoo-login requires target.url');
  }
  await ctx.page.goto(url, { waitUntil: 'domcontentloaded' });
  await ctx.captureSnapshot('odoo-login');
  await ctx.captureScreenshot('odoo-login');
  ctx.recordStep('odoo-login-open', 'ok', { url });
  return { url };
};
