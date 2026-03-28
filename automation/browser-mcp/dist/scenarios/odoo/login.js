"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.odooLoginScenario = void 0;
const odooLoginScenario = async (ctx) => {
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
exports.odooLoginScenario = odooLoginScenario;
