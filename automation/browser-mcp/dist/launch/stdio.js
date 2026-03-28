"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const node_path_1 = __importDefault(require("node:path"));
const node_child_process_1 = require("node:child_process");
const env_1 = require("../config/env");
async function main() {
    const config = (0, env_1.loadConfig)();
    const packageRoot = node_path_1.default.resolve(__dirname, '..', '..');
    const cliPath = node_path_1.default.resolve(packageRoot, 'node_modules', '@playwright', 'mcp', 'cli.js');
    const child = (0, node_child_process_1.spawn)(process.execPath, [cliPath, '--browser', config.browser.browserName], {
        stdio: 'inherit',
        cwd: packageRoot,
        env: process.env,
        shell: false,
    });
    child.on('exit', (code) => {
        process.exit(code ?? 0);
    });
}
void main();
