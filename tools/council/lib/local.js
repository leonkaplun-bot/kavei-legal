'use strict';

// Local-CLI transport: drive an already-installed `codex` / `grok` binary
// instead of calling a vendor API. No keys — the CLI carries its own auth.
//
// This only works where the binaries exist, i.e. a Claude Code session running
// on the machine that has them. A cloud session cannot reach them.
//
// Invocation syntax differs between builds and versions, so nothing is assumed:
// candidate argument patterns are probed once and the first working one is
// cached. An explicit override always wins.

const { spawn } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const PROBE_PROMPT = 'Reply with exactly: OK';
const PROBE_TIMEOUT_MS = 90000;

// Ordered by how current each form is; `{prompt}` is substituted at call time.
const CANDIDATES = {
  codex: [
    ['exec', '--skip-git-repo-check', '{prompt}'],
    ['exec', '{prompt}'],
    ['-q', '{prompt}'],
    ['{prompt}'],
  ],
  grok: [
    ['-p', '{prompt}'],
    ['--prompt', '{prompt}'],
    ['exec', '{prompt}'],
    ['-q', '{prompt}'],
    ['{prompt}'],
  ],
};

const DEFAULT_BIN = { codex: 'codex', grok: 'grok' };

function configFile() {
  return path.join(os.homedir(), '.council-local.json');
}

function readConfig() {
  try {
    return JSON.parse(fs.readFileSync(configFile(), 'utf8'));
  } catch {
    return {};
  }
}

function writeConfig(cfg) {
  try {
    fs.writeFileSync(configFile(), JSON.stringify(cfg, null, 2));
  } catch {
    /* unwritable home just means we re-probe next time */
  }
}

function binFor(provider) {
  const env = process.env[`COUNCIL_${provider.toUpperCase()}_BIN`];
  if (env && env.trim()) return env.trim();
  const cfg = readConfig();
  if (cfg[provider] && cfg[provider].bin) return cfg[provider].bin;
  return DEFAULT_BIN[provider] || provider;
}

/** Argument pattern pinned by env or config, if any. */
function pinnedArgs(provider) {
  const env = process.env[`COUNCIL_${provider.toUpperCase()}_ARGS`];
  if (env && env.trim()) {
    // Space-separated; must contain the {prompt} placeholder.
    const parts = env.trim().split(/\s+/);
    if (parts.includes('{prompt}')) return parts;
  }
  const cfg = readConfig();
  if (cfg[provider] && Array.isArray(cfg[provider].args)) return cfg[provider].args;
  return null;
}

// Directories these CLIs commonly install into but do not always add to PATH,
// searched after PATH itself.
function fallbackDirs(bin) {
  const home = os.homedir();
  const dirs = [path.join(home, `.${bin}`, 'bin'), path.join(home, '.local', 'bin')];
  if (process.platform === 'win32') {
    const appData = process.env.APPDATA || path.join(home, 'AppData', 'Roaming');
    dirs.push(path.join(appData, 'npm'), path.join(home, `.${bin}`));
  }
  return dirs;
}

function which(bin) {
  const dirs = (process.env.PATH || '').split(path.delimiter).filter(Boolean);
  dirs.push(...fallbackDirs(bin));
  const exts = process.platform === 'win32' ? ['.exe', '.cmd', '.bat', ''] : [''];
  if (bin.includes(path.sep)) {
    try {
      fs.accessSync(bin, fs.constants.X_OK);
      return bin;
    } catch {
      return null;
    }
  }
  for (const dir of dirs) {
    for (const ext of exts) {
      const full = path.join(dir, bin + ext);
      try {
        fs.accessSync(full, fs.constants.X_OK);
        return full;
      } catch {
        /* keep looking */
      }
    }
  }
  return null;
}

const IS_WIN = process.platform === 'win32';

