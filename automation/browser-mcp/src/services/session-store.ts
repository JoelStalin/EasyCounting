import fs from 'node:fs';
import path from 'node:path';

export interface SavedSession {
  sessionRef: string;
  storageStatePath: string;
}

function sessionFileName(jobId: string): string {
  return `${jobId.replace(/[^a-zA-Z0-9._-]+/g, '-')}-storage-state.json`;
}

export async function saveSessionState(
  sessionsRoot: string,
  jobId: string,
  storageState: unknown,
): Promise<SavedSession> {
  await fs.promises.mkdir(sessionsRoot, { recursive: true });
  const storageStatePath = path.join(sessionsRoot, sessionFileName(jobId));
  await fs.promises.writeFile(storageStatePath, JSON.stringify(storageState, null, 2), 'utf-8');
  return {
    sessionRef: path.basename(storageStatePath, '.json'),
    storageStatePath,
  };
}

export async function listSessions(sessionsRoot: string): Promise<SavedSession[]> {
  await fs.promises.mkdir(sessionsRoot, { recursive: true });
  const entries = await fs.promises.readdir(sessionsRoot, { withFileTypes: true });
  return entries
    .filter((entry) => entry.isFile() && entry.name.endsWith('.json'))
    .map((entry) => ({
      sessionRef: entry.name.replace(/\.json$/, ''),
      storageStatePath: path.join(sessionsRoot, entry.name),
    }));
}

export async function deleteSession(sessionsRoot: string, sessionRef: string): Promise<boolean> {
  const target = path.join(sessionsRoot, `${sessionRef}.json`);
  if (!fs.existsSync(target)) {
    return false;
  }
  await fs.promises.unlink(target);
  return true;
}
