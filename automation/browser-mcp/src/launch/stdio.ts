import path from 'node:path';
import { spawn } from 'node:child_process';

import { loadConfig } from '../config/env';

async function main() {
  const config = loadConfig();
  const packageRoot = path.resolve(__dirname, '..', '..');
  const cliPath = path.resolve(
    packageRoot,
    'node_modules',
    '@playwright',
    'mcp',
    'cli.js',
  );
  const child = spawn(
    process.execPath,
    [cliPath, '--browser', config.browser.browserName],
    {
      stdio: 'inherit',
      cwd: packageRoot,
      env: process.env,
      shell: false,
    },
  );
  child.on('exit', (code) => {
    process.exit(code ?? 0);
  });
}

void main();