// npm installs CLIs on Windows as .cmd shims, and since Node 18.20 spawning one
// directly throws EINVAL. Route those through cmd.exe with a hand-built,
// verbatim command line — Node's `shell: true` joins argv without quoting, so
// it mangles any argument containing a space.
function quoteForCmd(value) {
  return '"' + String(value).replace(/"/g, '\\"') + '"';
}

function spawnTarget(bin, args) {
  if (!IS_WIN || !/\.(cmd|bat)$/i.test(bin)) {
    return { command: bin, argv: args, extra: {} };
  }
  const line = [bin, ...args].map(quoteForCmd).join(' ');
  return {
    command: process.env.ComSpec || 'cmd.exe',
    argv: ['/d', '/s', '/c', `"${line}"`],
    extra: { windowsVerbatimArguments: true },
  };
}

function run(bin, args, { timeoutMs = 300000, cwd = process.cwd() } = {}) {
  return new Promise((resolve) => {
    const target = spawnTarget(bin, args);
    let child;
    try {
      child = spawn(target.command, target.argv, {
        cwd,
        env: process.env,
        stdio: ['ignore', 'pipe', 'pipe'],
        ...target.extra,
      });
    } catch (err) {
      resolve({ code: -1, stdout: '', stderr: err.message, timedOut: false });
      return;
    }

    let stdout = '';
    let stderr = '';
    let timedOut = false;

    const timer = setTimeout(() => {
      timedOut = true;
      child.kill('SIGKILL');
    }, timeoutMs);

    child.stdout.on('data', (d) => {
      stdout += d;
    });
    child.stderr.on('data', (d) => {
      stderr += d;
    });
    child.on('error', (err) => {
      clearTimeout(timer);
      resolve({ code: -1, stdout, stderr: stderr || err.message, timedOut });
    });
    child.on('close', (code) => {
      clearTimeout(timer);
      resolve({ code, stdout, stderr, timedOut });
    });
  });
}

function fill(pattern, prompt) {
  return pattern.map((a) => a.replace('{prompt}', prompt));
}

/** Is the binary present on this machine? */
function available(provider) {
  return Boolean(which(binFor(provider)));
}

/**
 * Find a working argument pattern, caching the result. Returns the pattern or
 * null when every candidate failed.
 */
async function resolveArgs(provider, { force = false } = {}) {
  const pinned = pinnedArgs(provider);
  if (pinned && !force) return pinned;

  const bin = binFor(provider);
  // Probe the resolved path, not the bare name: the binary may live in a
  // fallback directory that is not on PATH, where spawn would not find it.
  const resolved = which(bin);
  if (!resolved) return null;

  for (const pattern of CANDIDATES[provider] || []) {
    const res = await run(resolved, fill(pattern, PROBE_PROMPT), { timeoutMs: PROBE_TIMEOUT_MS });
    if (res.code === 0 && res.stdout.trim()) {
      const cfg = readConfig();
      cfg[provider] = { ...(cfg[provider] || {}), bin, args: pattern };
      writeConfig(cfg);
      return pattern;
    }
  }
  return null;
}

/** Ask a locally installed CLI. Throws with an actionable message on failure. */
async function ask(provider, prompt, { system, timeoutMs = 300000, cwd } = {}) {
  const bin = binFor(provider);
  const resolvedBin = which(bin);
  if (!resolvedBin) {
    const err = new Error(`${provider}: "${bin}" is not installed on this machine`);
    err.hint = `Install it, or point COUNCIL_${provider.toUpperCase()}_BIN at the executable. A cloud session cannot see binaries installed on your own computer.`;
    throw err;
  }

  const args = await resolveArgs(provider);
  if (!args) {
    const err = new Error(`${provider}: found "${resolvedBin}" but no known way to run it non-interactively`);
    err.hint = `Pin the invocation with COUNCIL_${provider.toUpperCase()}_ARGS (must include {prompt}), e.g. COUNCIL_${provider.toUpperCase()}_ARGS="exec {prompt}".`;
    throw err;
  }

  const full = system ? `${system}\n\n${prompt}` : prompt;
  const started = Date.now();
  const res = await run(resolvedBin, fill(args, full), { timeoutMs, cwd });

  if (res.timedOut) {
    const err = new Error(`${provider}: local CLI timed out after ${Math.round(timeoutMs / 1000)}s`);
    err.hint = 'Raise --timeout, or shorten the prompt.';
    throw err;
  }
  if (res.code !== 0) {
    const err = new Error(
      `${provider}: local CLI exited ${res.code} — ${(res.stderr || res.stdout).trim().slice(0, 400)}`
    );
    err.hint = `Check the CLI is signed in by running "${bin}" once yourself.`;
    throw err;
  }

  return {
    provider,
    transport: 'local-cli',
    model: `${path.basename(resolvedBin)} (local CLI)`,
    text: res.stdout.trim(),
    usage: null,
    ms: Date.now() - started,
  };
}

module.exports = { available, ask, resolveArgs, binFor, which, configFile, CANDIDATES };
