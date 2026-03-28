"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.cookiesLocalstorageScenario = void 0;
const cookiesLocalstorageScenario = async (ctx) => {
    const url = ctx.job.target?.url;
    const metadata = ctx.job.target?.metadata || {};
    const cookies = Array.isArray(metadata.cookies) ? metadata.cookies : [];
    const storageEntries = metadata.localStorage && typeof metadata.localStorage === 'object'
        ? metadata.localStorage
        : {};
    if (!url) {
        throw new Error('cookies-localstorage requires target.url');
    }
    if (cookies.length > 0) {
        await ctx.context.addCookies(cookies);
    }
    await ctx.page.goto(url, { waitUntil: 'domcontentloaded' });
    await ctx.page.evaluate((entries) => {
        Object.entries(entries).forEach(([key, value]) => window.localStorage.setItem(key, value));
    }, storageEntries);
    const loaded = await ctx.page.evaluate(() => ({
        localStorage: { ...window.localStorage },
        cookies: document.cookie,
    }));
    await ctx.captureSnapshot('cookies-localstorage');
    ctx.recordStep('cookies-localstorage', 'ok', { cookieCount: cookies.length });
    return loaded;
};
exports.cookiesLocalstorageScenario = cookiesLocalstorageScenario;
