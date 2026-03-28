"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.createScenarioContext = createScenarioContext;
const node_fs_1 = __importDefault(require("node:fs"));
const node_path_1 = __importDefault(require("node:path"));
function createScenarioContext(args) {
    const { job, config, context, page, outputDir, recordStepResults, writeText, writeJson, writeBuffer, registerArtifact, } = args;
    return {
        job,
        config,
        context,
        page,
        outputDir,
        recordStep(name, status, details) {
            recordStepResults.push({ name, status, details });
        },
        async writeArtifact(name, content) {
            if (typeof content === 'string') {
                return writeText(name, content);
            }
            return writeBuffer(name, content);
        },
        registerArtifact,
        async captureSnapshot(label) {
            if (job.artifacts?.snapshot === false) {
                return undefined;
            }
            const snapshot = {
                url: page.url(),
                title: await page.title(),
                aria: await page.locator('body').ariaSnapshot().catch(() => null),
            };
            return writeJson(`snapshot-${label}.json`, snapshot);
        },
        async captureScreenshot(label) {
            if (job.artifacts?.screenshot === false) {
                return undefined;
            }
            const target = node_path_1.default.join(outputDir, `screenshot-${label}.png`);
            await page.screenshot({ path: target, fullPage: true });
            registerArtifact(target);
            return target;
        },
        async capturePdf(label) {
            if (job.artifacts?.pdf === false) {
                return undefined;
            }
            if (page.context().browser()?.browserType().name() !== 'chromium') {
                return undefined;
            }
            const target = node_path_1.default.join(outputDir, `page-${label}.pdf`);
            await node_fs_1.default.promises.mkdir(node_path_1.default.dirname(target), { recursive: true });
            await page.pdf({ path: target, printBackground: true });
            registerArtifact(target);
            return target;
        },
        async saveStorageState() {
            if (!job.saveSession && job.artifacts?.saveSession === false) {
                return undefined;
            }
            const target = node_path_1.default.join(outputDir, 'storage-state.json');
            await context.storageState({ path: target });
            registerArtifact(target);
            return target;
        },
    };
}
