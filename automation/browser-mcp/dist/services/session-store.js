"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.saveSessionState = saveSessionState;
exports.listSessions = listSessions;
exports.deleteSession = deleteSession;
const node_fs_1 = __importDefault(require("node:fs"));
const node_path_1 = __importDefault(require("node:path"));
function sessionFileName(jobId) {
    return `${jobId.replace(/[^a-zA-Z0-9._-]+/g, '-')}-storage-state.json`;
}
async function saveSessionState(sessionsRoot, jobId, storageState) {
    await node_fs_1.default.promises.mkdir(sessionsRoot, { recursive: true });
    const storageStatePath = node_path_1.default.join(sessionsRoot, sessionFileName(jobId));
    await node_fs_1.default.promises.writeFile(storageStatePath, JSON.stringify(storageState, null, 2), 'utf-8');
    return {
        sessionRef: node_path_1.default.basename(storageStatePath, '.json'),
        storageStatePath,
    };
}
async function listSessions(sessionsRoot) {
    await node_fs_1.default.promises.mkdir(sessionsRoot, { recursive: true });
    const entries = await node_fs_1.default.promises.readdir(sessionsRoot, { withFileTypes: true });
    return entries
        .filter((entry) => entry.isFile() && entry.name.endsWith('.json'))
        .map((entry) => ({
        sessionRef: entry.name.replace(/\.json$/, ''),
        storageStatePath: node_path_1.default.join(sessionsRoot, entry.name),
    }));
}
async function deleteSession(sessionsRoot, sessionRef) {
    const target = node_path_1.default.join(sessionsRoot, `${sessionRef}.json`);
    if (!node_fs_1.default.existsSync(target)) {
        return false;
    }
    await node_fs_1.default.promises.unlink(target);
    return true;
}
