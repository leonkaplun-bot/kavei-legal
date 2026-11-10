# AI Video, Film and Music Production Services: market, tools, competitors, prices (as of November 2026)

Prepared for: Leon Kaplun (leonaii.com, one-person AI studio, Israel; music/creative project "Lion Style").
Research date: 2026-11-08. Data older than 2026 is marked [OLDER]. Vendor marketing claims are marked [VENDOR CLAIM]. My own calculations are marked [ESTIMATE]. Many tool-pricing figures come from third-party pricing blogs because official pages were truncated or would not load. These are marked [SECONDARY] and should be checked on the official page before quoting to clients.

FX reference: the latest dated mid-market rate I found was 1 USD = 3.0632 ILS (22 July 2026; 52-week range 2.80–3.46) — [Pluang](https://pluang.com/en/tools/currency-converter/usd-ils). I could not confirm the November 2026 rate. ILS conversions below use about 3.0 ILS/USD and are [ESTIMATE].

---

## 1. State of the art of AI video and AI music tools (late 2026): clip length, consistency, lip-sync, resolution, licensing, real cost

### Takeaway
As of November 2026 the leading generators (Google Veo 3.1 and the new Gemini Omni, Kling 3.0, ByteDance Seedance 2.0, Runway Gen-4.5) still produce one shot at a time, usually 8–15 seconds, with native audio and lip-sync. Raw generation costs roughly $0.05–$0.60 per second. The real cost per *usable* second is 10–30 times higher, because most generations are thrown away. OpenAI's Sora is gone: the API was shut down on 24 Sep 2026, so it can no longer go in Leon's tool stack. In music, Suno's paid plans grant commercial use for $8–30/month, but the copyright status of purely AI-generated output is weak. The US requires human authorship.

### Cited Findings

**Google (Veo 3.1 / Gemini Omni)**
- Gemini API prices for Veo 3.1 [SECONDARY, sources broadly agree]:
  - Standard: $0.40/s at 720p/1080p, $0.60/s at 4K.
  - Fast: $0.10/s at 720p, $0.12/s at 1080p, $0.30/s at 4K.
  - Lite: $0.05/s at 720p, $0.08/s at 1080p, no 4K.
  - One 8-second clip costs about $0.40–$4.80 depending on tier and resolution.
  - Sources: [CloudZero](https://www.cloudzero.com/blog/veo-3-pricing/), [Magic Hour](https://magichour.ai/blog/veo-3-pricing), [Layer3Labs](https://www.layer3labs.io/guides/veo-3-pricing).
  - One site quotes $0.75/s. That conflicts with the others and is probably an error (same search set).
- According to the Gemini API deprecations page as cited by secondary sources, the original Veo 3, Veo 3 Fast and Veo 2 shut down on 30 June 2026, with Veo 3.1 as the replacement. Pages quoting "Veo 3" prices are stale — [CloudZero](https://www.cloudzero.com/blog/veo-3-pricing/), [Magic Hour](https://magichour.ai/blog/veo-3-pricing) [SECONDARY].
- Google announced **Gemini Omni** at I/O on 19 May 2026. It is a multimodal "any input → video" model that lets you edit a clip conversationally. Google's own page says Omni will replace Veo in the Gemini app — [Google Gemini overview](https://gemini.google/overview/video-generation/), [Cinevva I/O recap](https://app.cinevva.com/news/2026-05-19-google-io-gemini-omni) [SECONDARY]. Third-party sources say the first Omni Flash produced clips of up to 10 s and that Veo 3.1 remains the API's dedicated video line — [OpusClip](https://www.opus.pro/blog/gemini-omni-released-multimodal-ai-video-model-explained) [SECONDARY].
- Official Google AI Studio pricing for **Gemini Omni 1.2 Flash** [PRIMARY]:
  - Supports "up to 15 seconds of video generation and editing with native audio".
  - Video output costs $12.00 per 1M tokens.
  - Per-second equivalents: about $0.023/s at 360p, about $0.07/s at 720p, about $0.104/s at 1080p (upsampled), about $0.209/s at 4K (upsampled).
  - A 15-second clip at 720p costs about $1.04.
  - Omni 1.1 Flash (about $0.10/s) is automatically routed to 1.2 from 3 Dec 2026.
  - Source: [Google AI Studio pricing](https://aistudio.google.com/docs/pricing).

**OpenAI Sora (discontinued)**
- OpenAI's official deprecations page says developers were notified on 24 March 2026, and that the Videos API, `sora-2` and `sora-2-pro` were removed on **24 September 2026** with no replacement listed — [OpenAI API deprecations](https://developers.openai.com/api/docs/deprecations) [PRIMARY].
- Prices before the shutdown were $0.10/s for sora-2 at 720p, and $0.30/$0.50/$0.70 per second for sora-2-pro at 720p/1024p/1080p. Clips were 4–20 s — [Voyager](https://voyager.so/resources/models/sora-2) [SECONDARY, citing OpenAI pricing read 9 Sep 2026].
- The same source says the Sora consumer app closed on 26 April 2026 — [Voyager](https://voyager.so/resources/models/sora-2). I could not confirm this on an OpenAI page, so it is UNVERIFIED.

**Kling 3.0 (Kuaishou)**
- Each generation is 3–15 s. Clips can be chained with extensions up to about 3 minutes total — [Atlas Cloud length guide](https://www.atlascloud.ai/blog/tips/kling-ai-video-length-limit), [Virse](https://www.virse.ai/blog/kling-3-0-pricing) [SECONDARY]. One Atlas review says the maximum is 10 s, which conflicts with this.
- Credit costs per second [SECONDARY, sources agree]:
  - Without audio: 6 credits at 720p, 8 at 1080p.
  - With native audio: 9 at 720p, 12 at 1080p.
  - Voice control adds 2 credits/s.
  - Native 4K costs 30 credits/s.
  - Source: [Virse](https://www.virse.ai/blog/kling-3-0-pricing).
- The free tier is watermarked, limited to 720p and **not licensed for commercial use**. Paid plans start around $8.80–$10/month — [Kling pricing (camclo3d)](https://camclo3d.com/blog/kling-ai-pricing), [Fello AI](https://felloai.com/kling-ai-pricing/) [SECONDARY; plan prices vary between sources].

**Runway Gen-4.5**
- Gen-4.5 costs 12 credits/s. The API charges $0.01/credit, so about $0.12/s. The rate was cut from 25 to 12 credits/s around June 2026 — [Magic Hour](https://magichour.ai/blog/runway-gen-45-pricing), [Flexprice](https://flexprice.io/pricing-index/runway) [SECONDARY].
- Plans are Standard $15/month (625 credits, about 52 s of Gen-4.5), Pro $35 and Max $95. Credits do not roll over on Standard or Pro — [Magic Hour](https://magichour.ai/blog/runway-gen-45-pricing), [eesel](https://eesel.ai/blog/runway-ai-pricing) [SECONDARY; Max price conflicts in one source].

**ByteDance Seedance 2.0 (via Dreamina and aggregators)**
- Most sources give a maximum clip length of 15 s (4–15 s). One outlier claims 60 s — [Hedra model page](https://www.hedra.com/models/video/bytedance/seedance-20), [Overchat](https://overchat.ai/ai-hub/seedance-2-0) [SECONDARY].
- Vendor descriptions claim phoneme-level lip-sync in 8+ languages, audio generated jointly with the video, up to 12 reference files, and character and style consistency across shots. For stricter identity lock, Hedra recommends supplying a multi-angle reference grid — [Hedra](https://www.hedra.com/models/video/bytedance/seedance-20) [VENDOR CLAIM].

**What a real production workflow looks like (evidence from shipped projects)**
- *Hell Grind* (95-minute feature, 2026): the crew "generated and regenerated 15-second clips until they were usable". Prompts averaged about 3,000 words to keep shots consistent and avoid an "AI sheen". Higgsfield's CEO described the process as "a feeling of a slot machine" — [Wikipedia: Hell Grind](https://en.wikipedia.org/wiki/Hell_Grind), citing WSJ, AV Club and Screen Daily.
- *Kalshi* NBA Finals ad (June 2025) [OLDER]: about 300–400 generations produced 15 usable clips, roughly 20–27 generations per usable shot — [NPR via MPR News](https://www.mprnews.org/story/2025/06/23/npr-ai-video-ad-kalshi-advertising-nba-finals).
- *Coca-Cola* 2025 holiday ad [OLDER]: more than 70,000 AI clips were generated and refined — [Sakshi Post citing WSJ](https://www.sakshipost.com/news/business/coca-cola-holiday-2025-ai-generated-christmas-ad-faces-backlash-netizens-472619).

**AI music tools**
- **Suno** official pricing [PRIMARY]:
  - Free: 50 credits/day, no downloads listed, **no commercial use**.
  - Pro: $10/month, or $8/month billed annually; 2,500 credits/month; 20 downloads/month; commercial use included.
  - Premier: $30/month, or $24/month billed annually; 10,000 credits/month; 60 downloads/month; commercial use included.
  - Credits do not carry over. Ownership limits are set out in the Terms of Service.
  - Source: [Suno pricing](https://suno.com/pricing).
- **Suno v6** launched on 9 Sep 2026 as a model family (v6, v6-wild, v6-mini) trained on licensed catalogs from Warner Music, BMG and Believe. Older models are being retired — [Tech-Insider](https://tech-insider.org/suno-v6-warner-bmg-licensing-deal-2026/), [ExplainX](https://explainx.ai/blog/suno-v6-warner-bmg-licensing-settlement-2026) [SECONDARY; I found no primary Suno or WMG statement].
- **ElevenLabs Eleven Music** launched in August 2025 with Merlin and Kobalt licenses — [Chartlex tracker](https://www.chartlex.com/blog/business/ai-music-licensing-deals-tracker-2026) [SECONDARY]. A third-party guide says it is cleared for film, TV, ads and games — [ElevenLabs Magazine](https://elevenlabsmagazine.com/elevenlabs-eleven-music-guide-2026/) [SECONDARY, not ElevenLabs' own terms].

### Inferences
- [ESTIMATE] Cost per finished minute of footage:
  - At the Kalshi ratio of about 20:1, a usable 8-second Veo 3.1 Standard 1080p shot costs about 20 × $3.20 = $64, which is about $480 per finished minute in generation fees alone.
  - With Veo 3.1 Fast, Omni Flash or Runway (about $0.10–0.12/s), the same ratio gives about $120–150 per finished minute.
  - *Hell Grind* worked out to about $4,200 of compute per finished minute ($400k ÷ 95 min). That reflects a much higher regeneration rate at feature quality.
  - Subscriptions to editing, upscaling, voice and music tools come on top.
- The biggest technical limit is not resolution (4K is available) but **shot length (8–15 s) and continuity across hundreds of shots**: the same face, wardrobe, props and lighting. Directed performance and lip-sync in dialogue scenes are also hard. Every long-form project above solved this with large regeneration volumes and human editing.
- The Sora shutdown is a vendor-risk lesson. A one-person studio should not build its offer around one model. Leon should price and promise outputs, not specific tools, and keep at least two video engines (e.g., Veo/Omni plus Kling or Seedance) in the workflow.

### Gaps
- I did not obtain official, current pricing pages for Kling, Runway, Luma (Ray), Pika, Midjourney video or Higgsfield. Figures above are from secondary pricing blogs; Luma, Pika, Midjourney video and Higgsfield were not researched at all.
- The Google Vertex AI and Gemini API Veo price tables did not render, so Veo 3.1 rates are secondary.
- I found no independent benchmark of lip-sync accuracy or character consistency. All claims are from vendors.
- I did not research commercial-use terms for Google Veo/Omni outputs (Google indemnity), Runway or Seedance/Dreamina.

---

## 2. Notable AI-produced commercials, music videos, short and feature films (2024–2026): who, budget, team, timeline, reception, what humans did

### Takeaway
There are real AI-made successes in **short-form**: a national TV spot made by one creator for under $2,000 in tool costs, big-brand holiday campaigns, and Chinese micro-dramas. **AI feature films released in 2026 have failed critically or commercially.** The best-documented one, *Hell Grind*, needed 15 people, $500k and about $400k of compute, and critics said it "screamed AI". Every notable project still relied on humans for writing, editing, sound, music and curation.

### Cited Findings

**Commercials**
- **Kalshi, NBA Finals Game 3 TV ad (June 2025)** [OLDER] — [NPR via MPR News](https://www.mprnews.org/story/2025/06/23/npr-ai-video-ad-kalshi-advertising-nba-finals):
  - Made by freelancer PJ Accetturo with Google Veo 3.
  - Kalshi said AI prompting costs were "under $2,000". Accetturo's own fee was not disclosed.
  - About 300–400 generations produced 15 usable clips over roughly 2–3 days.
  - The script was written with Gemini and ChatGPT and the edit was done in CapCut, i.e., a human did the editing.
- **Coca-Cola "Holidays Are Coming" (2025)** [OLDER]:
  - Made by Silverside and Secret Level.
  - About 100 people worked on it, including 5 Silverside AI specialists who generated more than 70,000 clips. The cost was not disclosed.
  - There was strong public backlash over the visuals and job losses. Some critics questioned whether it cost about the same as a conventional shoot.
  - Sources: [Sakshi Post citing WSJ](https://www.sakshipost.com/news/business/coca-cola-holiday-2025-ai-generated-christmas-ad-faces-backlash-netizens-472619), [NewsBytes](https://www.newsbytesapp.com/news/science/coca-cola-ai-christmas-ad-sparks-backlash-over-weird-visuals/story). The headcount comparison with prior years conflicts in [Tribune](https://tribune.com.pk/story/2575763/coca-cola-releases-ai-generated-holidays-are-coming-ad-second-year-in-a-row-despite-backlash).
- **Israel (older)**:
  - H&O ran a fully AI campaign with a reported budget of about 1 million ILS. The report is about 2 years old [OLDER] — [Blinker](https://blinker.co.il/%D7%A7%D7%A8%D7%99%D7%95%D7%AA/%D7%9B%D7%9C%D7%9B%D7%9C%D7%99-%D7%9E%D7%A7%D7%95%D7%9E%D7%99-%D7%A7%D7%A8%D7%99%D7%95%D7%AA-%D7%9E%D7%90%D7%9E%D7%A8%D7%99%D7%9D/%D7%9C%D7%A8%D7%90%D7%A9%D7%95%D7%A0%D7%94-%D7%91%D7%99%D7%A9%D7%A8%D7%90%D7%9C-%D7%A4%D7%A8%D7%A1%D7%95%D7%9E%D7%AA-%D7%A9%D7%9E%D7%91%D7%95%D7%A1%D7%A1%D7%AA-%D7%9B%D7%95%D7%9C%D7%94-%D7%A2%D7%9C/431676/).
  - Swimwear brand BOM ran a campaign starring an AI character, "May", created by Ron Peretz. The deal was reportedly worth about 120,000 ILS [OLDER] — [ICE](https://www.ice.co.il/culture/news/article/1080620).
  - Tadiran ran a fully AI-based campaign [OLDER] — [ICE](https://www.ice.co.il/advertising-marketing/news/article/1054444).
  - Samsung Israel runs a 2026 contest for AI ad creators, with paid freelance assignments as prizes — [Samsung IL](https://www.samsung.com/il/promotions/ai-contest-2026/).

**Feature films and long form (2026)**
- **Hell Grind (Higgsfield AI, Kazakhstan/US)**:
  - Directed by Aitore Zholdaskali, co-written with Adilkhan Yerzhanov, 95 minutes long.
  - Budget was $500,000, of which about $400,000 (80%) went on AI compute.
  - A team of 15 people made it in **two weeks**, using Higgsfield Soul Cinema and Soul Cast and Seedance 2.0.
  - It screened at an industry event in Cannes on 16 May 2026, which was **not part of the festival**.
  - Sources: [Wikipedia](https://en.wikipedia.org/wiki/Hell_Grind), citing WSJ ("This Cannes Film Cost $500,000 to Make. $400,000 Was AI Compute Costs", Bousquette, 2026-05-21; I did not read the WSJ article directly), and [AV Club](https://www.avclub.com/ai-movie-hell-grind-cannes-film-festival) on the Cannes dispute.
  - Higgsfield estimates a comparable traditional film would cost about $50M [VENDOR CLAIM] — [Notebookcheck](https://www.notebookcheck.net/First-95-minute-AI-movie-with-skateboards-demons-and-plenty-of-online-criticism.1308627.0.html).
  - Reception:
    - Notebookcheck said that as a film it "has hardly convinced so far; as an AI demo, however, it works considerably better" — [Notebookcheck](https://www.notebookcheck.net/First-95-minute-AI-movie-with-skateboards-demons-and-plenty-of-online-criticism.1308627.0.html).
    - Fortress of Solitude called it cold, boring and unoriginal — [Fortress of Solitude](https://www.fortressofsolitude.co.za/hell-grind-first-ai-feature-film/).
    - AV Club called it "slop" — [AV Club](https://www.avclub.com/ai-movie-hell-grind-cannes-film-festival).
    - JoBlo's Chris Bumbray reportedly said it "screamed 'AI' from beginning to end" — secondhand via [LetsDataScience](https://letsdatascience.com/news/higgsfield-debuts-95-minute-ai-generated-feature-54064725) [SECONDARY].
    - Only about 20–22 minutes are publicly viewable.
  - The director said "the future is one person making a whole film" — [Creative Bloq](https://creativebloq.com/ai/the-future-is-one-person-making-a-whole-film-says-director-of-first-ai-movie-at-cannes).
- **Sanxingdui: Future Past (Bona Film Group, China, Oct 2026)**:
  - China's first AI-generated feature with a theatrical release.
  - Budget about $1.5M (AFP); box office about $180,000 (Maoyan).
  - Bona's COO admitted a "lukewarm" reception. USC's Stanley Rosen said: "The public is highly skeptical about AI use in major feature films, despite their general acceptance of short-form films."
  - Sources: [Fortune](https://fortune.com/2026/10/27/china-first-ai-film-sanxingdui-box-office/), [PetaPixel](https://petapixel.com/2026/10/28/chinas-first-fully-ai-generated-film-is-crashing-and-burning-at-the-box-office/).
- **Critterz (OpenAI-backed animated feature)**:
  - Vertigo Films and Native Foreign produce it; Federation Studios funds it.
  - Budget is reported at about $30M, with a 9-month schedule instead of the usual 3 years. It starts from human artists' sketches fed into OpenAI tools.
  - Sources: [TechRadar](https://www.techradar.com/streaming/entertainment/this-new-openai-backed-movie-has-a-budget-of-just-usd30-million-but-will-it-prove-ai-can-make-movies-hollywood-cant), [AV Club](https://www.avclub.com/ai-animated-movie-critterz-aims-cannes-debut-openai) [OLDER, 2025].
  - In May 2026 only first-look footage was shown to buyers at Cannes, through AGC International sales — [Nerdbot](https://nerdbot.com/2026/05/04/critterz-an-ai-animated-film-at-cannes/). I found no evidence of a finished premiere.
- **Other 2026 titles**:
  - *Dreams of Violets* is a fully AI-generated film shown at the Tribeca Festival on 10 June 2026 — [Wikipedia](https://en.wikipedia.org/wiki/Dreams_of_Violets).
  - *Copán La Leyenda* is a Honduran AI animated film released in May 2026. It drew heavy criticism, and the studio was accused of deleting critics' comments — [Wikipedia](https://en.wikipedia.org/wiki/Cop%C3%A1n_La_Leyenda).
- **Hybrid use in mainstream film**: Ben Affleck said he used AI "for lots of things" in Netflix's *Animals* (released 9 Oct 2026). It is a conventional film with AI-assisted parts — [Fortune](https://fortune.com/2026/10/27/china-first-ai-film-sanxingdui-box-office/).
- **Asteria (Natasha Lyonne / Bryn Mooser)**: its first feature, *Uncanny Valley*, directed by Lyonne, is a **live-action hybrid**, not fully generated — [AI Films blog](https://studio.aifilms.ai/blog/natasha-lyonne-asteria-film-studio-uncanny-valley) [SECONDARY].

**Micro-dramas (where AI long form does work)**
- Caixin data via Fortune: more than 95% of the more than 120,000 Chinese micro-dramas released in Q1 2026 were AI-generated, up from almost none a year earlier. Production costs fell to as little as **$3,000 per drama** — [Fortune](https://fortune.com/2026/10/27/china-first-ai-film-sanxingdui-box-office/).

### Inferences
- The evidence splits cleanly:
  - **Short commercial formats (15–60 s), social ads and vertical serialized micro-dramas are proven** at low cost.
  - **Theatrical-quality feature films are not.** The 2026 releases were panned or flopped, needed teams of about 15 or more, and cost from $500k to $1.5M+.
- Even the "AI-only" successes used humans for script, edit, sound design, music and curation of thousands of generations. Kalshi used CapCut and LLM scripting; Coca-Cola used 100 people.

### Gaps
- I did not find documented 2025–2026 AI **music video** case studies with budgets. Older examples such as Washed Out / Paul Trillo (2024) were not verified in this session.
- I found no audience or box-office data for *Dreams of Violets* or *Gods Don't Give Gifts* (scheduled for 4 Dec 2026).
- I found no verified data on post-production breakdowns (color, sound, VFX hours) for *Hell Grind*.

---

## 3. Competitors: AI-native studios and traditional production houses; prices (global USD, Israel ILS)

### Takeaway
**Global AI-native studios** fall into two groups:
- Well-funded film studios (Promise, Asteria) that do not publish prices.
- Ad studios charging roughly $1k–$10k for a 30-second AI spot (vendor surveys). Full-scope work with creative direction runs $25k–$75k, and top names like The Dor Brothers reportedly charge far more.

**In Israel**, AI videos are sold at about 1,500–4,000 ILS + VAT for up to 60 seconds, and 5,000–15,000 ILS for premium work. Traditional business videos cost about 5,000–35,000 ILS, and full professional productions 40,000–150,000+ ILS. There are already Tel Aviv hybrid AI studios with blue-chip client lists (Alter World, ArcaneWiz, SHOOF).

### Cited Findings

**Global AI-native studios**
- **Promise (Promise Advanced Imagination)**:
  - Launched in November 2024 with seed funding from Peter Chernin's North Road and Andreessen Horowitz. In May 2025 Google's AI Futures Fund and others joined, and the round brought a Google AI partnership; terms were not disclosed. Promise builds the MUSE pipeline and runs a slate of films and series [OLDER] — [PR Newswire](https://prnewswire.com/news-releases/promise-advanced-imagination-inc-unveils-new-studio-built-for-the-generative-ai-era-to-produce-films-series-and-develop-innovative-new-formats-backed-by-investments-from-the-north-road-company-and-andreessen-horowitz-promise-302309374.html), [Tubefilter](https://www.tubefilter.com/2025/05/20/promise-generative-ai-startup-strategic-investment-partnership-google/amp/).
  - It reportedly acquired the AI film school Curious Refuge — [Dealroom](https://app.dealroom.co/companies/promisestudios_com) [SECONDARY].
  - No public pricing.
- **Asteria**:
  - Founded in 2022 by Natasha Lyonne and Bryn Mooser. It is a subsidiary of Moonvalley, whose Marey model is trained on licensed data.
  - Launched the "Continuum Suite" AI production OS in March 2026, with Pressman Film among the first clients — [Deadline](https://deadline.com/2026/03/asteria-launches-continuum-suite-ai-operating-system-film-tv-production-1236749265/).
  - Partnered with virtual production studio ZeroSpace — [Variety](https://variety.com/2026/biz/news/ai-studio-asteria-strikes-strategic-partnership-zerospace-1236825083/).
  - No public pricing.
- **The Dor Brothers (Berlin)**: Yonatan Dor reportedly charged €200,000 (about $235k) per spot and passed $1M in annual revenue by mid-2025 — [AI Video Bootcamp](https://aivideobootcamp.com/blog/ai-video-career-guide-2026/) [SECONDARY, UNVERIFIED]. The team is Dor, 4 full-time staff and dozens of freelancers — [NYT via La Prensa](https://www.laprensa.hn/new-york-times-international-weekly/estudio-video-impulsado-ia-viraliza-internet-CK26793414).
- **Silverside / Secret Level** made the Coca-Cola holiday campaign with about 100 people (see Q2) — [Sakshi Post citing WSJ](https://www.sakshipost.com/news/business/coca-cola-holiday-2025-ai-generated-christmas-ad-faces-backlash-netizens-472619).
- **Higgsfield** is a tool vendor that also produces its own showcase films (*Hell Grind*) — [Wikipedia](https://en.wikipedia.org/wiki/Hell_Grind).

**Global pricing benchmarks for ads** [VENDOR CLAIM — most sources sell AI production]
- Traditional 30-second spot: about $15k–$80k, and much more for national campaigns. A Clutch-based average agency video project is about $42,280 — [1BVP](https://1bvp.com/ai-commercial-production/). Lemonlight puts traditional production at $15k–$50k+ per video — [RuminateX](https://www.ruminatex.com/comparison/ai-agency-vs-traditional-agency).
- AI 30-second spot:
  - $1k–$10k — [Nasravi](https://nasravi.com/ai-creative-insights/ai-video-ads-vs-traditional-production/).
  - $2k–$9k — [1BVP](https://1bvp.com/ai-commercial-production/).
  - €1,500–3,500 for a mid-market Italian studio — [MaiDreamsLab](https://maidreamslab.ai/en/blog/how-much-ai-commercial-pricing-2026/).
  - $25k–$75k once creative direction, voice, music and delivery are included — [Social Operator](https://socialoperator.ai/learn/ai-commercial-vs-traditional/).
- Claimed savings are 60–80% — [Nasravi](https://nasravi.com/ai-creative-insights/ai-video-ads-vs-traditional-production/) — or 70–90% — [Social Operator](https://socialoperator.ai/learn/ai-commercial-vs-traditional/). Traditional production still wins for hero campaigns with real talent and locations, and many brands go hybrid — [1BVP](https://1bvp.com/ai-commercial-production/).

**UGC-style ads**
- Human UGC creators [SECONDARY]:
  - About $100–200 per video.
  - A Collabstr 2026 report gives a $180 average asking price and $154 average paid.
  - Influee lists $92 per 30-second video.
  - Sources: [Influee](https://influee.co/blog/ugc-price), [Fluxnote](https://fluxnote.io/guides/how-much-do-ugc-ads-cost).
- AI avatar UGC tools work out to about $1–$12 per short video, e.g., Arcads at $110/month for 10 videos (about $11 each) — [Cinerads](https://www.cinerads.com/blog/ai-ugc-cost) [SECONDARY]. The cost per usable ad after retakes is higher (same source).
- Fiverr UGC packages average about $117–$155, sample size not stated — [Knowlify](https://knowlify.com/articles/ai-ugc-vs-creator-ugc-cost) [SECONDARY]. I could not verify Fiverr gig prices directly.

**Music videos**
- Traditional indie music video directors charge $300–1,500 per project or $500–4,000 per day — [Revid](https://www.revid.ai/blog/how-much-does-a-music-video-cost). Pixo gives $500–1,250 per day, and under $50 in AI generation costs for an AI music video — [Pixo](https://pixo.video/blog/how-much-does-a-music-video-cost) [VENDOR].
- A professional traditional director costs $15k–100k — [Seedance blog](https://www.seedance.tv/blog/ai-video-generator-music-artists-2026) [VENDOR].

**Israeli AI studios**
- **Alter World Studios (Tel Aviv)**:
  - Describes itself as "Ten years of crafting commercials leveraged into a new breed of AI production studio". Tagline: "AI. With control."
  - Has sub-studios for gaming UA creatives and trailers, CG product visualisation, and B2C commercials, plus an end-to-end pipeline through post and sound.
  - Its pre-AI client list includes HP, Coca-Cola, Playtika, Plarium, SciPlay, Yotpo, NiCE, Amdocs, Israel Railways and Golan Heights Winery.
  - No public prices.
  - Source: [Alter World](https://alterworld-studios.com/).
- **ArcaneWiz (Ramat Hasharon; founder and creative director Daniel Atzil)**:
  - Makes cinematic AI commercials and brand films for B2B SaaS, startups and premium brands, using Midjourney, Veo, Kling and Seedance.
  - Investor, launch, demo and training films start at **$5,000, delivered in 7–10 working days**.
  - Claims AI is "typically 40–60% lower than traditional". Delivers 16:9, 9:16, 4:5 and 1:1 formats [VENDOR CLAIM].
  - Sources: [ArcaneWiz comparison page](https://arcanewiz.com/ai-video-studio-vs-traditional-production/), [ArcaneWiz](https://arcanewiz.com/).
- **SHOOF (Tel Aviv)** is a video studio for tech brands. It offers AI image and video generation, AI sound design and upscaling alongside 2D/3D — [SHOOF](https://www.shoofvideo.co.il/).
- **Lightricks (Jerusalem)** makes the LTX video model and LTX Studio platform. It is a tool vendor, not a studio — [Wikipedia: Lightricks](https://en.wikipedia.org/wiki/Lightricks).

**Israeli prices: AI video (ILS)**
- **2site (dated 11 July 2026)** [PRIMARY vendor page] — [2site](https://2site.co.il/how-much-does-an-ai-video-cost/):
  - **2,500 ILS + VAT for up to 40 s; 3,000 ILS + VAT for up to 1 minute.**
  - Includes script, concept, AI scene creation, professional voiceover, subtitles, editing, and adaptation for website, Meta and TikTok.
  - More characters, languages or versions cost extra.
- Other Israeli vendor pages, in aggregate. The search summary did not map each figure to one page, so these are attributed as a group: [NEXT FRAME](https://nextframemediaa.com/blog/ai-video-cost-business/), [Magic Caricatures](https://www.magic-caricatures.com/%D7%9B%D7%9E%D7%94-%D7%A2%D7%95%D7%9C%D7%94-%D7%A1%D7%A8%D7%98%D7%95%D7%9F-%D7%AA%D7%93%D7%9E%D7%99%D7%AA-%D7%91ai/), [MotionMint](https://motionmint.app/), [vdo.guru](https://www.vdo.guru/he/%D7%A1%D7%A8%D7%98%D7%95%D7%9F-%D7%A9%D7%99%D7%95%D7%95%D7%A7%D7%99-ai/).
  - Bulk social clips from 30 ILS per video.
  - Starter AI packages from 1,500 ILS + VAT; pro tier 4,000 ILS + VAT for up to 60 s with narration.
  - Premium AI video with full script and storyboard: 5,000–15,000 ILS.
  - Monthly retainers: 2,500–8,000 ILS.
  - AI brand video 1,000–4,000 ILS vs 10,000–25,000 ILS for classic production (Magic Caricatures, single vendor).

**Israeli prices: traditional video production (ILS)**
- Extra (2026 guide): most SMB corporate videos cost 15,000–35,000 ILS; basic 5,000–12,000; premium 30,000–100,000 — [Extra](https://www.extra.co.il/corporate-video-pricing-2026/).
- ELP (2026): productions cost 40,000–150,000+ ILS; a shooting day with a professional crew costs 8,000–20,000 ILS — [ELP](https://www.elptv.co.il/post/%D7%9B%D7%9E%D7%94-%D7%A2%D7%95%D7%9C%D7%94-%D7%94%D7%A4%D7%A7%D7%AA-%D7%A1%D7%A8%D7%98-%D7%AA%D7%93%D7%9E%D7%99%D7%AA-%D7%91%D7%99%D7%A9%D7%A8%D7%90%D7%9C-%D7%94%D7%9E%D7%93%D7%A8%D7%99%D7%9A-%D7%94%D7%9E%D7%9C%D7%90-%D7%9C%D7%AA%D7%9E%D7%97%D7%95%D7%A8-2026).
- Vivi Studio: 2,500–4,500 ILS per small-crew shooting day — [Vivi Studio](https://vivistudio.co.il/%D7%9B%D7%9E%D7%94-%D7%A2%D7%95%D7%9C%D7%94-%D7%A1%D7%A8%D7%98%D7%95%D7%9F-%D7%AA%D7%93%D7%9E%D7%99%D7%AA/).
- Entry-level videos cost about 1,200–2,800 ILS for 30–45 s, usually before VAT — [SmartPush](https://smartpush.co.il/%D7%A1%D7%A8%D7%98%D7%95%D7%9F-%D7%AA%D7%93%D7%9E%D7%99%D7%AA-%D7%9E%D7%97%D7%99%D7%A8/), [Shivuknet](https://shivuknet.co.il/blog/promotionalvideo-cost-14/).

### Inferences
- [ESTIMATE] Israeli AI video is already **commoditised at the low end** (1,500–4,000 ILS for 40–60 s), only slightly above cheap template or animation videos (1,200–2,800 ILS). Leon's realistic pricing bands:
  - Entry: about 2,500–4,000 ILS + VAT for a 30–60 s ad.
  - Mid: 5,000–15,000 ILS for a premium spot with a storyboard and several formats.
  - B2B/export: $5k+ (about 15,000+ ILS), as ArcaneWiz charges for startup and investor films.
- Leon's competition is **local hybrid studios that already have commercial reels and client logos** (Alter World, ArcaneWiz, SHOOF), not Promise or Asteria. A one-person studio has to win on speed, price, and a specific niche (e.g., Russian-, Hebrew- and English-speaking clients, music-led content), not on "any format".
- Exported B2B work (Israeli startups selling globally) supports USD pricing at $2k–$10k per spot, in line with global AI-studio benchmarks.

### Gaps
- I found no public price lists for Alter World, SHOOF or Israeli advertising agencies' AI units, and no Israeli UGC-creator price data in ILS.
- I did not check Fiverr or Upwork AI video gig prices directly; the marketplace figures are secondary.
- I could not verify the Dor Brothers rate or any Promise or Asteria commercial pricing.

---

## 4. What buyers want and complain about; which offers are proven sellers

### Takeaway
Consumers are measurably wary of AI ads. In a June 2026 Harris Poll, 63% said they would be less willing to buy from brands using AI-generated ads, and 74% want AI use disclosed. Brands therefore buy AI mostly where the audience does not notice or care: performance and UGC-style social ads, product and e-commerce videos, variants and localisation, gaming UA creatives, B2B explainers and micro-dramas. Uncanny visuals, "slop", job-displacement backlash and rights or disclosure risk are the main objections.

### Cited Findings
- **Harris Poll / 4As / Infillion (presented at Cannes Lions, 24 June 2026)** — [Marketing Brew](https://www.marketingbrew.com/stories/harris-poll-ai-fatigue-less-trust-ai-generated-ads-cannes-lions):
  - 78% say AI makes ads "feel less authentic".
  - 78% find brands "cringey" when they overuse AI.
  - 63% would be less willing to buy from a brand using AI-generated ads.
  - 73% would trust an ad less if they suspected AI made it.
  - 65% wish brands would stop meaningless AI marketing.
  - On the industry side, about half of professionals use AI for visual asset creation and 56% for ideation.
- **Cint / Advertising Week (October 2026)**: 74% of US consumers believe brands should disclose AI use in advertising — [GlobeNewswire](https://www.globenewswire.com/news-release/2026/10/20/3384820/0/en/cint-report-finds-74-of-u-s-consumers-believe-brands-should-disclose-ai-use-in-advertising.html). 44% say discovering undisclosed AI use would lower their trust (same report, per search summary).
- **IAB / Sonata Insights**: 82% of ad executives think Gen Z and millennials feel positive about AI ads, but only 45% of those consumers do. **Ipsos / Syracuse**: only 13% of viewers were confident an AI ad was AI-made, and the same share wrongly flagged human-made ads. Both findings come via search summary; see [Digiday](https://digiday.com/marketing/with-ai-backlash-building-marketers-reconsider-their-approach/) and [eMarketer](https://www.emarketer.com/content/shoppers-aren-t-impressed-by-ai-generated-marketing) [SECONDARY].
- **Brand backlash case**: Coca-Cola's AI holiday ads drew criticism two years running (2024 and 2025) over "weird visuals" and creative jobs — [NewsBytes](https://www.newsbytesapp.com/news/science/coca-cola-ai-christmas-ad-sparks-backlash-over-weird-visuals/story), [Tribune](https://tribune.com.pk/story/2575763/coca-cola-releases-ai-generated-holidays-are-coming-ad-second-year-in-a-row-despite-backlash).
- **Israel regulation**: from 26 July 2026, Israeli election propaganda created or edited with digital means, including AI, must carry a disclosure. The Elections Committee chair ordered an unlabeled AI video removed — [Content Managers](https://www.content-managers.com/he/insights/ai-videos-israeli-elections/). The Likud used AI videos, including user-made ones, in its 2026 campaign — [Mako](https://www.mako.co.il/news-israel-elections/2026/Article-ec4ac22a5157c91026.htm).
- **Rights and ownership**:
  - The US Supreme Court denied cert in *Thaler v. Perlmutter* on 2 March 2026. This leaves the human-authorship requirement in place — [Mayer Brown](https://www.mayerbrown.com/en/insights/publications/2026/03/supreme-court-denies-review-in-ai-authorship-case).
  - The Copyright Office's January 2025 report states that "prompts alone" are insufficient for protection, though AI-assisted works with human authorship can be protected — [Reed Smith](https://www.reedsmith.com/our-insights/blogs/viewpoints/102mlpl/supreme-court-denies-certiorari-in-thaler-v-perlmutter-human-only-rule-for-ai/).
- **Proven sellers (evidence)**:
  - AI UGC ads: tools such as Arcads and Creatify are sold on per-video economics of about $1–$12 — [Cinerads](https://www.cinerads.com/blog/ai-ugc-cost). Agencies are packaging "AI UGC as a service" — [Ciela](https://ciela.ai/blogs/ai-ugc-as-a-service-for-agencies), [Motionbox](https://motionbox.io/blog/how-much-to-charge-clients-for-ai-ugc-ads) [SECONDARY].
  - Variants and cutdowns: one example is 30 variants for 5 markets — [ArcaneWiz](https://arcanewiz.com/ai-video-studio-vs-traditional-production/) [VENDOR]. Vendors say this is where savings are biggest — [Nasravi](https://nasravi.com/ai-creative-insights/ai-video-ads-vs-traditional-production/).
  - Gaming UA creatives and CG product visualisation each have their own Alter World sub-studio — [Alter World](https://alterworld-studios.com/).
  - Micro-dramas: more than 95% of Chinese Q1 2026 output was AI-generated — [Fortune](https://fortune.com/2026/10/27/china-first-ai-film-sanxingdui-box-office/).
  - Low-cost national TV spot: the Kalshi ad — [NPR/MPR](https://www.mprnews.org/story/2025/06/23/npr-ai-video-ad-kalshi-advertising-nba-finals).

### Inferences
- The offers with the best evidence of demand are:
  1. AI UGC and performance ad packs (e.g., 5–10 variants per month).
  2. E-commerce product videos.
  3. Startup explainer and investor or launch films.
  4. Localisation and multi-format cutdowns.
  5. Stylised music videos for independent artists.
  6. Vertical micro-drama episodes.
- Hero brand films and anything posing as "real people" are the riskiest, because of backlash and disclosure duties.
- Leon should put a **disclosure and rights clause** into every contract. It should state which tools were used, that the client gets the license the tool terms allow, that copyright in pure AI output may be unprotectable, and that no real-person likeness will be used without consent. "Fully owned IP" should not be promised.

### Gaps
- I found no Israeli consumer survey on AI ads, and no data on conversion or ROAS of AI UGC versus human UGC that comes from an independent source.
- Israeli copyright law's position on AI-generated works was not researched in this session; another researcher or a lawyer should cover it.

---

## 5. Music: pricing for jingles, sound logos and background music; AI-music licensing and ownership in 2026

### Takeaway
- **Jingle prices in Israel** are low: about 1,250–5,000 ILS. Global freelance jingles cost $300–2,500, professional work $2.5k–10k, and agency or national sonic branding $10k–80k+.
- **AI music tools are now licensed through label deals**:
  - Warner settled with Suno (Nov 2025), and Suno v6 launched on licensed catalogs (Sep 2026).
  - UMG settled with Udio (Oct 2025) and signed with ElevenLabs (Sep 2026).
  - Sony's and UMG's suits against Suno were reportedly still open as of September 2026.
- **The output's copyright protection remains weak** unless there is real human authorship (US Thaler precedent).

### Cited Findings
- **Israel jingle prices**:
  - A business jingle with a professional singer and voiceover costs 2,000–5,000 ILS — [Likol Studios](https://www.likol.co.il/%D7%92%D7%99%D7%A0%D7%92%D7%9C-%D7%A2%D7%A1%D7%A7%D7%99/).
  - A voiceover vendor lists a jingle product at 1,250 ILS + VAT (about 1,462 ILS with VAT) — [Music On Hold](https://www.musiconhold.co.il/product/%D7%92%D7%99%D7%A0%D7%92%D7%9C-%D7%A7%D7%A8%D7%99%D7%99%D7%A0%D7%95%D7%AA-%D7%9C%D7%A8%D7%93%D7%99%D7%95-8/).
  - Radio spot production costs about 1,000–5,000 ILS. Radio campaigns cost 5,000–100,000 ILS depending on airplay, and a regional campaign is about 2,500 ILS per day — [Hamazleg](https://hamazleg.co.il/%D7%9B%D7%9E%D7%94-%D7%A2%D7%95%D7%9C%D7%94-%D7%A4%D7%A8%D7%A1%D7%95%D7%9D-%D7%91%D7%98%D7%9C%D7%95%D7%95%D7%99%D7%96%D7%99%D7%94-%D7%A9%D7%99%D7%95%D7%95%D7%A7-%D7%91%D7%A8%D7%93%D7%99%D7%95-%D7%95/), [Gaya Zohar](https://www.gaya-zohar.co.il/post/%D7%9B%D7%9E%D7%94-%D7%A2%D7%95%D7%9C%D7%94-%D7%A4%D7%A8%D7%A1%D7%95%D7%9D-%D7%91%D7%A8%D7%93%D7%99%D7%95-%D7%91%D7%99%D7%A9%D7%A8%D7%90%D7%9C) [the search summary did not map each figure to one of these pages exactly; some may be older].
- **Global jingle and sound-logo prices** [VENDOR]:
  - A sonic logo (1–3 s) costs $150–500, an in-the-box jingle $300–800, and named-brand agency work $10k+ — [Violet Recording](https://violetrecording.com/how-much-does-a-jingle-cost/).
  - Freelance jingles cost $500–2,500, professional ones $2.5k–10k, and agency or national work with buyouts $10k–50k+ — [Evolve (28 Aug 2026)](https://evolveamz.com/?p=12819).
  - A sonic logo plus brand track costs 50k–300k AED (about $13.6k–82k) — [WithFeeling via Sortlist](https://www.sortlist.co.uk/agency/withfeeling).
  - Original jingles cost $5k–$500k, with practitioners quoting $2k–3.5k for a regional jingle — [Foxi Music](https://www.foximusic.com/blog/advertising-jingles-licensing-costs-tips/).
- **Suno**:
  - Warner Music settled its suit with Suno and agreed to a licensing partnership (November 2025); Suno also bought Songkick from WMG — [MarketScreener](https://uk.marketscreener.com/news/warner-music-group-settles-copyright-case-with-suno-for-licensed-ai-music-ce7d5ed2db8bff22) [OLDER].
  - v6 launched on 9 Sep 2026, trained on WMG, BMG and Believe catalogs. Sony and UMG suits reportedly remained active as of September 2026 — [Tech-Insider](https://tech-insider.org/suno-v6-warner-bmg-licensing-deal-2026/), [Soir Records](https://soirrecords.com/blog/the-great-settlement-major-labels-ai-lawsuits-licensing-suno-udio/) [SECONDARY].
  - Commercial use requires a paid plan ($10 or $30 per month) — [Suno pricing](https://suno.com/pricing).
- **Udio**: UMG and Udio settled on 29 Oct 2025 with new recorded-music and publishing licenses and a planned 2026 subscription platform. One tracker says it is a "walled garden" where outputs cannot be exported — [Chartlex](https://www.chartlex.com/blog/business/ai-music-licensing-deals-tracker-2026) [SECONDARY]. If true, this makes Udio unsuitable for client deliverables.
- **ElevenLabs**: on 10 Sep 2026 UMG and ElevenLabs agreed a multi-year license, starting with a fan remix and mashup platform that is separate from Eleven Music and the Music API — [Music Business Worldwide](https://www.musicbusinessworldwide.com/elevenlabss-11b-valuation-is-more-than-twice-the-size-of-sunos-its-just-struck-a-global-ai-music-deal-with-umg/), [Engadget](https://www.engadget.com/2255044/universal-music-group-is-collaborating-with-elevenlabs-on-a-new-ai-powered-creation-platform/). Sources conflict on whether the UMG deal covers the Music API (search summary).
- **Ownership**: in the US, works need human authorship and prompts alone are insufficient (*Thaler* cert denied on 2 Mar 2026; Copyright Office 2025 report) — [Mayer Brown](https://www.mayerbrown.com/en/insights/publications/2026/03/supreme-court-denies-review-in-ai-authorship-case). The American Federation of Musicians has filed a federal-court challenge against the major labels over credit and pay for studio musicians (search summary of [Chartlex](https://www.chartlex.com/blog/business/ai-music-licensing-deals-tracker-2026)) [SECONDARY].

### Inferences
- [ESTIMATE] Leon can produce a jingle or sound logo with Suno Pro or Premier ($10–30 per month) plus human mixing. He could price it at about 1,500–4,000 ILS in Israel, in line with local studios, or $500–2,500 for export clients.
- The licensing caveat has to be explicit. Clients get the commercial-use license from Suno's paid tier, not guaranteed copyright, unless Leon adds substantial human authorship (lyrics, melody edits, live vocals, arrangement). That argues for a **hybrid "AI-assisted, human-produced" positioning** for Lion Style and for client jingles.
- Background music for videos is cheapest to source from licensed AI tools or stock libraries, and is best bundled into video packages rather than sold on its own.

### Gaps
- I did not research Spotify, YouTube or Content ID policies for AI-generated tracks, or distributor (DistroKid etc.) rules. These matter for Lion Style releases.
- I did not obtain Suno's full Terms of Service text on output ownership, or Eleven Music's official commercial terms.
- I did not research Israeli ACUM rules for AI-assisted works.

---

## 6. Reality check of the claim: "any video in any format up to a feature film at the most professional level" (one-person studio)

### Takeaway
**The evidence does not support the claim as stated.** As of November 2026, no AI feature film, including well-funded team efforts, has been judged "professional level" by critics or audiences. The best-documented one needed 15 people, two weeks and about $400k of compute, and was panned. What the evidence does support is a strong claim for **short-form: 15–60 s ads, social and UGC-style content, explainers, product videos, stylised music videos, and short films or micro-drama episodes**. Longer pieces need human editing, sound and music, and buyers should be told about the limits.

### Cited Findings
- **Feature-length**:
  - *Hell Grind* had a $500k budget, $400k of it compute, a team of 15 and two weeks of production, and received negative to mixed reviews ("screamed 'AI'", "slop") — [Wikipedia](https://en.wikipedia.org/wiki/Hell_Grind), [AV Club](https://www.avclub.com/ai-movie-hell-grind-cannes-film-festival), [Notebookcheck](https://www.notebookcheck.net/First-95-minute-AI-movie-with-skateboards-demons-and-plenty-of-online-criticism.1308627.0.html).
  - *Sanxingdui* cost $1.5M and took about $180k at the box office — [Fortune](https://fortune.com/2026/10/27/china-first-ai-film-sanxingdui-box-office/).
  - *Critterz* has a $30M budget and relies on human artists, and only first-look footage had been shown by May 2026 — [TechRadar](https://www.techradar.com/streaming/entertainment/this-new-openai-backed-movie-has-a-budget-of-just-usd30-million-but-will-it-prove-ai-can-make-movies-hollywood-cant), [Nerdbot](https://nerdbot.com/2026/05/04/critterz-an-ai-animated-film-at-cannes/).
- **Tool limits**:
  - A single generation is about 8–15 s: Veo 3.1 8 s, Kling 3.0 up to 15 s, Seedance 2.0 about 15 s, Gemini Omni 1.2 up to 15 s — [Magic Hour](https://magichour.ai/blog/veo-3-pricing), [Virse](https://www.virse.ai/blog/kling-3-0-pricing), [Hedra](https://www.hedra.com/models/video/bytedance/seedance-20), [Google AI Studio pricing](https://aistudio.google.com/docs/pricing).
  - Production ratios run from about 20:1 (Kalshi) to 70,000 clips (Coca-Cola) — [NPR/MPR](https://www.mprnews.org/story/2025/06/23/npr-ai-video-ad-kalshi-advertising-nba-finals), [Sakshi Post/WSJ](https://www.sakshipost.com/news/business/coca-cola-holiday-2025-ai-generated-christmas-ad-faces-backlash-netizens-472619).
- **Audience acceptance**: "The public is highly skeptical about AI use in major feature films, despite their general acceptance of short-form films" (Stanley Rosen, USC) — [Fortune](https://fortune.com/2026/10/27/china-first-ai-film-sanxingdui-box-office/). 73% of consumers would trust an ad less if they suspected AI — [Marketing Brew](https://www.marketingbrew.com/stories/harris-poll-ai-fatigue-less-trust-ai-generated-ads-cannes-lions).
- **Where one person can win**: one freelancer made a TV-aired national ad in about 2–3 days for under $2,000 in tool costs — [NPR/MPR](https://www.mprnews.org/story/2025/06/23/npr-ai-video-ad-kalshi-advertising-nba-finals). AI micro-dramas cost as little as about $3,000 per drama — [Fortune](https://fortune.com/2026/10/27/china-first-ai-film-sanxingdui-box-office/).
- **Vendor risk**: Sora was removed from the API on 24 Sep 2026 — [OpenAI deprecations](https://developers.openai.com/api/docs/deprecations). Veo 3 and Veo 2 were shut down on 30 June 2026 — [CloudZero](https://www.cloudzero.com/blog/veo-3-pricing/) [SECONDARY].

### Inferences
- [ESTIMATE] Feature-length budget for a solo creator: at *Hell Grind*'s ratio (about $4,200 of compute per finished minute), a 90-minute film would cost roughly $380k in generation alone. At the cheaper Kalshi-style ratio with Fast-tier models (about $120–480 per minute), it would be $11k–43k in generation. That excludes months of solo labour for writing, editing, sound, music and color. It is technically possible to *finish* a feature-length AI film, but the evidence says the result will not be judged "most professional level" in 2026.
- Honest positioning would be: "AI-first production of commercials, product and explainer videos, music videos and short films, in every social and broadcast format, with human direction, editing and sound." Long-form (short films and micro-drama series, possibly a feature as a portfolio or experimental project) should be shown as R&D or capability, not as a guaranteed professional-grade service.
- The strongest differentiators are a fast turnaround (2–10 days, cf. ArcaneWiz's 7–10 days, Kalshi's 2–3 days), multi-format delivery (16:9, 9:16, 4:5, 1:1), bundled original AI-assisted music (the Lion Style crossover), and transparent rights and disclosure terms.

### Gaps
- There is no independent, systematic quality benchmark comparing AI and traditional output for commercials.
- I found no data on how many solo AI creators have won paid broadcast or feature commissions beyond the Kalshi example.
- I did not review Leon's own portfolio, so I cannot judge his current output against these benchmarks.
