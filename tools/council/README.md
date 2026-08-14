# Council — Grok + Codex advisory bridge

A dependency-free bridge that lets Claude consult **Grok (xAI)** and **Codex
(OpenAI)** for independent opinions, or have the same task solved twice and
compared. Claude directs; these two advise.

Nothing to install. Node 18+ (this environment has v22) and a network path are
all it needs — the client is hand-rolled against `node:https` because Node's
global `fetch` ignores `HTTPS_PROXY`, which this environment requires.

## Setup

One step, done once per environment:

| Provider | Environment variable | Where to get a key |
| --- | --- | --- |
| Grok (xAI) | `XAI_API_KEY` | <https://console.x.ai> |
| Codex (OpenAI) | `OPENAI_API_KEY` | <https://platform.openai.com/api-keys> |

Set these as **environment variables on the Claude Code environment**
(claude.ai/code → environment settings → environment variables), not with
`export` inside a session. The container is ephemeral and is rebuilt from a
fresh clone each time; only environment-level variables survive that.

Verify:

```bash
node tools/council/bin/council.js status
```

`READY` on both lines means every new chat can use the council immediately.

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
  lib/council.js    ask / compare / status / model resolution
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
| `NO KEY`, HTTP 401 | no key in the environment | set the variable above at environment level |
| `key rejected` | wrong or revoked key | reissue in the provider console |
| HTTP 404 on a model | model not available to the account | `council models <provider>`, then set `XAI_MODEL` / `OPENAI_MODEL` |
| `proxy CONNECT … 403/407` | egress policy blocks the host | report it; do not route around the proxy |

A failing provider in `compare` is reported inline and never aborts the other.
