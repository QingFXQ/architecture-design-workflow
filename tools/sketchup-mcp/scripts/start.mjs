// Local wrapper only; upstream bundle is kept intact with its licenses.
import { spawn } from 'node:child_process';
import { existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const entry = fileURLToPath(new URL('../runtime/v1.3.0/server/index.mjs', import.meta.url));
if (!existsSync(entry)) {
  console.error('SketchUp runtime is not prepared. Run tools/sketchup-mcp/scripts/prepare.ps1 once.');
  process.exit(1);
}
const env = {
  ...process.env,
  SKETCHUP_MCP_PORT: process.env.SKETCHUP_MCP_PORT || '19876',
  SKETCHUP_MCP_TIMEOUT: process.env.SKETCHUP_MCP_TIMEOUT || '120',
};
const child = spawn(process.execPath, [entry], { env, stdio: 'inherit' });
child.on('error', (error) => { console.error(error.message); process.exitCode = 1; });
child.on('exit', (code, signal) => { process.exitCode = code ?? (signal ? 1 : 0); });
for (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, () => child.kill(signal));
