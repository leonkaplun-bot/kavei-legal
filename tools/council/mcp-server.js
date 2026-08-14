#!/usr/bin/env node
'use strict';

// Minimal MCP stdio server exposing the council to Claude Code as native tools.
// Hand-rolled JSON-RPC framing keeps this dependency-free, so a freshly cloned
// container needs no install step before the tools are usable.

const { ask, compare, status, listModels } = require('./lib/council');
const providers = require('./lib/providers');

const PROTOCOL_VERSION = '2025-06-18';
const SERVER_INFO = { name: 'council', version: '1.0.0' };

const PROVIDER_ENUM = providers.names();

const TOOLS = [
  {
    name: 'council_status',
    description:
      'Check whether Grok (xAI) and Codex (OpenAI) are reachable and authenticated from this session. Reports endpoint, key presence, and the resolved model per provider. Run this first if a council call fails.',
    inputSchema: { type: 'object', properties: {}, additionalProperties: false },
  },
  {
    name: 'ask_grok',
    description:
      'Ask Grok (xAI) a single question and return its answer. Use for an independent second opinion, adversarial review, or a cross-check of your own reasoning.',
    inputSchema: {
      type: 'object',
      properties: {
        prompt: { type: 'string', description: 'The question. Include all context needed — the provider sees nothing else.' },
        system: { type: 'string', description: 'Optional system prompt setting the role or output format.' },
        model: { type: 'string', description: 'Optional model override; defaults to the best available.' },
      },
      required: ['prompt'],
      additionalProperties: false,
    },
  },
  {
    name: 'ask_codex',
    description:
      'Ask Codex (OpenAI) a single question and return its answer. Use for an independent second opinion on code, or to have the same task solved twice and compared.',
    inputSchema: {
      type: 'object',
      properties: {
        prompt: { type: 'string', description: 'The question. Include all context needed — the provider sees nothing else.' },
        system: { type: 'string', description: 'Optional system prompt setting the role or output format.' },
        model: { type: 'string', description: 'Optional model override; defaults to the best available.' },
      },
      required: ['prompt'],
      additionalProperties: false,
    },
  },
  {
    name: 'council_compare',
    description:
      'Put the same prompt to Grok and Codex in parallel and return both answers side by side for comparison. Use when you want independent opinions before committing to an approach, or a double-check of a risky change. A provider that fails is reported inline rather than aborting the call.',
    inputSchema: {
      type: 'object',
      properties: {
        prompt: { type: 'string', description: 'The question put to every provider.' },
        system: { type: 'string', description: 'Optional shared system prompt.' },
        only: {
          type: 'array',
          items: { type: 'string', enum: PROVIDER_ENUM },
          description: 'Limit to a subset of providers. Defaults to all.',
        },
      },
      required: ['prompt'],
      additionalProperties: false,
    },
  },
  {
    name: 'council_models',
    description: 'List the model IDs a provider account can actually use.',
    inputSchema: {
      type: 'object',
      properties: { provider: { type: 'string', enum: PROVIDER_ENUM } },
      required: ['provider'],
      additionalProperties: false,
    },
  },
];

function send(msg) {
  process.stdout.write(JSON.stringify(msg) + '\n');
}

function reply(id, result) {
  send({ jsonrpc: '2.0', id, result });
}

function replyError(id, code, message) {
  send({ jsonrpc: '2.0', id, error: { code, message } });
}

function textResult(text, isError = false) {
  return { content: [{ type: 'text', text }], isError };
}

function formatStatus(rows) {
  return rows
    .map((r) => {
      const mark = r.authenticated ? 'READY' : r.reachable ? 'NOT READY' : 'DOWN';
      const isLocal = r.transport === 'local-cli';
      return [
        `[${mark}] ${r.label}`,
        `  via     : ${isLocal ? 'local CLI (no API key)' : 'vendor API'}`,
        isLocal ? `  binary  : ${r.localBin || '(not found)'}` : `  endpoint: ${r.baseUrl}`,
        isLocal ? null : `  key env : ${r.keyEnv} ${r.keyPresent ? '(set)' : '(missing)'}`,
        !isLocal && r.localBin ? `  note    : local CLI also found at ${r.localBin}` : null,
        !isLocal && r.model ? `  model   : ${r.model}` : null,
        r.detail ? `  detail  : ${r.detail}` : null,
      ]
        .filter(Boolean)
        .join('\n');
    })
    .join('\n\n');
}

async function callTool(name, argsIn) {
  const args = argsIn || {};

  if (name === 'council_status') return textResult(formatStatus(await status()));

  if (name === 'council_models') {
    const models = await listModels(args.provider, { useCache: false });
    return textResult(models.join('\n') || '(none reported)');
  }

  if (name === 'ask_grok' || name === 'ask_codex') {
    const provider = name === 'ask_grok' ? 'grok' : 'codex';
    const r = await ask(provider, args.prompt, { system: args.system, model: args.model });
    return textResult(`${r.label} — ${r.model} [${r.transport}] (${(r.ms / 1000).toFixed(1)}s)\n\n${r.text.trim()}`);
  }

  if (name === 'council_compare') {
    const results = await compare(args.only, args.prompt, { system: args.system });
    const body = results
      .map((r) =>
        r.ok
          ? `===== ${r.label} — ${r.model} [${r.transport}] (${(r.ms / 1000).toFixed(1)}s) =====\n${r.text.trim()}`
          : `===== ${r.label} — FAILED =====\n${r.error}${r.hint ? `\nhint: ${r.hint}` : ''}`
      )
      .join('\n\n');
    return textResult(body, !results.some((r) => r.ok));
  }

  throw new Error(`unknown tool "${name}"`);
}

async function handle(msg) {
  const { id, method, params } = msg;

  // Notifications carry no id and expect no response.
  if (id === undefined || id === null) return;

  if (method === 'initialize') {
    const requested = params && typeof params.protocolVersion === 'string' ? params.protocolVersion : null;
    reply(id, {
      protocolVersion: requested || PROTOCOL_VERSION,
      capabilities: { tools: {} },
      serverInfo: SERVER_INFO,
    });
    return;
  }

  if (method === 'tools/list') {
    reply(id, { tools: TOOLS });
    return;
  }

  if (method === 'tools/call') {
    const toolName = params && params.name;
    try {
      reply(id, await callTool(toolName, params && params.arguments));
    } catch (err) {
      // Tool-level failures come back as results, not protocol errors, so the
      // model can read the hint and act on it.
      reply(id, textResult(`${err.message}${err.hint ? `\nhint: ${err.hint}` : ''}`, true));
    }
    return;
  }

  if (method === 'ping') {
    reply(id, {});
    return;
  }

  replyError(id, -32601, `method not found: ${method}`);
}

let buffer = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', (chunk) => {
  buffer += chunk;
  let nl;
  while ((nl = buffer.indexOf('\n')) !== -1) {
    const line = buffer.slice(0, nl).trim();
    buffer = buffer.slice(nl + 1);
    if (!line) continue;
    let msg;
    try {
      msg = JSON.parse(line);
    } catch {
      continue;
    }
    handle(msg).catch((err) => {
      if (msg && msg.id != null) replyError(msg.id, -32603, err.message);
    });
  }
});
process.stdin.on('end', () => process.exit(0));
