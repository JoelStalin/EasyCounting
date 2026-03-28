"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.dgiiOfvLoginScenario = void 0;
const dgiiOfvLoginScenario = async (ctx) => {
    const url = ctx.job.target?.url || 'https://dgii.gov.do/OFV/home.aspx';
    await ctx.page.goto(url, { waitUntil: 'domcontentloaded' });
    await ctx.captureSnapshot('dgii-ofv-home');
    await ctx.captureScreenshot('dgii-ofv-home');
    ctx.recordStep('dgii-ofv-login-open', 'ok', { url });
    return { url };
};
exports.dgiiOfvLoginScenario = dgiiOfvLoginScenario;
