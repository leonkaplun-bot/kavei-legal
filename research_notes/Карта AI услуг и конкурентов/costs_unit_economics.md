# Cost stack and unit economics for a one-person AI services studio (Leon Kaplun / leonaii.com), as of 8 Nov 2026

All prices were seen on 2026-11-08 unless a different date is given. Prices are USD excluding tax unless stated otherwise.
**FX rate used: 1 USD = ₪3.17.** fxfeed.io quoted 3.1663 for 2026-11-08, and its daily quotes for 1–8 Nov 2026 ran from 3.133 to 3.199 ([fxfeed](https://fxfeed.io/currencies/pairs/usd-ils)). I could not confirm the Bank of Israel representative rate for November 2026, so treat ₪ figures as ±2%.
Notation: "MTok" means one million tokens. "Official" means the vendor's own pricing page or docs. "3rd-party" means an aggregator or blog, which is flagged as unconfirmed.

---

## Q1. Current prices of the core AI vendors (Anthropic, OpenAI, Google, xAI): API and subscription plans

### Takeaway
At the API level, mid-tier "workhorse" models from all four vendors now cost about $1–2 per MTok of input and $5–10 per MTok of output: Claude Sonnet 5.5 is $2/$10, GPT-6.1-sol is $2/$10, Gemini 4 Argon is $2/$10, and grok-4.3 is $1.25/$2.50. The cheap tier (Claude Haiku 5.5, GPT-6-luna, Gemini 3.5 Flash-Lite) costs $0.10–0.30 per MTok of input, which makes chat-style AI cost almost negligible per conversation. On the subscription side, every vendor now sells a ~$20 entry plan, a ~$100 plan and a ~$200 plan. The coding agents (Claude Code, Codex, Antigravity) come bundled into those consumer plans, but their usage limits are opaque and change often.

### Cited Findings

**Anthropic, consumer and Team plans** (official, [claude.com/pricing](https://claude.com/pricing))

| Plan | USD | ₪ (×3.17) | Notes |
|---|---|---|---|
| Free | $0 | ₪0 | No Claude Code |
| Pro | $20/mo monthly, or $17/mo on annual billing ($200/yr) | ₪63 / ₪54 | "1x usage every 5 hours and weekly"; includes Claude Code |
| Max (5x) | $100/mo | ₪317 | 5x Pro usage; includes Claude Code. The page also says "$100/month in API credits" (verify in the account before relying on it) |
| Ultra | $200/mo | ₪634 | "10x Pro usage weekly, no 5-hour limit for verified accounts"; the page says it includes "$200/month in API credits" (verify) |
| Team standard seat | $25/seat monthly, $20/seat annual | ₪79 / ₪63 | Includes Claude Code |
| Team premium seat | $125 monthly, $100 annual | ₪396 / ₪317 | 5x a standard seat; the page says Teams get "up to $500/month pooled API credits" |
| Enterprise | $20/seat annual, 20-seat minimum, plus usage at API rates | — | |

- Claude.com pricing states that "Price and plans are subject to change at Anthropic's discretion" — [claude.com/pricing](https://claude.com/pricing)

**Anthropic API, per MTok** (official, [platform.claude.com pricing docs](https://platform.claude.com/docs/en/about-claude/pricing); matches [claude.com/pricing](https://claude.com/pricing))

| Model | Input | 5-min cache write | 1-h cache write | Cache hit | Output | Batch in/out |
|---|---|---|---|---|---|---|
| Claude Fable 5.1 | $10 | $12.50 | $20 | $0.25 | $50 | n/a captured |
| Claude Opus 5.5 | $4 | $5 | $8 | $0.20 | $20 | $2 / $10 |
| Claude Sonnet 5.5 | $2 | $2.50 | $4 | $0.10 | $10 | $1 / $5 |
| Claude Haiku 5.5 (prompt ≤100K tokens) | $0.10 | $0.125 | $0.20 | $0.01 | $0.50 | $0.05 / $0.25 |
| Claude Haiku 5.5 (prompt >100K tokens) | $0.50 | $0.625 | $1 | $0.05 | $2.50 | $0.25 / $1.25 |

- The Batch API gives 50% off input and output. Batch and caching discounts stack — [Claude pricing docs](https://platform.claude.com/docs/en/about-claude/pricing)
- Opus 5.5 fast mode costs $8/$40 per MTok, twice standard. US-only inference (`inference_geo`) is a 1.1x multiplier — [Claude pricing docs](https://platform.claude.com/docs/en/about-claude/pricing)
- Claude 4.6 and later models, except Haiku 5.5, include the 1M-token context window at standard pricing. Haiku 5.5 charges 5x for prompts over 100K tokens — [Claude pricing docs](https://platform.claude.com/docs/en/about-claude/pricing)
- The web search tool costs $10 per 1,000 searches plus tokens. Web fetch costs nothing beyond tokens. Code execution is free when used with web search or web fetch — [Claude pricing docs](https://platform.claude.com/docs/en/about-claude/pricing)
- Vision: an image costs ⌈width/28⌉×⌈height/28⌉ visual tokens. Claude 4.7 and later run at a "high-resolution" tier with a maximum long edge of 2,576 px and at most 4,784 tokens per image. The docs' own example puts a 4K image on Opus 5.5 at about $19.14 per 1,000 images — [Claude vision docs](https://platform.claude.com/docs/en/build-with-claude/vision)

**OpenAI API, per MTok** (official, [developers.openai.com/api/docs/pricing](https://developers.openai.com/api/docs/pricing); openai.com/api/pricing returned HTTP 403)

| Model | Input | Cached input | Output |
|---|---|---|---|
| gpt-6-astra (top) | $10 | $1.00 | $50 |
| gpt-6.1-sol | $2 | $0.10 | $10 |
| gpt-6.1-terra | $1 | $0.05 | $5 |
| gpt-6-luna | $0.10 | $0.01 | $0.50 |
| gpt-5.6-sol / terra / luna | $4 / $2 / $0.20 | $0.40 / $0.20 / $0.02 | $20 / $12 / $1.20 |
| gpt-5.5 | $5 | $0.50 | $30 |
| gpt-5.4 / gpt-5.4-mini / nano | $2.50 / $0.75 / $0.20 | $0.25 / $0.075 / $0.02 | $15 / $4.50 / $1.25 |
| gpt-5.3-codex | $1.75 | $0.175 | $14 |
| gpt-realtime-2.1 (audio) | $32 | $0.40 | $64 |
| gpt-realtime-2.1-mini (audio) | $10 | $0.30 | $20 |

- GPT-Live (gpt-live-1) costs $0.05/min, billed per second, with the backend model billed separately. Transcription: gpt-transcribe $0.0045/min; gpt-4o-mini-transcribe $0.003/min. TTS: tts-1 $15 per 1M characters — [OpenAI pricing](https://developers.openai.com/api/docs/pricing)
- gpt-image-2 costs $8 per MTok of image input and $30 per MTok of image output. The page publishes no per-image price — [OpenAI pricing](https://developers.openai.com/api/docs/pricing)
- Web search costs $10 per 1k calls plus content tokens. Batch and Flex run about 50% of Standard. "Priority processing was renamed Fast mode on July 30, 2026". Input over 272K tokens is billed at higher rates — [OpenAI pricing](https://developers.openai.com/api/docs/pricing)
- **The Sora 2 and Sora 2 Pro API was shut down on 24 Sep 2026, and there is "no one-to-one replacement API".** Its former prices were $0.10/s at 720p and $0.30–0.70/s for Pro — [OpenAI Sora 2 model page](https://developers.openai.com/api/docs/models/sora-2)

**ChatGPT / Codex plans**
- The official page lists Free, Go, Plus, Pro, Business and Enterprise. Codex is "included" from Plus up, and Pro gets "Longer Codex... sessions". Business starts at 2 users. **The price figures did not render in the fetch** — [chatgpt.com/pricing](https://chatgpt.com/pricing)
- 3rd-party, unconfirmed: Plus $20/mo; Business $25/seat monthly or $20/seat annual with a 2-seat minimum (benchlm, as of 16 Oct 2026); Go about $8. Pro is quoted as $100 and $200 tiers; one source also lists a $500 tier, so the sources conflict — [benchlm](https://benchlm.ai/md/chatgpt/pricing-plans.md), [gptprompts](https://gptprompts.ai/ai-pricing/chatgpt-pricing), [krater](https://krater.ai/blog/chatgpt-pricing)

**Google Gemini API, per MTok, paid Standard tier** (official, [aistudio.google.com/docs/pricing](https://aistudio.google.com/docs/pricing), which ai.google.dev now redirects to)

| Model | Input | Output | Cache |
|---|---|---|---|
| Gemini 4 Argon | $2.00 | $10.00 | $0.10 (**"doubles Dec 1, 2026"**) |
| Gemini 3.8 Flash / 3.6 Flash | $0.75 | $3.75 | $0.075 + storage |
| Gemini 3.5 Flash-Lite | $0.30 | $2.50 | $0.03 |
| Gemini 3.1 Pro Preview | $2 (≤200k) / $4 | $12 / $18 | — |
| Gemini 2.5 Flash-Lite | $0.10 | $0.40 | $0.01 |

- A free tier exists for Gemini 3.8 Flash, 3.6 Flash, 3.5 Flash-Lite, 2.5 Pro/Flash, the 3.8 TTS models, Gemini 3.8 Live and Gemma 4. Gemini 4 Argon and the image models are paid only — [Gemini pricing](https://aistudio.google.com/docs/pricing)
- Gemini 3.8 Live audio costs about $0.005/min in and $0.018/min out — [Gemini pricing](https://aistudio.google.com/docs/pricing)
- Image models: Nano Banana 2.1 $0.0336 (1K) / $0.0504 (2K) / $0.113 (4K); Nano Banana Pro $0.134 (1K/2K) / $0.24 (4K) — [Gemini pricing](https://aistudio.google.com/docs/pricing)
- Video, Gemini Omni 1.2 Flash: about $0.07/s at 720p, $0.104/s at 1080p (upsampled) and $0.209/s at 4K. Omni 1.1 Flash requests "route to 1.2 on December 3, 2026". **The page lists no Veo prices** — [Gemini pricing](https://aistudio.google.com/docs/pricing)
- Grounding with Google Search on Gemini 3+: 5,000 free requests per month, then $14 per 1,000 — [Gemini pricing](https://aistudio.google.com/docs/pricing)
- "Prices for many models change on December 1, 2026 or January 1, 2027" — [Gemini pricing](https://aistudio.google.com/docs/pricing)
- 3rd-party: the Veo 3.1 preview models on the Gemini API were reportedly shut down on 22 Oct 2026 and replaced by Gemini Omni Flash. The last tracked Veo 3.1 price was about $0.40/s at 720p/1080p and $0.60/s at 4K — [search summary citing benchlm/useapi](https://benchlm.ai/media-pricing/veo) (unconfirmed)

**Google AI plans and Antigravity**
- Google AI Pro costs $19.99/mo or $199.99/yr and includes 1,000 Flow credits/mo, "expanded" Antigravity access with Gemini 4 Argon, and 5 TB of storage. Google AI Ultra is "from $99.99/mo" and comes in 5x and 20x tiers (10,000 or 25,000 Flow credits); the 20x price did not render. Google AI Plus also exists, price not shown — [Google AI plans](https://one.google.com/about/google-ai-plans/)
- Antigravity: an Individual plan at $0 with "basic weekly rate limits"; the Google AI Pro and Ultra tiers add higher limits and a "flexible AI credit pool"; the business tier via Gemini Enterprise starts at $30/seat/mo, or pay-as-you-go — [antigravity.google/pricing](https://antigravity.google/pricing)
- Google's 19 May 2026 change: Pro $20; a new Ultra $100 with 5x Pro's token rate limit; the top Ultra cut "from $250 to $200/month" with 20x. Flash and Pro now share one rate limit "drawn down according to API pricing", and AI credits now act only as overage — [Antigravity blog](https://www.antigravity.google/blog/changes-to-antigravity-plans)
- Users protested in March 2026 about Antigravity's effective price "floating upward" — [The Register](https://www.theregister.com/2026/03/12/users_protest_as_google_antigravity/) (headline only, not fetched)

**xAI Grok**
- API prices per MTok: grok-4.7 $2 input / $0.50 cached / $6 output (≤200k context; doubled above that); grok-4.3 $1.25 / $0.20 / $2.50 with a 1M context; grok-build-0.1 $1 / $2 — [docs.x.ai/docs/models](https://docs.x.ai/docs/models)
- Grok Imagine images cost $0.02–0.04 each. Grok Imagine video costs $0.02/s (1.5-lite), $0.05/s, or $0.08/s (1.5) — [xAI docs](https://docs.x.ai/docs/models)
- Grok Voice API: speech-to-speech (grok-voice-3.0) $0.08/min ($4.80/hr); STT $0.10/hr (REST); TTS $15 per 1M characters — [xAI docs](https://docs.x.ai/docs/models)
- Consumer plans, 3rd-party and unconfirmed (x.ai/pricing returned HTTP 403 and grok.com/plans did not render): since 12 Oct 2026 Grok is sold through "The X Subscription" at Plus $8, Premium $30, Super $100 and Ultra $200 per month ($80/$300/$1,000/$2,000 per year). The old SuperGrok tiers ($10/$30/$100/$300 Heavy) are closed to new subscribers — [ai-toolbox.co](https://ai-toolbox.co/grok-models/grok-pricing-plans-api-2026), [usagepricing](https://www.usagepricing.com/blueprint/activity/grok-2026-10-15-supergrok-x-subscription)

### Inferences
- For client-facing bots such as WhatsApp, lead qualification and FAQ, Haiku 5.5 ($0.10/$0.50) or Gemini 3.5 Flash-Lite is the margin-safe default. Sonnet 5.5, GPT-6.1-sol or Gemini 4 Argon should be reserved for reasoning-heavy work: drawings, consulting deliverables and long-form content.
- Claude Code, Codex and Antigravity subscriptions are Leon's *own production tools* (fixed cost). They are not a way to serve clients, because consumer-plan usage limits are per person and cannot be resold. Client-facing automations should run on API keys billed per token.
- Newer models are not automatically cheaper. On OpenAI, gpt-5.5 ($5/$30) costs more than gpt-6.1-sol ($2/$10), so pin model IDs in production and review them quarterly.

### Gaps
- I could not render official ChatGPT plan prices (chatgpt.com showed no figures; openai.com and help.openai.com returned 403). Plus, Pro and Business prices are 3rd-party.
- I could not reach official xAI consumer plan pages (403 / empty render). X Subscription prices are 3rd-party.
- The Google AI Ultra 20x price did not render (3rd-party sources and Google's May blog imply $200). The Google AI Plus price is not shown.
- The claim that Claude Max/Ultra include monthly API credits comes from a fetched summary of claude.com/pricing and should be checked in the console.
- Hebrew tokenization overhead (tokens per word compared with English) was not researched. Hebrew text likely costs more tokens per word, so the token estimates below may be low for Hebrew output.

---

## Q2. Prices of supporting tools (messaging, voice, telephony, video, music, images, automation, hosting, SEO, CRM)

### Takeaway
The variable costs that actually matter are voice minutes, WhatsApp marketing templates and video seconds. Voice runs about $0.09–0.21 per minute all-in before Israeli telephony extras. WhatsApp marketing templates cost about $0.035 each in Israel. Video costs $0.02–0.40 per generated second depending on model. Everything else (automation, hosting, SEO suites) is a fixed monthly subscription between $10 and $450.

### Cited Findings

**WhatsApp Business Platform (Meta)**
- Since 1 Jul 2025 Meta charges per *delivered* template message by category and market. Israel (+972) is a standalone rate market — [Meta dev docs](https://developers.facebook.com/docs/whatsapp/pricing)
- **From 1 Oct 2026, service messages are charged again.** Each business phone number gets "one free tier of 1,000 delivered service messages per month", with no rollover, and charging starts at the 1,001st — [Meta docs](https://developers.facebook.com/documentation/business-messaging/whatsapp/pricing). **Conflict:** the marketing site still says "we do not charge for service messages, or for utility messages businesses send in response to users" — [whatsappbusiness.com](https://whatsappbusiness.com/products/platform-pricing/). Treat the developer docs as authoritative and the marketing page as stale.
- Free entry points: replies to users who come from Click-to-WhatsApp ads open a free window of up to 7 days for all categories except Meta Business Agent messages. Meta Business Agent costs $2.00 per 1M tokens, globally — [Meta dev docs](https://developers.facebook.com/docs/whatsapp/pricing)
- **Israel rates, 3rd-party (Meta's CSV/PDF links did not resolve):** marketing about $0.0353, utility and authentication about $0.0053, service after the free tier about $0.0053, effective 1 Oct 2026 — [zernio](https://zernio.com/whatsapp-api-pricing), [nonito](https://www.nonito.io/whatsapp-business-api-pricing), [flowcall](https://www.flowcall.co/blog/whatsapp-business-api-pricing), [usewhapi](https://usewhapi.com/whatsapp-api-pricing/). An older BSP page lists higher rates (marketing $0.05–0.06, utility $0.02), which likely include a reseller markup or predate the change — [edna.io](https://edna.io/pricing-whatsapp-cbp-usd/)

**Voice AI platforms**

| Platform | Price | Source |
|---|---|---|
| Vapi | $0.05/min hosting (pay-as-you-go, $5 free credit). Core plan $29/mo (10 concurrent calls). Pro: 10% of hosting with a $999/mo minimum. Extra concurrency $10/line/mo; HIPAA $2,000/mo. Pass-through costs: Deepgram $0.0095–0.0099/min, OpenAI LLM $0.0077–0.0452/min, ElevenLabs $0.0146–0.0238/min, Twilio $0.008 inbound / $0.014 outbound per minute. Vapi's own all-in estimate is $82–129 per 1,000 min | [vapi.ai/pricing](https://vapi.ai/pricing) |
| Retell AI | Voice infra $0.055/min. LLM per minute: GPT-6.1-terra $0.032, GPT-5.6-terra or Claude 5.5 Sonnet $0.064, Claude 5.5 Haiku $0.0032, Gemini 3.5 Flash $0.048. TTS: $0.015 for platform voices, $0.04 ElevenLabs Flash, $0.06 ElevenLabs Multilingual v2, $0.10 ElevenLabs v3/v4. Telephony $0.015/min "for listed countries (US, UK, India, Canada)", free for SIP/custom. Number $2/mo. 20 concurrent calls free, then $8 each. KB add-on +$0.005/min; batch dial +$0.005; branded caller ID +$0.10/call; QA $0.10/min after 100 free. Speech-to-speech: GPT Realtime 2.1 mini $0.07/min, GPT Realtime 2.1 $0.38/min, Grok Voice 3.0 $0.135/min. Chat agents $0.002–0.02/message. Headline "voice agents $0.07–0.31/min" | [retellai.com/pricing](https://www.retellai.com/pricing) |
| ElevenLabs Agents | $0.08/min, with **$0.16/min "burst" pricing above the concurrency limit**. Included minutes by tier: 15 / 75 / 275 / 1,238 / 3,738 / 12,375. TTS API: v3 or Multilingual v2 $0.08 per 1K characters; Flash/Turbo $0.04. Scribe STT $0.22/hr | [elevenlabs.io/pricing/api](https://elevenlabs.io/pricing/api) |
| xAI Grok Voice | $0.08/min speech-to-speech | [docs.x.ai](https://docs.x.ai/docs/models) |
| OpenAI GPT-Live | $0.05/min plus the backend model | [OpenAI pricing](https://developers.openai.com/api/docs/pricing) |

**Telephony, Twilio Israel** ([twilio.com/en-us/voice/pricing/il](https://www.twilio.com/en-us/voice/pricing/il))
- Numbers: local $5.50/mo (₪17), mobile $15/mo (₪48), toll-free $22/mo (₪70)
- Receiving calls: local $0.0107/min, mobile $0.0350/min, toll-free $0.1344/min. SIP interface or BYOC $0.004/min
- Calls from an Israeli number: to Israeli landlines $0.0294/min, to Israeli mobiles $0.0646/min. Calls to Israeli mobiles from a non-Israeli origin cost $0.1868/min
- The page states no Israeli regulatory or KYC requirements.

**Video generation**
- Runway: Standard $15/mo ($12 annual) for 625 credits; Pro $35 ($28) for 2,250; Max $95 ($76) for 9,500. Gen-4.5 costs 12 credits/s; Aleph 2.0 28 credits/s; Kling 4.0 1080p about 23.6 credits/s; Seedance 2.0 Pro 40 credits/s. Standard and above have no watermark. The page doesn't spell out commercial rights — [runway.com/pricing](https://runway.com/pricing)
- Kling, direct: the official dev pricing page did not render. 3rd-party figures for Kling 3.0 are about $0.075–0.10/s through some resellers and $0.168–0.224/s on fal or WaveSpeed — [search summary: EvoLink / AIReiter](https://aireiter.com/blog/kling-3-api-pricing-guide-2026) (unconfirmed)
- Gemini Omni 1.2 Flash $0.07–0.104/s; Grok Imagine video $0.02–0.08/s (see Q1). The Sora API is shut down (see Q1).

**Music**
- Suno: Free (no commercial use, 50 credits/day); Pro $10/mo ($8 annual) for 2,500 credits/mo, 20 downloads and commercial use; Premier $30/mo ($24 annual) for 10,000 credits and 60 downloads. Subscription credits don't roll over — [suno.com/pricing](https://suno.com/pricing)
- ElevenLabs: music is included with a commercial license on Starter ($6/mo) and above, using 900 credits per generated minute. The music API costs $0.15/min with a 5-minute cap per generation — [elevenlabs.io/pricing](https://elevenlabs.io/pricing), [API pricing](https://elevenlabs.io/pricing/api)
- Udio: 3rd-party sources say Standard $10 and Pro $30, but **commercial rights and downloads are disputed**; downloads were reportedly halted on 29 Oct 2025 — [search summary: dailyaifixs / gptprompts](https://gptprompts.ai/udio-pricing) (unconfirmed; avoid for client deliverables)
- Google AI Pro includes 10,000 Flow Music credits/mo — [Google AI plans](https://one.google.com/about/google-ai-plans/)

**Images**: Nano Banana 2.1 costs $0.034–0.113 per image; Grok Imagine $0.02–0.04; gpt-image-2 is token-priced (see Q1).

**Automation**
- n8n Cloud, annual billing in EUR: Starter €20/mo (2.5K executions), Pro €50 (10K), Business €667 (40K). The Community Edition is self-hosted (no price stated) — [n8n.io/pricing](https://n8n.io/pricing/)
- Make: the official page did not render prices. Free has 1,000 credits. 3rd-party, annual billing for 10,000 credits: Core $9, Pro $16, Teams $29; monthly billing about $10.59 / $18.82 / $34.12 — [make.com/en/pricing](https://www.make.com/en/pricing), [jetadmin](https://www.jetadmin.io/blog/make-pricing/)
- Zapier: Pro $29.99 monthly or $19.99 annual for 750 tasks; 10K tasks $193.50 / $129; Team from $103.50 / $69 for 2K tasks. Agents and Chatbots are add-ons — [zapier.com/pricing](https://zapier.com/pricing)

**Websites and hosting**
- Vercel: Hobby is $0 but "for personal, non-commercial use"; Pro is $20 per developer seat per month with $20 of usage credit and 1 TB of transfer, then from $0.15/GB — [vercel.com/pricing](https://vercel.com/pricing)
- Netlify: Free (300 credits), Personal $9, Pro $20 (unlimited members, 3,000 credits) — [netlify.com/pricing](https://www.netlify.com/pricing/)
- Framer: Basic $10/mo (30 pages, 50 GB); Pro $30/mo (150 pages, 100 GB); extra editors $20/mo, content editors $10/mo — [framer.com/pricing](https://www.framer.com/pricing)
- Shopify: Basic $39 monthly or $29 annual; Grow $105 / $79; Advanced $399 / $299; Plus from $2,300. Online card fees 2.5–2.9% + 30¢ — [shopify.com/pricing](https://www.shopify.com/pricing)
- Webflow: the fetch failed with a header overflow, so prices are not captured.

**SEO tools**
- Ahrefs, monthly: Starter $29; Lite $129 (750 tracked keywords, 150 AI prompt checks); Standard $249; Advanced $449. Brand Radar AI add-on from $199/mo. Annual billing saves up to 17% — [ahrefs.com/pricing](https://ahrefs.com/pricing)
- Semrush: SEO $139 monthly or $117.33 annual; Starter (SEO + AI Search) $199 / $165.17; Pro+ $299 / $248.17 — [semrush.com/prices](https://www.semrush.com/prices/)

**CRM**
- HubSpot: free CRM for up to 2 users and 1,000 contacts. The Starter Customer Platform is $20/seat at standard price, with a new-customer discount of $7 annual or $10 monthly — [hubspot.com/pricing/crm](https://www.hubspot.com/pricing/crm)

### Inferences
- In Israel, Retell's $0.015/min bundled telephony may not apply, since Israel isn't in the listed countries. Assume BYO Twilio via SIP: Retell charges no fee for custom telephony, and Twilio Israel costs $0.0107–0.035/min to receive plus $5.50–15/mo per number.
- WhatsApp cost is dominated by Meta fees, not LLM tokens, once a number passes 1,000 service messages a month or the client sends marketing templates.
- The only realistic API video sources now are Gemini Omni, Grok Imagine, Runway (which resells Kling and Seedance) and Kling. Sora's API is gone and Veo's preview has moved to Omni on the Gemini API.

### Gaps
- I could not confirm the official Meta Israel rate card (the CSV/PDF links did not resolve). The $0.0353 and $0.0053 figures come from aggregators that say they cite Meta.
- I did not verify Hebrew support or quality for Deepgram, Retell's platform voices or Grok Voice. Hebrew may force pricier ElevenLabs Multilingual voices.
- Not captured: Kling official prices, Webflow prices, Make official prices, Pipedrive and monday CRM, BSP fees (e.g., 360dialog), domains, and Twilio Israel number KYC rules.

---

## Q3. Worked examples: cost per delivered unit and gross margin at market prices

### Takeaway
On direct tool and API cost alone, nearly every service clears 80–95% gross margin at typical market prices. The two exceptions are voice agents and WhatsApp bots for high-volume clients, which fall to 40–70% unless usage is capped or passed through. The real constraint is Leon's own hours, so margins should be computed per hour of his time, not only against tool costs.

### Cited Findings (market price benchmarks; mostly vendor or agency blogs, so directional only)
- Website: freelancers typically charge $1,500–5,000 for a small-business site; small agencies $3,000–8,000; Dribbble (Apr 2026) $10,000–20,000 — [search summary: wpzoom / seahawk / levitate](https://www.levitate.ai/blog-posts/average-website-design-cost-for-small-businesses-in-2026)
- SEO content: a common band is $0.15–0.30 per word for quality freelance SEO content, and a 1,500-word post typically sells for $250–399. Surveys are inconsistent, and about half of writers earn under $0.10/word — [search summary: bestwriting / earnifyhub](https://bestwriting.com/content-writing-rates) (low-quality sources)
- Ads management: 10–20% of ad spend with a $500–1,500/mo minimum. For $1k–5k spend, $500–2,000/mo — [OuterBox](https://outerboxdesign.com/articles/paid-media/google-ads-management-agency/ppc-management-pricing-fees), [WebFX](https://www.webfx.com/ppc/pricing/)
- AI video ads: an indie operator charges $50–150 per AI UGC video of 15–45 s; agencies $200–900; tool cost per ad $2–30 — [search summary: oakgen / wireflow / cinerads](https://www.cinerads.com/blog/ai-ugc-cost) (vendor sources)
- Voice agents: setup $1,500–5,000 plus $300–800/mo retainer for a single-purpose agent; other guides say setup $3,000–8,000 and $1,000–3,000/mo; managed services $297–997/mo — [search summary: ciela.ai / trillet / ideaproof](https://ciela.ai/blogs/how-much-to-charge-for-ai-voice-agent). Retell's own estimator default is $0.11/min — [Retell blog, 6 Nov 2026](https://www.retellai.com/blog/how-agencies-price-ai-voice-agents)
- Realistic steady-state gross margin for a managed voice-AI agency is about 50–70% (vendor modelling) — [trillet.ai](https://trillet.ai/blogs/voice-ai-agency-business-model)
- Drawing extraction comparables: Werk24 API charges €0.15/page for metadata/BOM title-block data, €0.85/page for geometry, plus a €490 or €1,490/mo tier fee; OpenDrawing $399–1,499/mo; CAD Crowd $120 for an exploded view and BOM (drafting, not extraction) — [werk24](https://es.werk24.io/product), [Capterra OpenDrawing](https://www.capterra.com/p/10037692/OpenDrawing/), [CAD Crowd](https://www.cadcrowd.com/service/3344-exploded-view-bill-materials)

### Inferences (worked examples; my calculations from the official unit prices in Q1–Q2, with assumptions stated; ₪ at 3.17)

**A. AI WhatsApp / Meta-inbox assistant, per 1,000 conversations**
Assumptions: 6 bot replies per conversation; each turn about 3,000 input tokens (system prompt, knowledge base, history) and 150 output tokens.

| Cost line | Calculation | USD | ₪ |
|---|---|---|---|
| LLM, Claude Haiku 5.5 | 6×(3,000×$0.10 + 150×$0.50)/1M ×1,000 | $2.25 | ₪7 |
| LLM, Claude Sonnet 5.5 with caching (2,500 tokens cached) | — | $16.50 | ₪52 |
| LLM, Sonnet 5.5 uncached | — | $45.00 | ₪143 |
| LLM, GPT-5.4-mini / Gemini 3.8 Flash | — | $17.55 / $16.88 | ₪56 / ₪53 |
| Meta service messages: 6,000, of which 1,000 are free | 5,000×$0.0053 | $26.50 | ₪84 |
| Optional: one marketing follow-up template per conversation | 1,000×$0.0353 | $35.30 | ₪112 |
| **Total (Haiku + Meta)** | | **≈$29** | **≈₪91** |
| **Total (Sonnet cached + Meta + 1 marketing template)** | | **≈$78** | **≈₪248** |

Plus fixed costs of about €20–50/mo for n8n (or a Make/Zapier equivalent). If a ₪1,500/mo retainer (assumed price) covers up to 1,000 conversations, gross margin is about 83–94%. At 5,000 conversations on the same flat fee, cost rises to about ₪520–1,310 (Meta fee: 29,000 billable service messages × $0.0053 ≈ $154) and margin falls to roughly 13–65%. The bot needs a conversation cap or overage pricing. Conversations that start from Click-to-WhatsApp ads are free for 7 days.

**B. AI voice agent / call handling, per hour of talk time**

| Stack | $/min | $/hour | ₪/hour |
|---|---|---|---|
| Vapi low (hosting + Deepgram + cheap LLM + ElevenLabs + Twilio Israel local inbound) | 0.093 | 5.55 | 17.6 |
| xAI Grok Voice 3.0 + Twilio Israel local inbound | 0.091 | 5.44 | 17.3 |
| ElevenLabs Agents + Twilio Israel mobile inbound (LLM extra) | 0.115 | 6.90 | 21.9 |
| Retell budget (infra + GPT-6.1-terra + platform TTS + $0.015 telephony) | 0.117 | 7.02 | 22.3 |
| Vapi high (pricier LLM and voice + Twilio Israel mobile inbound) | 0.164 | 9.83 | 31.2 |
| **Retell "Hebrew-quality"** (infra + GPT-5.6-terra + ElevenLabs Multilingual v2 + Twilio Israel mobile inbound) | **0.214** | **12.84** | **40.7** |
| Retell + GPT Realtime 2.1 speech-to-speech | 0.395 | 23.70 | 75.1 |

Example client at 1,000 min/mo (about 16.7 hours) on the Hebrew-quality stack: cost is $214 in minutes plus a $15 Twilio mobile number, so $229/mo (₪726).

| Retainer (minutes included) | Gross margin |
|---|---|
| $400/mo (₪1,268) | 43% |
| $600/mo (₪1,902) | 62% |
| $800/mo (₪2,536) | 71% |

Add the setup fee ($1,500–5,000 benchmark) as separate revenue. Outbound calling to Israeli mobiles from a non-Israeli number ($0.1868/min) would nearly double the per-minute cost.

**C. 30-second finished AI video ad**
Assumptions: 4x over-generation, so 120 s generated for 30 s used; 20 stills (Nano Banana 2.1 at 2K); 3 music takes from the ElevenLabs music API; a 450-character voice-over (ElevenLabs v2); about $0.50 of LLM script cost. The non-video extras total about $1.77.

| Video engine | Cost per ad, USD | ₪ | GM at $150 | GM at $300 |
|---|---|---|---|---|
| Grok Imagine 1.5-lite ($0.02/s) | ≈$4 | ≈₪13 | 97% | 99% |
| Gemini Omni 1.2 Flash 1080p ($0.104/s) | ≈$14 | ≈₪45 | 90% | 95% |
| Runway Gen-4.5 on the Pro plan (credits ≈ $0.187/s) | ≈$24 | ≈₪77 | 84% | 92% |
| Veo 3.1 at the old 3rd-party $0.40/s | ≈$50 | ≈₪158 | 67% | 83% |

Runway's effective per-second cost drops to about $0.12/s on the Max plan and rises to about $0.29/s on Standard. Suno at $10/mo is an alternative for the music, with commercial use on paid plans.

**D. 1,000-word SEO/GEO article**
Assumptions: about 40K input tokens (sources fetched and research), about 5K output tokens (outline, draft and revision), 5 web searches and 2 images.
- Cost per article: Haiku 5.5 about $0.12; Sonnet 5.5 about $0.25 (₪0.78); Opus 5.5 about $0.38 (₪1.20).
- Amortized SEO suite: Ahrefs Lite $129 or Semrush SEO $139 spread over 20 articles a month adds about $6.50–7 per article.
- All-in tool cost is about $7–8 per article (₪22–25). At market rates of $150–300 per 1,000 words, tool-cost gross margin is about 95–97%. Margin is limited by Leon's editing and fact-checking time.

**E. Engineering drawing to BOM extraction, per sheet**
Assumptions: the sheet is rasterized as one full view plus 4 zoomed tiles, each at the high-resolution cap of 4,784 tokens. Plus a 3,000-token prompt and 2,000 tokens of JSON output, so 26,920 input tokens per sheet.

| Model | Cost per sheet, standard | Batch | Per 1,000 sheets with a second verification pass |
|---|---|---|---|
| Opus 5.5 | $0.148 (₪0.47) | $0.074 | ≈$295 |
| Sonnet 5.5 / Gemini 4 Argon / GPT-6.1-sol | $0.074 | $0.037 | — |

For comparison, Werk24 charges €0.15–0.95 per page plus a €490+/mo tier fee. Pricing at even $3–10 per sheet (an assumed value-based price, not a sourced market rate) gives over 95% tool-cost gross margin. The economics hinge on accuracy and human QA time.

**F. AI website build**
- Variable cost per site: about $25–50 of amortized Claude Max or Codex subscription (assuming about 3–4 sites a month on a $100 plan), plus about $1–3 of images.
- Hosting is passed through to the client: Vercel Pro $20, Netlify $9–20, Framer $10–30 or Shopify $29–39 per month.
- At a $1,500–5,000 freelancer price, tool-cost gross margin is 97% or more. Selling hosting and maintenance as a monthly line (e.g., ₪150–300/mo, assumed) covers the $10–30 hosting cost with a 70–90% margin.

**G. Ads management (Meta/Google)**
- Tools: creative generation (40 images at about $0.05 each is about $2; 2 short videos at about $14–24 each), plus reporting automation (about €20–50/mo n8n) and the shared LLM subscription.
- Total is under $60/mo per client against a $500–2,000/mo fee, so tool-cost gross margin is about 90–97%.

**H. Lead qualification**
- Using A's cost of about $0.03–0.08 per WhatsApp conversation, and assuming 30% of conversations qualify, AI and messaging cost is about $0.10–0.26 per qualified lead. A 3-minute voice qualification call costs about $0.28–0.64.
- HubSpot's free tier covers up to 1,000 contacts. Per-lead pricing (any client price above about $1 per qualified lead) leaves a large tool-cost margin, but Leon carries the volume risk.

**I. AI consulting / automation builds**
- Run cost per client is about €20–50/mo for n8n Cloud, or $9–29 for Make (3rd-party prices), or $19.99–129 for Zapier, plus LLM calls (a Haiku call with 2K input and 500 output tokens costs about $0.00045).
- Build cost is almost entirely Leon's time, so price the build on value or hours and add a maintenance retainer.

### Gaps
- No reliable Israeli-market (₪) price benchmarks were collected in this thread; all market benchmarks are US/global vendor blogs. Cross-check against the competitor notes in this folder.
- The over-generation ratio (4x) for video, the token sizes per chat turn and article, and the tile strategy for drawings are my assumptions, not measured values.
- Hebrew token inflation, VAT (מע"מ) treatment of foreign SaaS, and BSP or WhatsApp-provider markups are not included.

---

## Q4. Pricing models that protect margin, and common traps

### Takeaway
Separate the one-time build fee from a monthly fee that bundles a capped amount of usage, with published overage rates. Pass through or cap anything metered (voice minutes, WhatsApp templates, video seconds), and reprice after 60 days on observed volume. The biggest 2026-specific risks are vendor-side: frequent price and model changes, product shutdowns, and the end of free WhatsApp service messages.

### Cited Findings
- Retell's guide for agencies (6 Nov 2026) recommends four models. **(1)** Pass-through plus retainer: usage at cost or a stated markup, plus a management retainer sized to actual support hours. **(2)** A flat monthly fee per agent with a minute bundle and overage, with the bundle sized after 60 days. **(3)** Per outcome (booking, qualified lead), only with a known pilot conversion rate *and a monthly floor that covers platform cost*. **(4)** Committed usage with a floor. It also says to price the build separately even if discounted to zero, and to write a 60-day repricing step into the first contract — [Retell blog](https://www.retellai.com/blog/how-agencies-price-ai-voice-agents)
- A rule of thumb: set the setup fee at roughly the value of the first 90 days divided by 3, and the retainer at 15–25% of the setup fee per month (not an established standard) — [search summary: ideaproof.io](https://ideaproof.io/guides/ai-automation-agency)
- Ads management is commonly priced as a percentage of spend with a minimum, or a base fee plus a smaller percentage (e.g., $1,000 plus 8%) — [OuterBox](https://outerboxdesign.com/articles/paid-media/google-ads-management-agency/ppc-management-pricing-fees)

Traps documented on official pages:
- WhatsApp service messages became chargeable on 1 Oct 2026, after 1,000 free per number per month — [Meta docs](https://developers.facebook.com/documentation/business-messaging/whatsapp/pricing). Meta's marketing page still says they are free — [whatsappbusiness.com](https://whatsappbusiness.com/products/platform-pricing/). Meta may change rates at the start of a quarter — [search summary](https://www.nonito.io/whatsapp-business-api-pricing)
- Product shutdowns: the Sora 2 API was shut down on 24 Sep 2026 — [OpenAI](https://developers.openai.com/api/docs/models/sora-2). Gemini Omni 1.1 moves to 1.2 on 3 Dec 2026, and Gemini 2.5 Flash Image shuts down on 15 Mar 2027 — [Gemini pricing](https://aistudio.google.com/docs/pricing)
- Scheduled price changes: Gemini 4 Argon's cache price "doubles Dec 1, 2026", and "prices for many models change on December 1, 2026 or January 1, 2027" — [Gemini pricing](https://aistudio.google.com/docs/pricing)
- Context-length cliffs: Haiku 5.5 costs 5x more for prompts over 100K tokens — [Claude docs](https://platform.claude.com/docs/en/about-claude/pricing). OpenAI charges higher rates above 272K input tokens — [OpenAI](https://developers.openai.com/api/docs/pricing). Grok doubles above 200K — [xAI](https://docs.x.ai/docs/models)
- Concurrency and burst: ElevenLabs Agents bill $0.16/min (2x) above the concurrency limit — [ElevenLabs](https://elevenlabs.io/pricing/api). Retell includes 20 concurrent calls, then $8/mo each — [Retell](https://www.retellai.com/pricing). Vapi's free tier allows 4 concurrent calls, with extra lines at $10/mo — [Vapi](https://vapi.ai/pricing)
- Subscription limits shift: Antigravity merged Flash and Pro limits into one pool drawn down "according to API pricing" and turned AI credits into overage only (19 May 2026) — [Antigravity blog](https://www.antigravity.google/blog/changes-to-antigravity-plans). There was user backlash in March 2026 — [The Register](https://www.theregister.com/2026/03/12/users_protest_as_google_antigravity/). Claude plans say usage limits "depend on the model, chat length, and file size" — [claude.com/pricing](https://claude.com/pricing). xAI replaced SuperGrok with the X Subscription on 12 Oct 2026 — [ai-toolbox.co](https://ai-toolbox.co/grok-models/grok-pricing-plans-api-2026) (3rd-party)
- Licensing and terms: Vercel Hobby is non-commercial, so client sites need Pro — [Vercel](https://vercel.com/pricing). Suno's Free plan has no commercial rights, and credits don't roll over — [Suno](https://suno.com/pricing). Udio's commercial rights and downloads are disputed — [search summary](https://gptprompts.ai/udio-pricing)
- Premium modes: Opus fast mode is 2x the price; US-only inference is 1.1x — [Claude docs](https://platform.claude.com/docs/en/about-claude/pricing)
- Practitioner warning: "We're investing more time troubleshooting our automation than we would have spent handling the tasks manually." This argues for maintenance retainers — [search summary of a Reddit quote](https://optimizesmart.com/blog/ai-automation-agency-pricing-rules/) (secondary)

### Inferences
- A recommended structure for Leon:
  - Setup fee
  - Monthly retainer with explicit usage caps (e.g., "up to X voice minutes / Y WhatsApp conversations / Z videos")
  - Overage at about 2–3x unit cost
  - Client-owned accounts for Meta ad spend, WhatsApp WABA billing and Twilio wherever possible, so metered third-party costs bill directly to the client
  - A contract clause allowing repricing if vendor list prices change by more than about 10%
- Quote prices in USD-linked ₪, or reprice quarterly. The USD/ILS rate moved about 2% within one week of November 2026 (3.133–3.199) — [fxfeed](https://fxfeed.io/currencies/pairs/usd-ils)
- Build each automation so the model can be swapped (Claude, GPT, Gemini or Grok), because shutdowns and repricing happen on roughly a quarterly cadence.

### Gaps
- I found no hard data (only vendor blogs) on actual realized margins of small AI agencies, and no Israeli-specific data.
- I did not fetch Reddit or IndieHackers threads directly.

---

## Q5. Fixed monthly tool budget for a one-person studio (USD and ₪)

### Takeaway
A realistic minimum stack costs about **$177/mo (₪561)**. A comfortable stack with Claude Max, Google AI Ultra, Ahrefs and creative suites costs about **$764/mo (₪2,422)**. Client-specific metered costs (voice, WhatsApp, hosting, ad spend) should sit outside this and be passed through.

### Cited Findings (unit prices from the official pages cited in Q1–Q2)
- Claude Pro $20 / Max $100 — [claude.com/pricing](https://claude.com/pricing)
- ChatGPT Plus about $20 with Codex included (price is 3rd-party) — [chatgpt.com/pricing](https://chatgpt.com/pricing), [benchlm](https://benchlm.ai/md/chatgpt/pricing-plans.md)
- Google AI Pro $19.99 / Ultra $99.99 — [Google AI plans](https://one.google.com/about/google-ai-plans/)
- X Subscription Plus $8 / Premium $30 (3rd-party) — [ai-toolbox.co](https://ai-toolbox.co/grok-models/grok-pricing-plans-api-2026)
- n8n Starter €20 / Pro €50 — [n8n](https://n8n.io/pricing/)
- Vercel Pro $20 — [Vercel](https://vercel.com/pricing)
- ElevenLabs Starter $6 / Creator $22 — [ElevenLabs](https://elevenlabs.io/pricing)
- Suno Pro $10 / Premier $30 — [Suno](https://suno.com/pricing)
- Runway Pro $35 — [Runway](https://runway.com/pricing)
- Ahrefs Lite $129 — [Ahrefs](https://ahrefs.com/pricing)
- Framer Pro $30 — [Framer](https://www.framer.com/pricing)
- HubSpot Starter $20 — [HubSpot](https://www.hubspot.com/pricing/crm)
- Zapier Pro $19.99 annual — [Zapier](https://zapier.com/pricing)

### Inferences

**Minimum stack ≈ $177/mo ≈ ₪561/mo**

| Item | USD |
|---|---|
| Claude Pro (Claude Code) | $20 |
| ChatGPT Plus (Codex) | $20 |
| Google AI Pro (Antigravity, Flow) | $19.99 |
| X Subscription Plus (Grok), or Grok API only | $8 |
| n8n Starter, €20 (≈$23; EUR/USD not verified) | ≈$23 |
| Vercel Pro (commercial hosting for own and demo sites) | $20 |
| ElevenLabs Starter (TTS and music with commercial license) | $6 |
| Suno Pro | $10 |
| Prepaid API usage buffer (Claude, OpenAI, Gemini, xAI) | $50 |

HubSpot free CRM. No SEO suite; free or trial tools, or Gemini Search grounding with 5,000 free requests/mo.

**Comfortable stack ≈ $764/mo ≈ ₪2,422/mo**

| Item | USD |
|---|---|
| Claude Max 5x | $100 |
| ChatGPT Plus | $20 |
| Google AI Ultra 5x | $99.99 |
| X Subscription Premium | $30 |
| n8n Pro, €50 (≈$58, rate not verified) | ≈$58 |
| Ahrefs Lite (or Semrush SEO, $139) | $129 |
| ElevenLabs Creator | $22 |
| Suno Premier | $30 |
| Runway Pro | $35 |
| Vercel Pro | $20 |
| Framer Pro (own site) | $30 |
| HubSpot Starter | $20 |
| Zapier Pro (annual) | $19.99 |
| API buffer | $150 |

Upgrading to Claude Ultra ($200) or ChatGPT Pro ($100–200) would add $100–300.

- Break-even view: at ₪2,422/mo of fixed tools, one ₪3,000/mo retainer client or one ₪5,000 website build covers the comfortable stack. The fixed tool budget is small next to Leon's income target, so the main pricing lever is billable hours and caps on metered usage, not subscription costs.
- Buying annual plans (Claude Pro $17, Runway, Zapier, Semrush, n8n, Shopify) cuts the fixed stack by roughly 15–33% on those lines, at the cost of flexibility while vendor terms change quickly.

### Gaps
- The EUR/USD rate for n8n was not verified; ≈1.15 was assumed.
- Israeli VAT (18% assumed, not verified in this research) on foreign digital services, and income-tax treatment, were not researched. ₪ figures are pre-VAT.
- The stack excludes a domain or email (Google Workspace), a design tool (Canva/Figma), accounting software and Meta/Twilio account deposits. None of these were priced in this thread.
