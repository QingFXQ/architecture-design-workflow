// Offline discovery by default. --live-readonly adds ping/model_info only.
// Does not install plugins, open/save files, create geometry or change views.
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
const args = process.argv.slice(2);
if (args.some((x) => x !== '--live-readonly')) throw new Error('Usage: node probe.mjs [--live-readonly]');
const live = args.includes('--live-readonly');
const child = spawn(process.execPath, [fileURLToPath(new URL('./start.mjs', import.meta.url))], {
  env: process.env, stdio: ['pipe', 'pipe', 'pipe'],
});
let buffer = '', nextId = 0;
const pending = new Map();
child.stderr.on('data', (data) => process.stderr.write(data));
function failAll(error) {
  for (const request of pending.values()) { clearTimeout(request.timer); request.reject(error); }
  pending.clear();
}
child.on('error', failAll);
child.on('exit', (code) => failAll(new Error(`MCP process exited (${code})`)));
child.stdin.on('error', failAll);
child.stdout.on('data', (data) => {
  buffer += data.toString();
  let index;
  while ((index = buffer.indexOf('\n')) >= 0) {
    const line = buffer.slice(0, index); buffer = buffer.slice(index + 1);
    if (!line.trim()) continue;
    try {
      const response = JSON.parse(line), request = pending.get(response.id);
      if (request) {
        pending.delete(response.id); clearTimeout(request.timer);
        response.error ? request.reject(new Error(JSON.stringify(response.error))) : request.resolve(response.result);
      }
    } catch (error) { failAll(error); }
  }
});
function rpc(method, params) {
  const id = ++nextId;
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => { pending.delete(id); reject(new Error(`Timeout: ${method}`)); }, 15000);
    pending.set(id, { resolve, reject, timer });
    child.stdin.write(JSON.stringify({ jsonrpc: '2.0', id, method, params }) + '\n');
  });
}
try {
  const init = await rpc('initialize', {
    protocolVersion: '2025-06-18', capabilities: {},
    clientInfo: { name: 'architecture-workflow-probe', version: '1.0.0' },
  });
  child.stdin.write(JSON.stringify({ jsonrpc: '2.0', method: 'notifications/initialized' }) + '\n');
  const { tools } = await rpc('tools/list', {});
  const names = tools.map((t) => t.name);
  for (const required of ['ping', 'model_info', 'create_box', 'create_shape', 'screenshot', 'export_file', 'run_ruby']) {
    if (!names.includes(required)) throw new Error(`Missing required tool: ${required}`);
  }
  if (init.serverInfo.version !== '1.3.0' || tools.length !== 29) throw new Error('Unexpected bundle version or tool catalogue');
  const result = { server: init.serverInfo, tool_count: tools.length, tools: names, live_verified: false };
  if (live) {
    result.readonly = {};
    for (const name of ['ping', 'model_info']) {
      const response = await rpc('tools/call', { name, arguments: {} });
      if (response.isError) throw new Error(`${name}: ${JSON.stringify(response.content)}`);
      result.readonly[name] = response.content;
    }
    result.live_verified = true;
  }
  console.log(JSON.stringify(result, null, 2));
} catch (error) {
  console.error(error.message); process.exitCode = 1;
} finally {
  failAll(new Error('Probe closed'));
  child.stdin.end(); // Let EOF close the bundle and wrapper normally.
  const fallback = setTimeout(() => child.kill(), 2000); fallback.unref();
}
