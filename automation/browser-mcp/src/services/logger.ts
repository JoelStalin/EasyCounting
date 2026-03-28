import pino from 'pino';

import type { AppConfig } from '../types';

export function createLogger(config: AppConfig) {
  return pino({
    name: 'browser-mcp',
    level: config.service.logLevel,
    base: undefined,
    timestamp: pino.stdTimeFunctions.isoTime,
  });
}
