# Engineering drafting, electrical design, BOM/quoting, PLC & I&C services: market, prices and the role of AI (as of Nov 2026)

Scope note: research done 2026-11-08. Prices are list or marketplace prices in USD unless stated as ILS. "Vendor claim" means the figure comes from the seller's own page. Older data is dated inline. Many marketplace figures came from search-result snippets of individual gig pages. Those are marked "(snippet)" where I could not open the page myself. Israeli licensing is mentioned only briefly; another researcher covers the law.

## 1. Who sells CAD drafting/conversion and electrical drafting, and at what price?

### Takeaway
Plain drafting and PDF/scan-to-DWG conversion is a heavily commoditized global market. Offshore firms in India start at about $9–16/hr. Marketplace gigs sell PDF-to-DWG at a few dollars per page and PDF-to-EPLAN at about $7–10 per page. Price rises mainly with speed (one-day turnaround), "intelligent" output (AutoCAD Electrical/EPLAN projects rather than dumb lines), and an engineer's sign-off. One new entrant (Schematiq) already sells "AI drafts, engineer signs, 48-hour delivery" as a productized electrical-schematic service.

### Cited Findings
**General drafting benchmarks (global/US)**
- Cad Crowd's AutoCAD rate guide (last updated 18 Nov 2024, older data) gives these ranges. Hourly: $30–120 overall, $30–85 for freelancers, $80–120 for a drafter at a design or construction company. Per CAD sheet: $35–180. A residential CAD sheet takes 8–15 hours. — [Cad Crowd blog](https://www.cadcrowd.com/blog/what-are-autocad-designer-rates-drafting-costs-services-company-pricing/)
- The same guide prices paper-to-CAD conversion per sheet by turnaround. At 4–6 weeks: 2D $35–140, 3D $160–180. At 3–10 days: 2D $45–350, 3D $250–480. One-day turnaround: $140–690 per sheet. Speed is a major price lever. — [Cad Crowd blog](https://www.cadcrowd.com/blog/what-are-autocad-designer-rates-drafting-costs-services-company-pricing/)
- Cad Crowd's electrical CAD marketplace lists freelancers "from $20/hr". Cad Crowd's help pages say jobs are custom-quoted. — [Cad Crowd electrical CAD](https://www.cadcrowd.com/services/electrical-cad); [Cad Crowd: how much jobs cost](https://www.cadcrowd.com/help/buyers/how-much-to-jobs-cost/)
- Cad Crowd PDF-to-DWG service listings have tiered packages, for example Simple $15 / Standard $40 / Advanced $75 for up to 5 / 15 / 30 pages. Other listings run $25/$60/$120 and $30/$80/$150. At the top tier that is about $2.5–5 per page. (snippet; the exact listing per tier was not confirmed) — [Cad Crowd 1805](https://www.cadcrowd.com/service/1805-convert-2d-pdf-to-dwg); [Cad Crowd 251](https://www.cadcrowd.com/service/251-convert-pdf-image-to-cad-dwg); [Cad Crowd 1657](https://www.cadcrowd.com/service/1657-i-will-convert-pdf-sketch-or-image-into-accurate)
- ArchiCGI (scan-to-CAD firm) bills $20/hr and says a clean single floor plan takes "a few hours". Large archives are quoted per batch. (snippet) — [ArchiCGI CAD conversion](https://drawings.archicgi.com/cad-conversion-services/)
- Upwork client budgets (job posts, not freelancer asks): electrical engineer for AutoCAD projects $17–39/hr; MEP drafter for AutoCAD electrical/circuit plans $5–20/hr (20–50 proposals); architectural AutoCAD drafter $6–10/hr. — [Upwork job 1](https://www.upwork.com/freelance-jobs/apply/Electrical-Engineer-for-AutoCAD-Projects_~022066673805523037882/); [Upwork job 2](https://www.upwork.com/freelance-jobs/apply/Autocad-Drafter-for-MEP-Plans_~022074272547833576935/); [Upwork job 3](https://www.upwork.com/freelance-jobs/apply/AutoCAD-Architectural-Drafter-Full-Time-Remote_~022070547582523516394/)
- US employed benchmark: an electrical/electronics drafter with AutoCAD averages $24.30/hr (2026), with a 10th–90th percentile range of about $19.4–30.2. — [PayScale](https://www.payscale.com/research/US/Job=Electrical_%2F_Electronics_Drafter/Hourly_Rate/98a1b775/Autodesk-AutoCAD)

**Offshore outsourcing firms (India)**
- Outsource2India: electrical 2D drafting from $9/hr, with a similar starting point for schematic drawing. (vendor claim) — [Outsource2India electrical 2D](https://www.outsource2india.com/engineering/electrical/electrical-2d-drafting-services.asp); [Outsource2India schematics](https://www.outsource2india.com/engineering/electrical/electrical-schematic-drawing-services.asp)
- IndiaCADworks: electrical schematic preparation/drafting from $14/hr, 3D modeling $16/hr, takeoff and estimation $14/hr (vendor claim). Its Clutch profile shows a minimum project of $1,000+ and an average rate under $25/hr. — [IndiaCADworks pricing](https://www.indiacadworks.com/pricing.php); [Clutch profile](https://www.clutch.co/profile/indiacadworks)
- Other Indian listings: Milestone PLM $8–28/hr; Ace CAD Solutions electrical CAD drafting ₹800/hr. — [IndiaMART Milestone](https://m.indiamart.com/milestoneplmsolutions/products-and-services.html); [IndiaMART Ace CAD](https://m.indiamart.com/ace-cad-solution/cad-drafting-services.html)
- A 2026 outsourcing guide puts Indian CAD drafters at about $10–30/hr versus $50–100+ onshore. — [Wisemonk](https://www.wisemonk.io/blogs/outsource-cad-services-to-india)
- An aggregator lists a "CAD outsourcing" average of $25–49/hr. — [Krowdbase](https://www.krowdbase.com/service/cad-outsourcing)
- No sourced Philippines or Eastern Europe rate cards were found (see Gaps).

**Electrical-specific gigs (Fiverr) and legacy conversion to intelligent ECAD**
- Fiverr has dozens of gigs for electrical schematics, control wiring, panel layouts and SLDs in AutoCAD/AutoCAD Electrical/EPLAN. Many hide prices ("Inbox for price details"). One gig shows conversion as a $20 add-on. — e.g. [Fiverr alfiand](https://www.fiverr.com/alfiand/draw-electrical-schematic-control-wiring-and-panel-layout-by-autocad-eplan); [Fiverr andrewphilip0](https://fiverr.com/andrewphilip0/create-electrical-schematics-single-line-diagrams-and-control-panel-layout); [Fiverr eliteelectrica](https://fiverr.com/eliteelectrica/create-autocad-electrical-drawings-wiring-diagrams-and-schematic-panel-layout)
- PDF-to-EPLAN P8 conversion gig: $10/page up to 10 pages, $8.50/page for 11–250 pages, $7/page above 250. It excludes new design, calculations and certification. (snippet) — [Fiverr em_design_ins](https://fiverr.com/em_design_ins/convert-pdf-electrical-schematics-into-professional-eplan-p8-projects)
- Another electrical PDF-to-AutoCAD conversion gig is quoted at $100–200. (snippet; scope unclear) — [Fiverr lakyshan](https://fiverr.com/lakyshan/convert-electrical-pdf-file-to-autocad-file)
- An industrial vendor blog estimates 2–4 hours per drawing page for a full "intelligent" conversion (wire numbers, cross-references, part data). (snippet, unverified) — [Industrial Monitor Direct](https://industrialmonitordirect.com/blogs/knowledgebase/autocad-electrical-vs-promise-vs-eplan-industrial-cad-comparison)
- Hagerman (Autodesk reseller) warns that migrating legacy AutoCAD to AutoCAD Electrical often carries existing drawing problems into the new environment, so cleanup comes first. — [Hagerman blog](https://blog.hagerman.com/converting-legacy-autocad-projects-to-autocad-electrical-hagerman-migration-process)
- Elecdes offers legacy drawing conversion with "contact us for prices", so no public rate. — [Elecdes](https://elecdes.com/services/electrical-drafting)

**Software alternative to conversion services**
- AutoDWG PDF to DWG Converter costs $130 for a perpetual single-user license (ComponentSource lists from $176.40). The vendor says results on scanned PDFs depend on line clarity and contrast. — [AutoDWG store](https://dwg.autodwg.com/pdf-to-dwg-converter/store.html); [ComponentSource](https://www.componentsource.com/product/pdf-to-dwg-converter); [AutoDWG support](https://dwg.autodwg.com/pdf-to-dwg-converter/support.html)

**AI-native electrical engineering service (direct model competitor)**
- Schematiq calls itself "the first AI-native electrical engineering firm". AI drafts custom schematics and senior engineers review and sign them. Deliverables: a native EPLAN, AutoCAD Electrical or Zuken E3 project, a BOM, a compliance report (IEC 60204-1, IEC 61439), an audit log and engineer sign-off. It quotes fixed prices within 4 business hours and delivers 48 hours after brief approval. Engagement models: project, retainer, or embedded. No public prices. Targets OEM machine builders, system integrators and panel builders. — [Schematiq](https://schematiq.org/)

### Inferences
- Plain "PDF → DWG lines" work is a race to the bottom ($2.5–15/page, $5–20/hr). An Israel-based studio cannot win there on price. It can win only on turnaround, correctness, Hebrew/Israeli-standard knowledge and accountability.
- The defensible upmarket bands are visible in the data. One-day turnaround costs $140–690/sheet against $35–140/sheet over weeks. "Intelligent" ECAD conversion takes 2–4 h/page versus minutes for dumb conversion. Engineer-reviewed packages are Schematiq's model.
- Schematiq shows that a "spec in → fixed quote in 4 h → package in 48 h" productized format is already being sold to panel builders and integrators. Leon's offer would be compared to it.

### Gaps
- No sourced Philippines or Eastern European (Ukraine, Serbia etc.) drafting rate cards were found.
- Fiverr electrical gig base prices were mostly hidden. Per-page conversion figures are single-seller snippets, not market averages.
- No Israeli per-sheet or per-hour drafting prices (ILS) were found on public pages. Israeli freelancers appear to quote privately.

## 2. The Israeli market: panel builders, electrical contractors and I&C integrators needing drawings, BOMs and quotes. Who buys, and how?

### Takeaway
Israel has a concentrated, standards-regulated panel-building sector (about 110 certified assemblers under SI 61439) plus electrical design offices and a few dozen small-to-mid I&C integrators. Public and defence clients buy through tenders, planner rosters and fixed tariff schedules. In the defence tariff, the "specifications, bill of quantities (BOQ) and estimate" component is an explicitly priced slice of the electrical design fee. Private panel builders, contractors and integrators mostly do drawings and BOMs in-house with salaried drafters, which is the work an AI studio would take over or speed up.

### Cited Findings
**Panel builders (the core SpecFlow buyer)**
- The Standards Institution of Israel says there are about 170 approved permits for about 110 assembling manufacturers of electrical panels in Israel. Panels must comply with the SI 61439 series, and the Standard Mark (Tav Teken) is audited annually; the page was updated January 2026. — [SII: Standard Mark for electrical panels](https://www.sii.org.il/he/lobby/lab-tests-search/laboratory-test/electrical-panel/)
- Named players: the Kahane Group runs an electrical panels division and published a low-voltage price catalog (dated 19.9.21, older). W.M. Rom Electrical Panel Engineering has a plant in the Tzipori industrial zone. The d.co.il directory has a dedicated "electrical panels" category. — [Kahane catalog PDF](https://www.kahane.co.il/wp-content/uploads/2024/01/Low-Voltage-catalogprice-19.9.21-Digital.pdf); [AllJobs: W.M. Rom](https://www.alljobs.co.il/m/p/company?cid=348370); [d.co.il panels category](https://www.d.co.il/h-c22000-e0-p0-l0/)
- The Israeli association of electrical and electronics engineers (SEEEI) runs a forum of electrical panel manufacturers. — [SEEEI document](https://www.seeei.org.il/prdFiles/2637_desc3.doc)

**Electrical design offices and in-house drafting demand**
- Israeli job boards carry many ads for electrical drafters and practical engineers (handasaim) at design offices and manufacturers. They ask for AutoCAD/AutoCAD Electrical (one ad requires 3+ years of AutoCAD Electrical), single-line drawings of panels, wiring plans, component layouts and component lists for purchasing. — [Drushim ad](https://www.drushim.co.il/job/37928221/e9e4c6fa/); [Drushim ad 2](https://www.drushim.co.il/job/38578420/1f2fec48/); [Drushim job category](https://www.drushim.co.il/jobs/subcat/105-356-356/)
- Example: design office Y.T. Engineering (Haifa) recruits a drafter with at least 3 years in design offices and experience drafting control panels and LV/HV systems. No salary is listed. — [Drushim: drafter for electrical design office](https://www.drushim.co.il/job/38975197/c18d38f5/)

**I&C / automation integrators**
- El-Mor (founded 1993) provides automation and SCADA control, PLC-integrated systems and HMI. — [El-Mor automation & control](https://www.el-mor.co.il/en/areas-of-activity/automation-and-control/)
- ACKSYS (Rishon LeZion) lists electrical design, PLC programming, SCADA and DCS integration. — [automa.net directory](https://automa.net/business-directory/israel/system-integrator/acksys)
- "Automatika – Automation & Control Technologies" (Kfar Saba, 11–50 employees) recruits for PLC/HMI work, mainly defence. YSB Group (Yavne) recruits SCADA/HMI programmers. — [AllJobs: Automatika](https://www.alljobs.co.il/Employer/HP/default.aspx?cid=169072); [Drushim: YSB](https://www.drushim.co.il/job/37934225/86f0e964/)
- Israeli control-engineer job ads ask for 3–5+ years of PLC programming. They cite Siemens (TIA Portal) and Unitronics, Profinet/Ethernet-IP/Modbus, and SCADA/DCS. Field roles may require an electrician's license. Process plants in the south and the Dead Sea area are among the hirers. — [Drushim: control & automation engineer](https://www.drushim.co.il/job/38596109/4f0c2ae8/); [AllJobs: PLC & industrial control engineer](https://www.alljobs.co.il/m/p/jobs/8751169); [AllJobs: automation & control engineer](https://www.alljobs.co.il/m/p/jobs/8762104)

**How public and defence buyers pay for electrical design (hard ILS anchors)**
- The Ministry of Defense tariff for electrical and extra-low-voltage design (chapter 2.9.1, edition 01, August 2020 — older) sets the base fee as a percentage of installation value, interpolated between table rows:

  | Installation value | Standard fee | Complex buildings |
  |---|---|---|
  | ₪100K | 9.720% | 11.907% |
  | ₪1M | 6.364% | 7.795% |
  | ₪10M | 4.396% | 5.285% |
  | ₪100M | 3.095% | 3.753% |

  — [MOD tariff 2.9.1 (PDF)](https://www.online.mod.gov.il/Online2016/Documents/General/Binuy/forms/2020/2_9_1.pdf)
- The same tariff splits the fee into partial services (CAD design): preliminary design 15%, final plans 5%, system calculations 10%, layout and installation drawings 35%, specifications/BOQ/estimate 10%, and design-to-execution checks 20% (12% of that is supervision). Tasks explicitly include preparing BOQs (כתבי כמויות), equipment lists (רשימות ציוד), cost estimates, and answering contractor questions during tender. Controllers, cameras and similar end equipment count at only 20% of their value for fee purposes; generators, UPS, transformers and PV count at 50%. Its per-m² installation-cost assumptions include offices ₪750/m², computer halls ₪2,600/m² and clean rooms ₪2,000/m². — [MOD tariff 2.9.1 (PDF)](https://www.online.mod.gov.il/Online2016/Documents/General/Binuy/forms/2020/2_9_1.pdf)
- A newer MOD "Yellow Book" sets planner fees per m² and, for the first time, decouples the fee from the planner's cost estimate. (snippet of the announcement) — [MOD Yellow Book message](https://www.online.mod.gov.il/Online2016/Documents/General/Binuy/Presentations/YellowBook/message.pdf)
- A Finance Ministry directive (Takam 13.9.2) caps hourly rates for external service providers. The top engineer tier appears to be about ₪314/hr, but the extracted table was garbled and undated, so this is unverified. — [Takam 13.9.2.1 (btl.gov.il)](https://www.btl.gov.il/Funds/Yoatzim/Documents/TakamHodaa13.9.2.1.doc)

**Procurement channels (2026 examples)**
- KKL tender 562/26 for engineering coordination, design and execution management (published 21.05.2026, due 23.06.2026). — [KKL tender brief](https://www.kkl.org.il/files/bid-562-26-brief.pdf)
- Tel Aviv-Yafo tender 134/2026 to supply, install and maintain an energy control, management and monitoring system at municipal sites (due 08.11.2026). — [Tel Aviv tender 134/2026 (PDF)](https://www.tel-aviv.gov.il/AuctionAndCareers/DocLib4/%D7%9E%D7%9B%D7%A8%D7%96%20%D7%A4%D7%95%D7%9E%D7%91%D7%99%20%D7%9E%D7%A1%D7%A4%D7%A8%20134.2026%20%D7%9C%D7%90%D7%A1%D7%A4%D7%A7%D7%94,%20%D7%94%D7%AA%D7%A7%D7%A0%D7%94%20%D7%95%D7%AA%D7%97%D7%96%D7%95%D7%A7%D7%94%20%D7%A9%D7%9C%20%D7%9E%D7%A2%D7%A8%D7%9B%D7%AA%20%D7%91%D7%A7%D7%A8%D7%94,%20%D7%A0%D7%99%D7%94%D7%95%D7%9C%20%D7%95%D7%A0%D7%99%D7%98%D7%95%D7%A8%20%D7%90%D7%A0%D7%A8%D7%92%D7%99%D7%94%20%D7%91%D7%90%D7%AA%D7%A8%D7%99%D7%9D%20%D7%A2%D7%99%D7%A8%D7%95%D7%A0%D7%99%D7%99%D7%9D%20%D7%91%D7%AA%D7%9C%20%D7%90%D7%91%D7%99%D7%91-%D7%99%D7%A4%D7%95.pdf)
- National Insurance Institute (btl.gov.il) tender B(1040)2025 for maintenance of electrical panels, transformers and HV switchgear (published 28.04.2026, due 28.06.2026). This is a maintenance tender, not design. — [BTL tender](https://www.btl.gov.il/About/tenders/Pages/MichrazB(1040)2025.aspx)
- Public bodies also keep rosters of planners/consultants (מאגר מתכננים), e.g. Habima National Theatre's January 2026 call to join its roster of engineers, planners and consultants. — [Habima roster call (PDF)](https://www.habima.co.il/wp-content/uploads/2026/01/%E2%80%8E%E2%81%A8%D7%94%D7%96%D7%9E%D7%A0%D7%94-%D7%9C%D7%94%D7%A6%D7%98%D7%A8%D7%A3-%D7%9C%D7%9E%D7%90%D7%92%D7%A8-%D7%9E%D7%94%D7%A0%D7%93%D7%A1%D7%99%D7%9D-%D7%9E%D7%AA%D7%9B%D7%A0%D7%A0%D7%99%D7%9D-%D7%95_%D7%90%D7%95-%D7%99%D7%95%D7%A2%D7%A6%D7%99%D7%9D-%D7%A9%D7%9C-%D7%AA%D7%99%D7%90%D7%98%D7%A8%D7%95%D7%9F-%D7%94%D7%91%D7%99%D7%9E%D7%94-%D7%94%D7%AA%D7%99%D7%90%D7%98%D7%A8%D7%95%D7%9F-%D7%94%D7%9C%D7%90%D7%95%D7%9E%D7%9914694131.10%E2%81%A9.pdf)
- Noga (the Israeli grid system operator) contracts electromechanical planners for transformation projects. — [Noga document](https://www.noga-iso.co.il/media/44fj2lnz/%D7%9E%D7%A8-%D7%95%D7%9C%D7%93%D7%99%D7%9E%D7%99%D7%A8-%D7%91%D7%9C%D7%95%D7%9E%D7%A0%D7%98%D7%9C-%D7%9E%D7%AA%D7%9B%D7%A0%D7%9F-%D7%90%D7%9C%D7%A7%D7%98%D7%A8%D7%95%D7%9E%D7%9B%D7%A0%D7%99-%D7%9C%D7%A4%D7%A8%D7%95%D7%99%D7%A7%D7%98%D7%99-%D7%94%D7%A9%D7%A0%D7%90%D7%94-%D7%94%D7%A2%D7%A8%D7%95%D7%AA-%D7%90%D7%92%D7%A3-%D7%9E%D7%A9%D7%A4%D7%98%D7%99.pdf)
- The central portal for government tenders is mr.gov.il. — [mr.gov.il tender documents example](https://mr.gov.il/ilgstorefront/he/p/attachment/005056BF4DAB1EDB809610EFABBFA123/מסמכי הליך)

**Demand drivers in 2026: data centers**
- About 100 data-center bids across Israel are testing the national grid. — [Ynet](https://www.ynetnews.com/business/article/bjn8umhpze)
- Israel capped new data centers at 200 MW. About 27 GW of grid connection requests had queued, and 1 GW extra is allocated to large data centers. — [DCD](https://datacenterdynamics.com/en/news/israel-to-cap-capacity-of-new-data-centers-at-200mw-report); [Dealroom news](https://dealroom.co/news/163814-israel-caps-data-centres-at-200mw-after-developers-sought-27gw-of-grid-c/)
- The Crusoe Afula deal is boosting Israel's data center sector. — [Globes](https://en.globes.co.il/en/article-1001541136)
- In the US, 45–70% of a data center's construction budget goes to electrical work (not Israel-specific). — [EC&M / ECmag](https://www.ecmag.com/magazine/articles/article-detail/data-center-surge-beckons-electrical-workers)
- Local contractors named in market reports: Electra Group, Mercury, MiCiM, Margolin Bros. — [Arizton Israel data center market](https://www.arizton.com/market-reports/israel-data-center-market)

**Licensing (brief)**
- A registered electrical engineer has the broadest authority to prepare electrical plans. A licensed electrician can prepare plans, usually only for smaller buildings. — [pro.co.il guide](https://www.pro.co.il/electricians/guide/home-electrical-plan)

### Inferences
- About 110 certified panel assemblers is a small, reachable B2B list for direct outreach. Their bottleneck is turning consultant SLDs/schematics (usually PDF) into a priced BOM and quote for tenders, which is exactly what SpecFlow does. The standard-mark regime (SI 61439) also creates demand for documentation packages: BOMs, layouts and verification documents.
- The MOD tariff gives a defensible ILS price anchor for BOQ/estimate work. These are calculations from the table. On a ₪1M installation the standard design fee is about ₪63.6K, and its "specs/BOQ/estimate" slice (10%) is about ₪6.4K. On ₪10M the fee is about ₪440K and the BOQ slice about ₪44K. A design office could subcontract BOQ/estimate preparation to an AI studio below these numbers and keep margin.
- Buying modes: (a) public and defence work goes through tenders, planner rosters and tariffs, and you need to be a registered planner or a subcontractor to one; (b) private panel builders, contractors and integrators buy ad hoc via relationships, mostly to meet tender deadlines. Subcontracting to design offices and panel builders is the realistic entry point for a small studio, rather than bidding tenders directly.
- Data-center build-out (with the 200 MW cap) and defence-sector expansion are the likely near-term demand pulls for LV panel and I&C documentation. This is inference; no Israel-specific contractor-demand statistics were found.

### Gaps
- No ILS hourly or per-sheet rates for Israeli private drafters or electrical design offices, and no Israeli salary survey for drafters or control engineers, were found. One search snippet mentioned a panel-drafter job ad at ₪10–13K/month, but the source could not be verified, so it is excluded.
- I did not research the number of registered electrical contractors (Registrar of Contractors) or the size of the Israeli panel market in ILS.
- The current (post-2020) MOD Yellow Book per-m² electrical design rates were not extracted.

## 3. AI tools for CAD and electrical design: what exists, cost, and quality

### Takeaway
AI is already productized for (a) construction electrical takeoff from floor plans: counting devices and fixtures, at roughly $100–300/user/month or $2–3K/seat/year, with Trimble Accubid LiveCount, Togal, STACK, Kreo, BuildVision, Drawer AI and Countfire; and (b) ECAD assistants inside EPLAN, WSCAD and Siemens TIA that generate BOMs, layouts and edits from structured project data. Very few tools read an arbitrary PDF schematic or SLD of an industrial panel and output a priced BOM. The closest is Switchonomy (India), plus construction-oriented PDF-to-BOM tools such as Aginera and OpenDrawing. No vendor publishes independent accuracy tests, and reviewers treat AI counts as a check, not final bid quantities.

### Cited Findings
**General CAD (Autodesk)**
- AutoCAD 2026 AI features:
  - Smart Blocks "Detect and Convert" (tech preview) finds similar geometry and converts it to blocks; Search & Convert, Placement and Replacement suggest blocks via Autodesk AI.
  - Markup Import/Assist imports PDF/JPG/PNG markups and detects commands like MOVE/COPY/DELETE in markup text.
  - Autodesk Assistant is a conversational help assistant.

  — [Autodesk AutoCAD 2026 features](https://www.autodesk.com/uk/products/autocad/features)
- Cadalyst's review of AutoCAD 2026 notes that "human oversight remains essential" for AI-suggested changes. — [Cadalyst](https://blog.cadalyst.com/cadmanagement/autocad-2026-focuses-on-productivity-with-speed-ai-and-collaboration)

**Electrical CAD (ECAD) assistants**
- Eplan Copilot ships with Eplan Platform 2027, available from September (2026). At Hannover Messe it generated a mounting-panel layout live from a well-defined BOM. Siemens' Industrial Copilot can independently make changes in an Eplan project. SPS 2026 (Nuremberg, 24–26 Nov) highlights include pre-planning and automated wiring and wire-end processing. These are vendor and trade-press claims; I found no independent tests. — [Eplan Copilot page](https://www.eplan.com/de-en/about-us/innovations/ai-driven-industrial-automation/eplan-copilot/); [Eplan Platform 2027 press](https://www.eplan.com/my-en/about-us/press/now-is-best-to-test-the-eplan-platform-2027/); [Eplan at SPS](https://www.eplan.com/de-en/about-us/events/sps/)
- WSCAD ELECTRIX AI 2026: "generate complete BOM with just one click", cabinet layouts from circuit diagrams, rule and error checks (unassigned symbols, open connections), translation into 100+ languages and a prompt-driven Copilot. The page does not claim AI import of PDF or scanned schematics. Prices are by quote. — [WSCAD ELECTRIX AI](https://www.wscad.com/us/electrix/)
- eSchematicAI generates IEC schematics plus BOM from plain-language prompts for QElectroTech (open source). It has a free trial (100 prompts) and a €99 one-time personal license. It does not convert PDFs. — [eSchematicAI](https://eschematicai.com/)
- Siemens Industrial Copilot for TIA Portal engineering has been on the Siemens Xcelerator marketplace since summer 2024. A managed-service version was announced for 2025. No public price was found. — [BusinessWire (Siemens, May 2025)](https://www.businesswire.com/news/home/20250512053219/en); [Manufacturing.net](https://www.manufacturing.net/operations/news/22926249/siemens-expands-generative-aipowered-industrial-copilot)

**PDF/SLD → BOM → quote (closest to SpecFlow AI)**
- Switchonomy (Skylights Energy, Bangalore) is marketed as the "first AI-based panel estimation software". It covers LV panels (PCC, MCC, APFC, PLC, VFD, control). Its AI reads an uploaded SLD and generates a BOM "in minutes", then it prices from a maintained component database and generates a quotation; there is also drag-and-drop layout. No price is listed ("Start Free" plus demo) and no accuracy metrics are given. Targets panel manufacturers, contractors, consultants and estimators. — [Switchonomy / panelestimation.com](https://panelestimation.com/)
- Aginera "PDF to BOM": computer vision trained on construction drawings recognizes symbols, reads annotations and traces linear runs. It exports to Excel/PDF, can price the BOM or generate RFQ packages, and claims very high accuracy on schedule-driven items (vendor claim). Pricing: free Starter with 200 AI credits, Professional $299/month, Enterprise by quote (snippet). — [Aginera PDF to BOM](https://aginera.ai/solutions/pdf-to-bom); [Aginera free tool](https://aginera.ai/tools/pdf-to-bom); [Aginera comparison 2026](https://aginera.ai/blog/ai-takeoff-software-comparison-2026)
- OpenDrawing finds, counts and labels symbols, tables and values, including on single-line diagrams (vendor claim). — [OpenDrawing](https://opendrawing.ai/)
- AutoPanel Design is a panel design tool that exports a BOM, circuit diagrams and manufacturing PDF. It does not read PDFs. — [AutoPanel Design](https://www.autopaneldesign.com/)

**Mechanical drawing AI (adjacent, not electrical)**
- Werk24 is an API that extracts metadata, tolerances, GD&T and material from 2D mechanical drawings for quoting. It charges per page after choosing a tier; the trial is 100 pages free for 90 days (another page says a 100-drawing trial key); pay-as-you-go has no minimum. — [Werk24 pricing](https://it.werk24.io/pricing); [Werk24 Laserhub case](https://werk24.io/case-studies/laserhub)
- CADDi (Japan) sells an AI drawing search and data platform. It raised $114M at a $1.2B valuation in Sep 2026, and more than half of Japan's 100 largest manufacturers are customers. Pricing is on request. — [SiliconANGLE](https://siliconangle.com/2026/09/16/caddi-raises-114m-at-1-2b-valuation-to-bring-manufacturing-ai-to-north-america/); [G2 pricing page](https://www.g2.com/products/caddi-drawer/pricing)

**Construction electrical takeoff/estimating (SparkQuote guide, updated 31 Oct 2026; prices checked 15–18 Oct 2026)**
- Drawer AI reads the legend, detects devices, links them to panels and circuits, routes home runs and sizes wire (voltage drop, derating). It outputs Excel plus a marked-up PDF. Price is unpublished; it does not produce a bid price. — [SparkQuote guide](https://sparkquote.ai/guides/best-ai-electrical-takeoff-software)
- Trimble Accubid LiveCount AI recognizes and counts receptacles, switches and fixtures. Trimble says it has detected 3M+ symbols, which is a volume figure, not accuracy. It is available only in Accubid Anywhere and Classic Estimating Essentials. — [SparkQuote guide](https://sparkquote.ai/guides/best-ai-electrical-takeoff-software)
- Prices from the same guide:
  - STACK: from $299/user/month.
  - Togal.AI: $299/user/month billed yearly (custom pricing for 4+ users).
  - BuildVision: Pro $299/month (up to 5 users, 50K tokens), Max $599/month.
  - PlanSwift: $2,000 per seat/year (Essential) or $3,000 (Core).
  - Bluebeam: Revu Complete $440/user/year; Max $590/user/year at the introductory price.
  - Countfire: rated 4.8/5 on Capterra (243 reviews), price unpublished.

  The guide says no vendor publishes an independent accuracy test and advises "Treat Max counts as a check, not final bid quantities". — [SparkQuote guide](https://sparkquote.ai/guides/best-ai-electrical-takeoff-software)
- Kreo (current pricing page), billed annually: Essential $100/user/month with no AI; Pro $175; Business $250 (minimum 5 seats, $15,000/year). AI auto symbol counting, AI scale detection and auto measure are on Pro and above. The Auto Measure API is an $840/year add-on on Pro. — [Kreo pricing](https://www.kreo.net/pricing)
- Togal: its "98% accuracy" claim is marketing. Its electrical page says it counts fixtures, devices and distribution equipment, and pricing happens elsewhere. G2 rates it 4.8 (60 reviews). Some Trustpilot reviewers report a gap between marketing and capability ("Overpriced, Under-Delivered"). — [Togal electrical](https://www.togal.ai/trade/electrical-takeoff-software); [G2](https://g2.com/products/togal-ai/reviews/togal-ai-review-9837102); [Trustpilot](https://at.trustpilot.com/review/www.togal.ai)
- Beam AI sells annual licenses: "Do It Yourself" from about $8,000 per trade and "Done For You" about $25,000 (snippet). — [Drawer AI blog comparison](https://drawer.ai/blog/6-best-automated-electrical-takeoff-software-for-2026)
- A done-for-you electrical takeoff service charges $0.02/sq ft, from $49, with no subscription. — [electricaltakeoffsoftware.com](https://www.electricaltakeoffsoftware.com/)
- Non-AI estimating incumbents: ConEst IntelliBid Pro about $1,950/user/year; Electrical Bid Manager $1,549–4,549 (snippet). — [Electrical estimating software comparison](https://www.electricaltakeoffsoftware.com/blog/electrical-estimating-software)

**LLMs for PLC code**
- A Control.com test found ChatGPT's ladder logic diagrams were not usable, though its text explanations helped. — [Control.com](https://control.com/technical-articles/can-openai-chatgpt-generative-ai-be-used-for-control-system-programming/)
- An academic paper on RAG-enhanced LLM PLC code generation reports about 60% compilation success on Siemens TIA Portal and CODESYS. — [arXiv 2511.09122](https://www.arxiv.org/pdf/2511.09122)
- Industry vendor blogs advise using AI for search, drafting and documentation, with mandatory engineer review and simulation testing. Safety-related logic should go only to vendor docs and certified safety engineers. — [IMD: hallucination risks](https://industrialmonitordirect.com/blogs/knowledgebase/plc-ai-assistant-hallucination-risks-and-verification-strategies); [IMD: LLMs for PLC limitations](https://industrialmonitordirect.com/blogs/knowledgebase/using-llms-for-plc-programming-practical-use-cases-and-limitations)

### Inferences
- The well-funded AI takeoff tools (Togal, STACK, Kreo, Trimble, Drawer) target building floor plans: counting outlets and luminaires per room. They are not built for industrial control-panel schematics, where the BOM comes from device tags, part numbers, terminal strips and wire lists. That leaves a niche: industrial and LV panel schematic/SLD → BOM → quote. Switchonomy is the only directly comparable product found, and it is India-focused with an Indian component database.
- ECAD vendors (EPLAN, WSCAD) do one-click BOMs only once the project is already intelligent in their tool. PDF and legacy drawings remain the gap. That supports both SpecFlow (read the PDF) and a "PDF → intelligent ECAD project" conversion service.
- The SaaS price anchor for buyers is about $100–300/user/month. A low-volume Israeli panel builder or contractor might prefer pay-per-job (per drawing set) over yet another subscription. That favors a service plus tool hybrid.
- AI for PLC code is currently assistant-grade (about 60% compile success in research). An offer should frame AI as accelerating documentation, I/O lists, tag databases, code review and commenting, with a licensed or certified human owning the logic.

### Gaps
- Independent accuracy benchmarks for any AI takeoff or schematic-reading tool were not found.
- Prices for Siemens Industrial Copilot, Eplan Copilot, WSCAD, Switchonomy, Drawer AI and CADDi are not public. AutoCAD, AutoCAD Electrical and EPLAN license prices were not verified in this pass.
- I found no tool that reads Hebrew-annotated Israeli SLDs, and no Israeli competitor to SpecFlow.

## 4. PLC and industrial automation services: rates for programming, documentation, HMI/SCADA and AI predictive-maintenance pilots

### Takeaway
In 2026 US freelance and integrator PLC rates cluster at $75–150/hr: about $75–125 freelance, $100–150 on-site, $125–150 for OEMs and large integrators, and up to $300 for specialists. The UK is £75–120/hr on-site. India is about $50–100 per day. A common sizing rule is about 1 programming hour per I/O point. No public Israeli ILS rates were found; Israeli demand is visible through job ads for Siemens and Unitronics programmers. AI predictive maintenance is sold as quote-based, per-machine subscriptions; third-party estimates are about $50–200 per machine per month.

### Cited Findings
- Industrial Monitor Direct guide (18 Apr 2026, US unless noted):
  - In-house programming $50–75/hr in one table and $70–100/hr in another; on-site service $100–150/hr.
  - OEM and large integrators $125–150/hr; freelance $75–125/hr; specialized or contract $75–300/hr.
  - Out-of-town $150–200/hr plus expenses; panel build plus programming $50–100/hr; nights, weekends and holidays 1.5×.
  - Brazil about $75–90/hr; India $50–100/day.
  - Budget 30–50% of programming time for debug and startup.

  — [IMD PLC rates guide](https://industrialmonitordirect.com/blogs/knowledgebase/plc-programming-rates-freelance-developer-pricing-guide)
- IMD estimation article (5 May 2026):
  - About 1 hour of programming per I/O point, so a 350-I/O system needs about 350 h for a new file.
  - US/Canada field service $50–75/hr; on-site programming $75–120/hr.
  - UK service £34–75/hr; on-site programming £75–120/hr.
  - Minimum call-out 2–4 h; one-off project premium 25–50%; repeat-customer discounts 10–40%.

  — [IMD 1-hour-per-I/O rule](https://industrialmonitordirect.com/blogs/knowledgebase/plc-programming-rate-estimation-1-hour-per-io-point-rule)
- ZipRecruiter: "PLC automation contract" pay averages $33.79/hr in the US (30 May 2026), with most between $30.29 and $37.50. This is W-2-style pay, not a business billing rate. — [ZipRecruiter](https://www.ziprecruiter.com/Jobs/Plc-Automation-Contract/2)
- PayScale: PLC programmer in Detroit averages $28/hr, 75th percentile $47.50 (2026). — [PayScale](https://www.payscale.com/research/US/Job=PLC_Programmer/Hourly_Rate/6b7339ae/Detroit-MI-Programmable-Logic-Controllers-PLC-Automation)
- Control Engineering's 2026 salary survey (218 responses) reports an average salary of $117,395, down from $119,682 in 2025. — [Control Engineering 2026 survey](https://www.controleng.com/results-are-in-control-engineering-career-and-salary-survey-2026/)
- A control.com forum post sought experienced PLC contractors at about $45/hr and up. (older forum data) — [control.com forum](https://control.com/forums/threads/55714)
- Freelance PLC/HMI/SCADA services are sold on Cad Crowd, Fiverr and Freelancer; gig prices were not captured. — [Cad Crowd PLC programming](https://www.cadcrowd.com/manufacturing-services/plc-programming); [Fiverr PLC gig example](https://fiverr.com/cullengilfillan/engineer-robust-plc-programs-for-your-applications); [Freelancer PLC/SCADA](https://www.freelancer.com.co/hire/plc-scada)
- Israel: control and automation job ads ask for 3–5+ years of PLC experience, Siemens TIA and Unitronics, industrial protocols, and SCADA/DCS. Some field roles require an electrician's license. No ILS figures were published. — [Drushim: control & automation engineer](https://www.drushim.co.il/job/38596109/4f0c2ae8/); [AllJobs: PLC programmer & control engineer](https://www.alljobs.co.il/m/p/jobs/8358535)
- AI predictive maintenance:
  - Augury (Israeli-founded) is quote-based. Third parties describe either a turnkey annual per-machine service including hardware, installation and support, or SaaS per machine plus enterprise fees. — [SpotSaaS Augury pricing](https://www.spotsaas.com/product/augury/pricing); [SoftwareFinder Augury](https://softwarefinder.com/facility-management-software/augury)
  - A generic pricing-strategy article estimates $50–200 per asset per month for AI predictive maintenance (not Augury-specific, unverified). — [Monetizely](https://www.getmonetizely.com/articles/how-do-manufacturers-price-ai-predictive-maintenance-solutions)
  - An Augury case study (vendor) reports a hospital avoided over $750K in maintenance costs in 12 months. — [CaseStudies.com Augury](https://www.casestudies.com/company/augury/case-study/top-ranked-hospital-remained-operational-to-save-lives-by-implementing-augurys-technology)

### Inferences
- For Leon, PLC work is more premium and less commoditized than drafting: it is site-bound, safety-critical and platform-specific. Offshore India at $50–100/day competes mainly on remote coding and documentation, not commissioning.
- Productizable, AI-accelerated PLC services that avoid owning safety logic:
  - Documentation and as-built packs: I/O lists, tag databases, cause-and-effect matrices, commented code.
  - Migration assessment, e.g. legacy to Siemens TIA or Unitronics.
  - Code review.
  - Drawing ↔ PLC I/O cross-check.

  The 1 h/I/O rule lets him quote fixed prices per I/O count.
- An "AI predictive maintenance pilot" for Israeli plants competes with well-funded vendors (Augury and others). A small studio's credible angle is vendor-neutral pilot scoping, sensor and data integration with existing PLC/SCADA, and ROI reporting, not building its own PdM platform. This is inference.

### Gaps
- No Israeli PLC/automation freelance or integrator rates in ILS were found. I&C integrator day rates in Israel remain unknown.
- No public HMI/SCADA per-screen or documentation-only rates were found.
- No published PdM pilot prices were found; the per-machine figures are unverified third-party estimates.
- Reddit r/PLC opinion was not captured directly; only proxies (Control.com, IMD, arXiv) were found.

## 5. Where is demand strongest, what is commoditized vs premium, and what would a credible productized offer look like?

### Takeaway
Commoditized: plain drafting, redraws and PDF→DWG ($2.5–15/page; $5–25/hr offshore), and generic floor-plan device counts, already automated by $100–300/month SaaS. Premium: fast, accountable and standards-aware packages for industrial and LV panels, such as SLD/schematic → BOM → priced quote, legacy → intelligent ECAD, and BOQ/estimates for tenders. Fast turnaround and engineer sign-off sharply raise price. The evidence supports offers like "Electrical panel PDF → BOM + Excel quote within 24h" aimed at Israel's roughly 110 certified panel assemblers, design offices and integrators, with fixed per-project pricing. Schematiq (48h, engineer-signed) and Switchonomy (SLD→BOM→quote) show the model is being sold. Neither is localized for Israel.

### Cited Findings
- Speed premium: one-day conversion costs $140–690/sheet against $35–140/sheet at 4–6 weeks. — [Cad Crowd blog (2024)](https://www.cadcrowd.com/blog/what-are-autocad-designer-rates-drafting-costs-services-company-pricing/)
- Low end: India electrical drafting from $9/hr; PDF→EPLAN gigs $7–10/page; Upwork budgets $5–20/hr. — [Outsource2India](https://www.outsource2india.com/engineering/electrical/electrical-2d-drafting-services.asp); [Fiverr em_design_ins](https://fiverr.com/em_design_ins/convert-pdf-electrical-schematics-into-professional-eplan-p8-projects); [Upwork job](https://www.upwork.com/freelance-jobs/apply/Autocad-Drafter-for-MEP-Plans_~022074272547833576935/)
- Productized AI-plus-engineer service: fixed quote in 4 business hours, 48h delivery, native ECAD plus BOM plus compliance report plus sign-off. — [Schematiq](https://schematiq.org/)
- Productized panel estimation SaaS: SLD → BOM → quote from a component price database. — [Switchonomy](https://panelestimation.com/)
- Takeoff SaaS anchors: Kreo AI tiers $175–250/user/month; Togal and STACK $299/user/month. Done-for-you takeoff at $0.02/sq ft from $49. — [Kreo pricing](https://www.kreo.net/pricing); [SparkQuote guide](https://sparkquote.ai/guides/best-ai-electrical-takeoff-software); [electricaltakeoffsoftware.com](https://www.electricaltakeoffsoftware.com/)
- Accuracy caution: no vendor publishes independent accuracy tests, and AI counts should be checks, not final bid quantities. AI accuracy falls on poor scans and hand-drafted plans. — [SparkQuote guide](https://sparkquote.ai/guides/best-ai-electrical-takeoff-software); [Togal review aggregator](https://b2bsalestools-com.pages.dev/tools/togal-ai/)
- The Israeli public-sector anchor for BOQ/estimate work is 10% of the electrical design fee, where the base fee is 3.1–11.9% of installation value depending on size and complexity (MOD tariff, Aug 2020). — [MOD tariff 2.9.1](https://www.online.mod.gov.il/Online2016/Documents/General/Binuy/forms/2020/2_9_1.pdf)
- Israeli demand signals: about 110 certified panel assemblers; design offices continuously hiring drafters with 3+ years of AutoCAD Electrical; about 100 data-center bids under a 200 MW cap. — [SII](https://www.sii.org.il/he/lobby/lab-tests-search/laboratory-test/electrical-panel/); [Drushim ad](https://www.drushim.co.il/job/38975197/c18d38f5/); [Ynet](https://www.ynetnews.com/business/article/bjn8umhpze); [DCD](https://datacenterdynamics.com/en/news/israel-to-cap-capacity-of-new-data-centers-at-200mw-report)

### Inferences (offer design; all pricing below is the researcher's estimate, not sourced market data)
- **Strongest-fit offer (flagship): "Panel schematic/SLD PDF → BOM + priced Excel quote within 24h"** for Israeli panel builders and electrical contractors bidding on tenders. It uses SpecFlow plus Leon's human review. Differentiators:
  - Hebrew and Israeli-supplier price lists.
  - SI/IEC 61439 awareness.
  - Licensed electrician and I&C background.
  - Tender-deadline speed.

  Price per project, tiered by sheet count or panel count, with a rush fee. Benchmarks: global rush drafting at $140–690/sheet; MOD BOQ slice of about ₪6K on a ₪1M installation. A plausible starting band is roughly ₪1,500–5,000 per panel set (estimate; needs validation with 5–10 Israeli panel builders).
- **Second offer: "Legacy panel drawings (PDF/scan/dumb DWG) → intelligent AutoCAD Electrical/EPLAN project"** with wire numbers, cross-references and BOM. This sits in the 2–4 h/page band, which is premium compared with $7–10/page "dumb" conversion. Offshore partners can do the redraw while Leon does the QA and engineering checks.
- **Third offer: BOQ/כתב כמויות and cost estimates from electrical tender drawings,** subcontracted to design offices and contractors. This is anchored to the 10% BOQ slice of the design fee.
- **Fourth offer: PLC/I&C documentation packs** (I/O lists, tag databases, loop diagrams, cause-and-effect matrices, as-builts, commented code, code review), priced per I/O point. Avoid selling AI-written safety logic, given the evidence on LLM reliability.
- **Commodity to avoid as a headline:** generic "AutoCAD drafting / PDF→DWG". Offshore competition sets the price at $10–20/hr or a few dollars per page. Offer it only as an add-on.
- **AI predictive-maintenance pilot:** credible only as vendor-neutral scoping and integration (connecting existing PLC/SCADA data). Israeli PdM vendors are well funded; a small studio should not compete on platform.
- **Positioning risk:** the "AI did it" claim needs a human-accountability layer (Schematiq's sign-off model). Licensing determines which deliverables Leon may sign; another researcher covers Israeli law. Showing accuracy on sample sets, such as a published before/after BOM comparison, would differentiate, since competitors publish no accuracy data.

### Gaps
- No direct evidence of willingness to pay among Israeli panel builders or contractors for outsourced BOM/quote work; customer interviews are needed.
- No data on how many tenders per year Israeli panel builders bid on, or on time spent per quote.
- No sourced ILS/USD conversion was gathered; use the current rate when converting.
