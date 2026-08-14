'use strict';

const os = require('node:os');
const path = require('node:path');
const fs = require('node:fs');

const { request } = require('./http');
const providers = require('./providers');

const CACHE_TTL_MS = 60 * 60 * 1000;

function cachePath(id) {
  return path.join(os.tmpdir(), `council-models-${id}.json`);
}

function readCache(id) {
  try {
    const raw = JSON.parse(fs.readFileSync(cachePath(id), 'utf8'));
    if (Date.now() - raw.at < CACHE_TTL_MS && Array.isArray(raw.models)) return raw.models;
  } catch {
    /* cache miss is not an error */
  }
  return null;
}

function writeCache(id, models) {
  try {
    fs.writeFileSync(cachePath(id), JSON.stringify({ at: Date.now(), models }));
  } catch {
    /* a read-only tmpdir just means we re-resolve next time */
  }
}

class CouncilError extends Error {
  constructor(message, { provider, status, hint } = {}) {
    super(message);
    this.name = 'CouncilError';
    this.provider = provider;
    this.status = status;
    this.hint = hint;
  }
}

function missingKeyError(p) {
  return new CouncilError(`${p.label}: no API key in environment`, {
    provider: p.id,
    hint: `Set ${p.keyEnv[0]} as an environment variable for this Claude Code environment (get one at ${p.consoleUrl}).`,
  });
}

async function listModels(name, { useCache = true } = {}) {
  const p = providers.get(name);
  const key = providers.apiKey(p);
  if (!key) throw missingKeyError(p);

  if (useCache) {
    const cached = readCache(p.id);
    if (cached) return cached;
  }

  const res = await request(`${p.baseUrl}/models`, {
    headers: { Authorization: `Bearer ${key}`, Accept: 'application/json' },
    timeoutMs: 30000,
  });

  if (res.status !== 200) {
    throw new CouncilError(`${p.label}: /models returned ${res.status}`, {
      provider: p.id,
      status: res.status,
      hint: res.status === 401 ? `The key in ${p.keyEnv[0]} was rejected.` : res.text.slice(0, 300),
    });
  }

  const models = (res.json && Array.isArray(res.json.data) ? res.json.data : [])
    .map((m) => m && m.id)
    .filter(Boolean)
    .sort();

  writeCache(p.id, models);
  return models;
}

async function resolveModel(name, explicit) {
  const p = providers.get(name);
  if (explicit) return explicit;
  if (process.env[p.modelEnv]) return process.env[p.modelEnv];

  let available = [];
  try {
    available = await listModels(name);
  } catch {
    // If the catalog is unreachable, fall back to the top preference and let
    // the chat call report the real error.
    return p.prefer[0];
  }

  const set = new Set(available);
  for (const candidate of p.prefer) if (set.has(candidate)) return candidate;

  // Nothing from the preference list — take the newest-looking match instead of
  // failing outright.
  const loose = available.filter((m) => p.prefer.some((c) => m.startsWith(c.split('-')[0])));
  return loose[loose.length - 1] || available[0] || p.prefer[0];
}

/**
 * Ask one provider a single question.
 * Returns { provider, label, model, text, usage, ms }.
 */
async function ask(name, prompt, options = {}) {
  const { system, model, timeoutMs = 180000 } = options;
  const p = providers.get(name);
  const key = providers.apiKey(p);
  if (!key) throw missingKeyError(p);
  if (!prompt || !String(prompt).trim()) {
    throw new CouncilError('prompt is empty', { provider: p.id });
  }

  const chosen = await resolveModel(name, model);
  const messages = [];
  if (system) messages.push({ role: 'system', content: system });
  messages.push({ role: 'user', content: String(prompt) });

  // Deliberately minimal payload: reasoning models reject `temperature` and
  // `max_tokens`, and omitting both keeps one code path valid everywhere.
  const started = Date.now();
  const res = await request(`${p.baseUrl}/chat/completions`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${key}`,
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: { model: chosen, messages },
    timeoutMs,
  });

  if (res.status !== 200) {
    const detail =
      (res.json && res.json.error && (res.json.error.message || res.json.error)) || res.text.slice(0, 400);
    throw new CouncilError(`${p.label}: chat/completions returned ${res.status} — ${detail}`, {
      provider: p.id,
      status: res.status,
      hint:
        res.status === 401
          ? `The key in ${p.keyEnv[0]} was rejected.`
          : res.status === 404
            ? `Model "${chosen}" may not exist for this account. Run "council models ${p.id}" to see what is available, then set ${p.modelEnv}.`
            : undefined,
    });
  }

  const choice = res.json && res.json.choices && res.json.choices[0];
  const text = (choice && choice.message && choice.message.content) || '';

  return {
    provider: p.id,
    label: p.label,
    model: (res.json && res.json.model) || chosen,
    text: typeof text === 'string' ? text : JSON.stringify(text),
    usage: (res.json && res.json.usage) || null,
    ms: Date.now() - started,
  };
}

/**
 * Ask several providers the same question in parallel. Never rejects: a failed
 * provider comes back as { ok: false, error, hint } so one dead key does not
 * hide the other opinion.
 */
async function compare(names, prompt, options = {}) {
  const list = names && names.length ? names : providers.names();
  const results = await Promise.all(
    list.map(async (name) => {
      try {
        const r = await ask(name, prompt, options);
        return { ok: true, ...r };
      } catch (err) {
        const p = (() => {
          try {
            return providers.get(name);
          } catch {
            return { id: name, label: name };
          }
        })();
        return {
          ok: false,
          provider: p.id,
          label: p.label,
          error: err.message,
          hint: err.hint || null,
        };
      }
    })
  );
  return results;
}

/**
 * Connectivity and credential report for every provider. Transport reachability
 * is checked even without a key: a 401 proves the network path works.
 */
async function status() {
  const out = [];
  for (const name of providers.names()) {
    const p = providers.get(name);
    const key = providers.apiKey(p);
    const entry = {
      provider: p.id,
      label: p.label,
      baseUrl: p.baseUrl,
      keyEnv: p.keyEnv[0],
      keyPresent: Boolean(key),
      reachable: false,
      authenticated: false,
      model: null,
      detail: null,
    };

    try {
      const res = await request(`${p.baseUrl}/models`, {
        headers: key ? { Authorization: `Bearer ${key}` } : {},
        timeoutMs: 30000,
      });
      entry.reachable = true;
      if (res.status === 200) {
        entry.authenticated = true;
        try {
          entry.model = await resolveModel(name);
        } catch {
          entry.model = null;
        }
        const models = res.json && Array.isArray(res.json.data) ? res.json.data.length : 0;
        entry.detail = `${models} models visible`;
      } else if (res.status === 401 || res.status === 403) {
        entry.detail = key
          ? `key rejected (HTTP ${res.status})`
          : `endpoint reachable, no credentials (HTTP ${res.status})`;
      } else {
        entry.detail = `HTTP ${res.status}: ${res.text.slice(0, 160)}`;
      }
    } catch (err) {
      entry.detail = `unreachable: ${err.message}`;
    }

    out.push(entry);
  }
  return out;
}

module.exports = { ask, compare, status, listModels, resolveModel, CouncilError };
