import { execFile } from 'node:child_process';
import { appendFile, readFile } from 'node:fs/promises';
import path from 'node:path';
import { promisify } from 'node:util';

const execFileAsync = promisify(execFile);

const PROJECT_ROOT = process.env.ARCH_PROJECT_ROOT || process.cwd();
const REPO_ROOT = process.env.ARCH_WORKFLOW_ROOT || process.cwd();
const STATE_SCRIPT = path.join(REPO_ROOT, 'tools/studio_state/check_state.py');
const SMOKE_SCRIPT = path.join(PROJECT_ROOT, '.revit-work/smoke_local.py');
const REVIEW_MATRIX = path.join(PROJECT_ROOT, 'REVIEW_MATRIX.csv');
const REVIEW_HEADER = [
  'date',
  'package_id',
  'kind',
  'scope',
  'intent',
  'function_check',
  'model_check',
  'delivery_check',
  'status',
  'evidence',
  'notes',
];

function text(value) {
  const body = typeof value === 'string' ? value : JSON.stringify(value, null, 2);
  return [{ type: 'text', text: body }];
}

function parseJson(value) {
  try {
    return JSON.parse(value);
  } catch {
    return null;
  }
}

function csvEscape(value) {
  const textValue = value === undefined || value === null ? '' : String(value);
  return `"${textValue.replace(/"/g, '""')}"`;
}

async function runPython(script, args) {
  try {
    const { stdout, stderr } = await execFileAsync(
      process.env.DSH_WUCHANG_PYTHON || 'python',
      [script, ...args],
      {
        cwd: PROJECT_ROOT,
        encoding: 'utf8',
        maxBuffer: 32 * 1024 * 1024,
        windowsHide: true,
        env: { ...process.env, PYTHONIOENCODING: 'utf-8' },
      },
    );
    return { ok: true, stdout, stderr, code: 0 };
  } catch (error) {
    return {
      ok: false,
      stdout: typeof error.stdout === 'string' ? error.stdout : '',
      stderr: typeof error.stderr === 'string' ? error.stderr : String(error),
      code: typeof error.code === 'number' ? error.code : -1,
    };
  }
}

const stateTool = {
  name: 'wuchang_state',
  description:
    'Run the Wuchang library project state check: area totals, Gate status, decisions, blockers, artifacts, and git HEAD. Read-only.',
  parameters: {
    type: 'object',
    properties: {
      root: {
        type: 'string',
        description: 'Project root; defaults to the configured Wuchang library folder.',
      },
      strict: {
        type: 'boolean',
        description: 'Treat warnings as errors.',
      },
    },
    additionalProperties: false,
  },
  output: {
    schema: { type: 'object', additionalProperties: true },
    render: (_args, value) => text(value),
  },
  async execute(args = {}) {
    const root =
      typeof args.root === 'string' && args.root.trim() ? args.root.trim() : PROJECT_ROOT;
    const cliArgs = ['--root', root, '--json'];
    if (args.strict === true) cliArgs.push('--strict');
    const run = await runPython(STATE_SCRIPT, cliArgs);
    const payload = parseJson(run.stdout);
    if (payload) return payload;
    return {
      ok: false,
      error: 'state check did not return JSON',
      stderr: run.stderr,
      exitCode: run.code,
    };
  },
};

const revitTool = {
  name: 'wuchang_revit_read',
  description:
    'Read the active Revit model through the local MCP bridge. Read-only: it never creates, edits, or deletes model elements.',
  parameters: {
    type: 'object',
    properties: {
      probe: {
        type: 'string',
        enum: ['both', 'view', 'statistics'],
        description: 'Which read-only probe to run: current view, model statistics, or both.',
      },
    },
    additionalProperties: false,
  },
  output: {
    schema: { type: 'object', additionalProperties: true },
    render: (_args, value) => text(value),
  },
  async execute(args = {}) {
    const probe = args.probe || 'both';
    if (!['both', 'view', 'statistics'].includes(probe)) {
      return { ok: false, error: 'probe must be both, view, or statistics' };
    }
    const run = await runPython(SMOKE_SCRIPT, []);
    const payload = parseJson(run.stdout);
    if (!payload) {
      return {
        ok: false,
        error: 'Revit probe did not return JSON',
        stderr: run.stderr,
        exitCode: run.code,
      };
    }
    if (probe === 'both') {
      return { ok: true, ...payload };
    }
    const id = probe === 'view' ? '2' : '3';
    return {
      ok: true,
      probe,
      host: payload.host,
      read_only: true,
      response: payload.responses?.[id] ?? null,
      server_stderr: payload.server_stderr ?? '',
    };
  },
};

