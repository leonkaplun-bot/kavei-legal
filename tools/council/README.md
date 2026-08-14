# Council — Grok + Codex advisory bridge

A dependency-free bridge that lets Claude consult **Grok (xAI)** and **Codex
(OpenAI)** for independent opinions, or have the same task solved twice and
compared. Claude directs; these two advise.

Nothing to install. Node 18+ (this environment has v22) and a network path are
all it needs — the client is hand-rolled against `node:https` because Node's
global `fetch` ignores `HTTPS_PROXY`, which this environment requires.

## Windows one-shot setup

`setup-windows.cmd` in the repository root does the whole local setup: clones or
updates the repo under `%USERPROFILE%`, installs Claude Code and Codex if
missing, locates the CLIs, runs the connectivity check, and launches Claude Code
in the repo. It is a `.cmd`, so the PowerShell execution policy never applies,
and it is safe to run repeatedly — every step checks before acting.

Double-click it, or from `cmd`:

```
curl -L -o "%USERPROFILE%\council-setup.cmd" https://raw.githubusercontent.com/leonkaplun-bot/kavei-legal/claude/grok-codex-integration-ezmmc9/setup-windows.cmd && "%USERPROFILE%\council-setup.cmd"
```

## Two transports

Chosen automatically per provider; `council status` shows which one is active.

### 1. Local CLI — preferred, no API key

If `codex` / `grok` are installed on the machine running the session, the
council runs those binaries directly. They use their own existing login, and
they can see the repository, so answers are grounded in the actual code.

**This requires a session on that machine** — the Claude Code CLI or desktop
app, opened in this repo. A browser session at claude.ai/code runs in a cloud
VM with no path to your computer, so it can never see locally installed tools.

Nothing to configure. The invocation form differs between CLI builds, so it is
probed once against a set of known patterns and the winner is cached in
`~/.council-local.json`. Overrides, if a build is unusual:

```bash
COUNCIL_CODEX_BIN=/opt/codex/bin/codex     # non-standard install path
COUNCIL_GROK_ARGS="--prompt {prompt}"      # pin the argument form
```

On Windows, npm installs these CLIs as `.cmd` shims, which Node refuses to
spawn directly since 18.20. Those are routed through `cmd.exe` with a verbatim,
hand-quoted command line. A native `.exe` is preferred when both exist, since it
skips the shell entirely. Known limit of the `.cmd` route: `cmd.exe` command
lines cannot carry literal newlines or `%VAR%` sequences intact, so very large
multi-line prompts are better piped to the CLI directly than sent through the
council.

### 2. Vendor API — fallback

Used when no local binary is found.

| Provider | Environment variable | Where to get a key |
| --- | --- | --- |
| Grok (xAI) | `XAI_API_KEY` | <https://console.x.ai> |
| Codex (OpenAI) | `OPENAI_API_KEY` | <https://platform.openai.com/api-keys> |

Set these as **environment variables on the Claude Code environment**
(claude.ai/code → environment settings → environment variables), not with
`export` inside a session. The container is ephemeral and is rebuilt from a
fresh clone each time; only environment-level variables survive that.

### Verify either way

```bash
node tools/council/bin/council.js status
```

`READY` on both lines means every new chat can use the council immediately.
`COUNCIL_MODE=local|api|auto` forces a transport instead of auto-selecting.

## Usage

### From Claude (MCP tools)

`.mcp.json` registers this server, so `council_status`, `ask_grok`, `ask_codex`,
`council_compare`, and `council_models` appear as native tools in every session
with no connection procedure.

### From the shell

```bash
council status                                  # connectivity + credentials
council models grok                             # what this account can use
council ask codex "Why does this test flake?"   # one provider
council compare "Which approach is safer?"      # both, in parallel

council compare "Review for GDPR gaps" --file privacy.html
git diff | council compare "Find correctness bugs in this diff"
```

Options: `--system <text>`, `--file <path>` (repeatable), `--model <id>`,
`--only grok,codex`, `--timeout <sec>`, `--json`.

Prompt text is assembled from the positional argument, any `--file` contents,
and stdin — so large context can be piped instead of quoted.

## Model selection

Model IDs are not pinned in code. Resolution order per provider:

1. `--model` / the MCP `model` argument
2. `XAI_MODEL` / `OPENAI_MODEL`
3. the first entry of the provider's preference list that its own `/v1/models`
   actually reports (cached for an hour)

So the setup keeps working when a vendor renames or retires a model. To pin one
deliberately, set the env var.

## Layout

```
tools/council/
  lib/http.js       CONNECT-tunnelling HTTPS client, trusts the proxy CA bundle
  lib/providers.js  endpoints, key env vars, model preference lists
  lib/local.js      local-CLI transport: binary discovery, invocation probing
  lib/council.js    transport selection, ask / compare / status
  bin/council.js    CLI
  mcp-server.js     MCP stdio server (JSON-RPC over stdin/stdout)
```

Both providers speak the OpenAI-compatible `/v1/chat/completions` shape, so one
request path serves both. Payloads stay minimal — no `temperature`, no
`max_tokens` — because reasoning models reject those, and omitting them keeps a
single code path valid across every model either vendor offers.

## Failure modes

| Symptom | Cause | Fix |
| --- | --- | --- |
| falls back to API although the CLI is installed | session is running elsewhere (e.g. in the browser), or the binary is not on `PATH` | run the session on that machine, or set `COUNCIL_<PROVIDER>_BIN` |
| `no known way to run it non-interactively` | unusual CLI build | pin `COUNCIL_<PROVIDER>_ARGS`, must contain `{prompt}` |
| local CLI exits non-zero | CLI not signed in | run the binary once by hand and complete its login |
| `NOT READY`, HTTP 401 | no key in the environment | set the variable above at environment level |
| `key rejected` | wrong or revoked key | reissue in the provider console |
| HTTP 404 on a model | model not available to the account | `council models <provider>`, then set `XAI_MODEL` / `OPENAI_MODEL` |
| `proxy CONNECT … 403/407` | egress policy blocks the host | report it; do not route around the proxy |

A failing provider in `compare` is reported inline and never aborts the other.
