"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.loginPersistentSessionScenario = void 0;
const loginPersistentSessionScenario = async (ctx) => {
    const metadata = ctx.job.target?.metadata || {};
    const url = ctx.job.target?.url;
    const usernameSelector = String(metadata.usernameSelector || 'input[name="username"]');
    const passwordSelector = String(metadata.passwordSelector || 'input[name="password"]');
    const submitSelector = String(metadata.submitSelector || 'button[type="submit"]');
    const username = String(metadata.username || '');
    const password = String(metadata.password || '');
    if (!url) {
        throw new Error('login-persistent-session requires target.url');
    }
    await ctx.page.goto(url, { waitUntil: 'domcontentloaded' });
    await ctx.page.locator(usernameSelector).fill(username);
    await ctx.page.locator(passwordSelector).fill(password);
    await ctx.page.locator(submitSelector).click();
    await ctx.page.waitForLoadState('networkidle');
    await ctx.captureSnapshot('after-login');
    await ctx.captureScreenshot('after-login');
    const storageState = await ctx.saveStorageState();
    ctx.recordStep('login', 'ok', { url, storageState });
    return { storageState };
};
exports.loginPersistentSessionScenario = loginPersistentSessionScenario;
