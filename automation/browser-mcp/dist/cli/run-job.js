"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const node_fs_1 = __importDefault(require("node:fs"));
const env_1 = require("../config/env");
const job_runner_1 = require("../services/job-runner");
async function main() {
    const raw = node_fs_1.default.readFileSync(0, 'utf-8').trim();
    if (!raw) {
        throw new Error('Expected JSON job payload on stdin');
    }
    const job = JSON.parse(raw);
    const runner = new job_runner_1.JobRunner((0, env_1.loadConfig)());
    const response = await runner.runSync(job);
    process.stdout.write(`${JSON.stringify(response)}\n`);
}
void main();
