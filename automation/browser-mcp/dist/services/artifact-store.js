"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.createArtifactContext = createArtifactContext;
const node_fs_1 = __importDefault(require("node:fs"));
const node_path_1 = __importDefault(require("node:path"));
function sanitizeName(value) {
    return value.replace(/[^a-zA-Z0-9._-]+/g, '-');
}
function createArtifactContext(root, job) {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const scenario = sanitizeName(job.scenario);
    const jobId = sanitizeName(job.jobId);
    const outputDir = job.outputDir || node_path_1.default.join(root, `${timestamp}_${jobId}_${scenario}`);
    node_fs_1.default.mkdirSync(outputDir, { recursive: true });
    const artifacts = [];
    async function writeFile(name, content) {
        const filePath = node_path_1.default.join(outputDir, sanitizeName(name));
        await node_fs_1.default.promises.mkdir(node_path_1.default.dirname(filePath), { recursive: true });
        await node_fs_1.default.promises.writeFile(filePath, content);
        artifacts.push(filePath);
        return filePath;
    }
    return {
        outputDir,
        artifacts,
        writeText: (name, content) => writeFile(name, content),
        writeJson: (name, content) => writeFile(name, JSON.stringify(content, null, 2)),
        writeBuffer: (name, content) => writeFile(name, content),
        appendJsonl: async (name, line) => {
            const filePath = node_path_1.default.join(outputDir, sanitizeName(name));
            await node_fs_1.default.promises.mkdir(node_path_1.default.dirname(filePath), { recursive: true });
            await node_fs_1.default.promises.appendFile(filePath, `${JSON.stringify(line)}\n`, 'utf-8');
            if (!artifacts.includes(filePath)) {
                artifacts.push(filePath);
            }
            return filePath;
        },
    };
}