const reviewTool = {
  name: 'wuchang_review',
  description:
    'List or append a drawing/function package review record in REVIEW_MATRIX.csv. Appends only; it does not approve a Gate.',
  parameters: {
    type: 'object',
    properties: {
      action: { type: 'string', enum: ['list', 'append'] },
      package_id: { type: 'string', description: 'e.g. BASE-01, B1-01, FUNC-PUBLIC-01' },
      kind: { type: 'string', enum: ['drawing', 'function'] },
      scope: {
        type: 'string',
        description: 'Floor/space group for drawing, or functional package for function.',
      },
      intent: { type: 'string', description: 'Intent and aesthetic conclusion.' },
      function_check: { type: 'string', description: 'Function/area/circulation conclusion.' },
      model_check: { type: 'string', description: 'Model/technical conclusion.' },
      delivery_check: { type: 'string', description: 'Drawing/expression/version conclusion.' },
      status: { type: 'string', enum: ['PASS', 'REVISE', 'RETURN_TO_SCHEME'] },
      evidence: { type: 'string', description: 'Files, views, hashes, or log labels.' },
      notes: { type: 'string', description: 'Limits, known unknowns, next action.' },
    },
    required: ['action'],
    additionalProperties: false,
  },
  output: {
    schema: { type: 'object', additionalProperties: true },
    render: (_args, value) => text(value),
  },
  async execute(args = {}) {
    if (args.action === 'list') {
      try {
        const csv = await readFile(REVIEW_MATRIX, 'utf8');
        const rows = Math.max(0, csv.trim().split(/\r?\n/).length - 1);
        return { ok: true, path: REVIEW_MATRIX, rows, csv };
      } catch {
        return {
          ok: true,
          path: REVIEW_MATRIX,
          rows: 0,
          csv: '',
          note: 'REVIEW_MATRIX.csv does not exist yet; the first append creates it.',
        };
      }
    }
    if (args.action !== 'append') {
      return { ok: false, error: 'action must be list or append' };
    }
    const missing = ['package_id', 'kind', 'scope', 'status'].filter((key) => !args[key]);
    if (missing.length > 0) {
      return { ok: false, error: `missing required fields: ${missing.join(', ')}` };
    }
    const row = [
      new Date().toISOString(),
      args.package_id,
      args.kind,
      args.scope,
      args.intent || '',
      args.function_check || '',
      args.model_check || '',
      args.delivery_check || '',
      args.status,
      args.evidence || '',
      args.notes || '',
    ];
    try {
      let exists = true;
      try {
        await readFile(REVIEW_MATRIX, 'utf8');
      } catch {
        exists = false;
      }
      const content =
        (exists ? '' : `${REVIEW_HEADER.map(csvEscape).join(',')}\n`) +
        `${row.map(csvEscape).join(',')}\n`;
      await appendFile(REVIEW_MATRIX, content, 'utf8');
      return { ok: true, path: REVIEW_MATRIX, appended: row };
    } catch (error) {
      return { ok: false, error: String(error) };
    }
  },
};

export const inject = ['tools'];

export function apply(ctx) {
  ctx.effect(() => ctx.tools.register(stateTool));
  ctx.effect(() => ctx.tools.register(revitTool));
  ctx.effect(() => ctx.tools.register(reviewTool));
}
