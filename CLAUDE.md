# kavei-legal

Static legal and support pages for the Kavei iOS app: `index.html`, `privacy.html`,
`support.html`. No build step — the files are served as-is.

## Advisory council: Grok and Codex

This repo ships a standing connection to two external models so they can be
consulted for independent opinions. **Claude is the director**: Claude decides
what to ask, judges the answers, and owns the final result. Grok and Codex are
consultants — their output is input to a decision, never the decision itself,
and it is never applied to the repo unverified.

### How to reach them

Native MCP tools (registered in `.mcp.json`, available automatically in every
session, no setup):

| Tool | Use |
| --- | --- |
| `council_status` | Are both providers reachable and authenticated? Run this first when anything fails. |
| `ask_grok` | One question to Grok (xAI). |
| `ask_codex` | One question to Codex (OpenAI). |
| `council_compare` | Same question to both, in parallel, answers side by side. |
| `council_models` | Model IDs the account can actually use. |

Equivalent CLI, for piping large context or scripting:

```bash
node tools/council/bin/council.js status
node tools/council/bin/council.js ask grok "Is this clause enforceable in the EU?"
node tools/council/bin/council.js compare "Review this approach" --file privacy.html
git diff | node tools/council/bin/council.js compare "Review this diff for correctness bugs"
```

### When to consult

Reach for the council on judgement calls with real cost to getting them wrong:
architectural choices, security- or compliance-sensitive wording, a risky diff,
a bug that resists one line of reasoning. Use `council_compare` when independent
opinions matter, and `ask_grok` / `ask_codex` when one specialist is enough.

Skip it for mechanical work. A rename does not need a committee.

### Rules

1. Each provider sees only the prompt sent to it — it has no repo access and no
   memory of previous turns. Include every piece of context the question needs.
2. Never paste secrets, API keys, or private user data into a prompt.
3. Verify before adopting. Confident and wrong is a normal failure mode; check
   claims against the actual code before acting on them.
4. When the council's advice changes the outcome, say so in the reply and
   attribute it — the user should know which opinion drove which decision.
5. A provider without a key fails loudly and in isolation. One dead key never
   blocks the other opinion, and never blocks the task.

### Credentials

Keys are read from the environment: `XAI_API_KEY` for Grok, `OPENAI_API_KEY`
for Codex. Set them on the Claude Code **environment** (not with `export` in a
session) so they survive container restarts and are present in every new chat.
Setup details are in `tools/council/README.md`.
