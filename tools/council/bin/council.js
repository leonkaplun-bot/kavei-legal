#!/usr/bin/env node
'use strict';

// CLI front end for the advisory council.
//
//   council status
//   council models <grok|codex>
//   council ask <grok|codex> "question" [--system S] [--file F ...] [--model M] [--json]
//   council compare "question" [--only grok,codex] [--system S] [--file F ...] [--json]
//
// With no positional question the prompt is read from stdin, so large context
// can be piped in: `git diff | council compare "Review this diff"`.

const fs = require('node:fs');
const { ask, compare, status, listModels } = require('../lib/council');
const providers = require('../lib/providers');

function parseArgs(argv) {
  const out = { _: [], files: [], json: false };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--json') out.json = true;
    else if (a === '--system') out.system = argv[++i];
    else if (a === '--model') out.model = argv[++i];
    else if (a === '--file') out.files.push(argv[++i]);
    else if (a === '--only') out.only = String(argv[++i] || '').split(',').map((s) => s.trim()).filter(Boolean);
    else if (a === '--timeout') out.timeoutMs = Number(argv[++i]) * 1000;
    else if (a === '-h' || a === '--help') out.help = true;
    else out._.push(a);
  }
  return out;
}

function readStdin() {
  try {
    if (process.stdin.isTTY) return '';
    return fs.readFileSync(0, 'utf8');
  } catch {
    return '';
  }
}

function buildPrompt(args) {
  const parts = [];
  const positional = args._.join(' ').trim();
  if (positional) parts.push(positional);

  for (const f of args.files) {
    let body;
    try {
      body = fs.readFileSync(f, 'utf8');
    } catch (err) {
      throw new Error(`cannot read --file ${f}: ${err.message}`);
    }
    parts.push(`--- FILE: ${f} ---\n${body}\n--- END FILE: ${f} ---`);
  }

  const piped = readStdin().trim();
  if (piped) parts.push(piped);

  return parts.join('\n\n');
}

const USAGE = `council — ask Grok and Codex for independent opinions

  council status                       connectivity + credential check
  council models <grok|codex>          list model IDs the account can use
  council ask <grok|codex> "<prompt>"  ask one provider
  council compare "<prompt>"           ask every provider in parallel

Options
  --system <text>    system prompt
  --file <path>      attach a file (repeatable)
  --model <id>       override the model
  --only a,b         limit "compare" to these providers
  --timeout <sec>    request timeout (default 180)
  --json             machine-readable output

Prompt text can also be piped on stdin:
  git diff | council compare "Review this diff for correctness bugs"
`;

function printStatus(rows, asJson) {
  if (asJson) {
    process.stdout.write(JSON.stringify(rows, null, 2) + '\n');
    return;
  }
  for (const r of rows) {
    const mark = r.authenticated ? 'READY' : r.reachable ? 'NOT READY' : 'DOWN';
    process.stdout.write(`[${mark}] ${r.label}\n`);
    process.stdout.write(`          via      : ${r.transport === 'local-cli' ? 'local CLI (no API key)' : 'vendor API'}\n`);
    if (r.transport === 'local-cli') {
      process.stdout.write(`          binary   : ${r.localBin || '(not found)'}\n`);
    } else {
      process.stdout.write(`          endpoint : ${r.baseUrl}\n`);
      process.stdout.write(`          key env  : ${r.keyEnv} ${r.keyPresent ? '(set)' : '(missing)'}\n`);
      if (r.localBin) process.stdout.write(`          note     : local CLI also found at ${r.localBin}\n`);
      if (r.model) process.stdout.write(`          model    : ${r.model}\n`);
    }
    if (r.detail) process.stdout.write(`          detail   : ${r.detail}\n`);
    process.stdout.write('\n');
  }
  const ready = rows.filter((r) => r.authenticated).map((r) => r.provider);
  if (ready.length === rows.length) {
    process.stdout.write('All providers ready.\n');
    return;
  }
  process.stdout.write(`Ready: ${ready.length ? ready.join(', ') : 'none'}.\n`);
  process.stdout.write(
    'Two ways to get there: run this session on a machine that has the codex/grok CLIs installed (no key needed), or set XAI_API_KEY / OPENAI_API_KEY on the Claude Code environment.\n'
  );
}

function printAnswer(r) {
  process.stdout.write(`===== ${r.label} — ${r.model} [${r.transport}] (${(r.ms / 1000).toFixed(1)}s) =====\n`);
  process.stdout.write(r.text.trim() + '\n\n');
}

async function main() {
  const argv = process.argv.slice(2);
  const cmd = argv[0];
  const args = parseArgs(argv.slice(1));

  if (!cmd || args.help || cmd === 'help' || cmd === '--help' || cmd === '-h') {
    process.stdout.write(USAGE);
    return 0;
  }

  if (cmd === 'status') {
    printStatus(await status(), args.json);
    return 0;
  }

  if (cmd === 'models') {
    const name = args._[0];
    if (!name) throw new Error(`usage: council models <${providers.names().join('|')}>`);
    const models = await listModels(name, { useCache: false });
    process.stdout.write(args.json ? JSON.stringify(models, null, 2) + '\n' : models.join('\n') + '\n');
    return 0;
  }

  if (cmd === 'ask') {
    const name = args._.shift();
    if (!name) throw new Error(`usage: council ask <${providers.names().join('|')}> "<prompt>"`);
    const prompt = buildPrompt(args);
    const r = await ask(name, prompt, args);
    if (args.json) process.stdout.write(JSON.stringify(r, null, 2) + '\n');
    else printAnswer(r);
    return 0;
  }

  if (cmd === 'compare') {
    const prompt = buildPrompt(args);
    const results = await compare(args.only, prompt, args);
    if (args.json) {
      process.stdout.write(JSON.stringify(results, null, 2) + '\n');
    } else {
      for (const r of results) {
        if (r.ok) printAnswer(r);
        else {
          process.stdout.write(`===== ${r.label} — FAILED =====\n${r.error}\n`);
          if (r.hint) process.stdout.write(`hint: ${r.hint}\n`);
          process.stdout.write('\n');
        }
      }
    }
    return results.some((r) => r.ok) ? 0 : 1;
  }

  throw new Error(`unknown command "${cmd}"\n\n${USAGE}`);
}

main()
  .then((code) => process.exit(code))
  .catch((err) => {
    process.stderr.write(`council: ${err.message}\n`);
    if (err.hint) process.stderr.write(`hint: ${err.hint}\n`);
    process.exit(1);
  });
