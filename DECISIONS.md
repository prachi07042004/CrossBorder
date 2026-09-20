# Decision Log

Architecture Decision Records for this project. Newest entries at the bottom. See `docs/WORKING_PRINCIPLES.md` for when an entry is required. Each entry: what we decided, why, what we considered instead, and what it's based on — so a decision can be revisited later without re-deriving the reasoning from scratch.

Entries 001-010 were made during planning (before any code existed) and are recorded here retroactively, sourced from `docs/System_Design_and_Requirements.md`. Everything from 011 onward is logged as it happens.

---

### ADR-001: Modular monolith, not microservices
- **Decision:** Ingestion, expense classification, RAG retrieval, the deterministic tax engine, and the audit-risk scorer are Python packages inside one FastAPI service — not separately deployed services.
- **Why:** Two-person team, one semester, single deployment target. Microservice boundaries add operational overhead (service discovery, inter-service auth, separate deploys) with no corresponding benefit at this scale.
- **Alternatives considered:** Microservices per module — rejected as unrewarded complexity for this team size.
- **Source:** `System_Design_and_Requirements.md` §3, §7.

### ADR-002: PostgreSQL + pgvector as the only datastore
- **Decision:** Vector embeddings live in the same Postgres instance as relational data (transactions, computations, citations), via the pgvector extension.
- **Why:** One database to operate instead of two. A dedicated vector DB's advantages (Pinecone, Weaviate) only show up past corpus sizes this project won't reach.
- **Alternatives considered:** Pinecone, Weaviate, Chroma — rejected.
- **Source:** `System_Design_and_Requirements.md` §6.

### ADR-003: Free/self-hosted embedding model by default
- **Decision:** Default to BGE-M3 or Nomic Embed Text v1.5 (free, CPU-capable) for embeddings; a paid API (Voyage, OpenAI) is a fallback only if retrieval eval shows the free model is inadequate.
- **Why:** Small, curated corpus — no evidence yet that a premium embedding model is needed, and it removes a per-query cost variable on a student budget.
- **Alternatives considered:** OpenAI text-embedding-3-large, Gemini embedding-001 — deferred pending evidence, not rejected outright.
- **Source:** `System_Design_and_Requirements.md` §6, citing premai.io embedding model comparison (2026).

### ADR-004: No reranker in v1
- **Decision:** Ship hybrid BM25+vector retrieval without a cross-encoder reranker; add one only if the retrieval eval (recall@3 vs recall@50) shows ordering, not recall, is the bottleneck.
- **Why:** Rerankers only pay off when recall@50 is good but recall@3 ordering is poor — an empirical question, not something to assume upfront.
- **Source:** `System_Design_and_Requirements.md` §6-7, citing reranker guidance (folarin.dev, 2026).

### ADR-005: No model fine-tuning, no self-hosted LLM
- **Decision:** All LLM use (classification, grounded generation) goes through one hosted API, prompted, never fine-tuned or self-hosted.
- **Why:** Confirmed by the Austrian VAT RAG-vs-fine-tuning paper (RAG wins on auditability); also matches this team's ops capacity — no GPU infra to run or maintain.
- **Source:** `System_Design_and_Requirements.md` §6-7.

### ADR-006: Single-instance Docker Compose deployment
- **Decision:** One `docker-compose.yml` (db, backend, frontend), deployed identically in dev and production, on one cloud instance (PaaS free/hobby tier or a small VM).
- **Why:** Matches the synopsis's explicit "single cloud-hosted instance" requirement; no traffic pattern here needs autoscaling or multi-region.
- **Source:** `System_Design_and_Requirements.md` §9; original project synopsis.

### ADR-007: Hand-crafted synthetic personas, not PaySim, as seed data
- **Decision:** Use 4-6 hand-crafted freelancer/consultant personas with known-correct tax outcomes; use PaySim only (if at all) as a transaction-schema reference, not as actual seed data.
- **Why:** PaySim is a fraud-detection dataset (cash-in/cash-out/transfer patterns); it can't provide the tax-correct ground truth needed to test the deterministic engine.
- **Source:** `Implementation_Plan.md` §4, §6.

### ADR-008: Hybrid BM25 + vector retrieval, not vector-only
- **Decision:** Retrieval combines keyword (BM25) and vector similarity search.
- **Why:** Pure vector search consistently misses exact statutory terms and section numbers in the research reviewed (`Tax-Authority-RAG`, general legal RAG literature).
- **Source:** `System_Design_and_Requirements.md` §1, §6.

### ADR-009: Document chunks are tagged with jurisdiction, effective_date, and tax_year, filtered before ranking
- **Decision:** Every `document_chunks` row carries `jurisdiction`, `effective_date`, `tax_year`; retrieval filters on these before vector/BM25 ranking runs, not after.
- **Why:** Directly addresses the temporal-misgrounding failure mode (retrieving the wrong tax year's rule) identified in the "Temporal Misgrounding in Legal RAG" paper (arXiv:2608.09393).
- **Source:** `System_Design_and_Requirements.md` §1, §5.

### ADR-010: The LLM never performs arithmetic
- **Decision:** All tax computation (44ADA presumptive income, DTAA Article 15/25 relief) happens in deterministic, unit-tested Python (Pydantic/SQLAlchemy) code. The LLM's role is limited to classification and retrieval/citation.
- **Why:** Field-standard pattern for legal/tax AI; keeps the highest-stakes output (a tax number) auditable and testable independent of model behavior.
- **Source:** Original project synopsis; `System_Design_and_Requirements.md` §1.

---

### ADR-011: Local dev runs via Docker volume mounts + hot reload, not a host-side venv
- **Date:** 2026-09-17
- **Decision:** `docker-compose.yml` mounts `./backend` and `./frontend` straight into their containers and runs `uvicorn --reload` / `next dev`, instead of requiring a Python venv or local `npm install` on the host. `docker compose up --build` is only needed when `requirements.txt`, `package.json`, or a Dockerfile changes; plain `docker compose up` picks up ordinary code edits live.
- **Why:** The team wants a Docker-only workflow, and the original compose file baked code into the image at build time (`COPY . .`), meaning every edit needed a rebuild. Volume-mounting the source is the standard fix and keeps everything inside Docker as requested — no host-side Python/Node environment required at all.
- **Alternatives considered:** A host venv + `npm install` for local iteration, with Docker only for the "does this deploy" check — works, but means keeping two environments in sync (host and container) for no benefit once hot reload is available.
- **Trade-off accepted:** The frontend build now targets the Dockerfile's `deps` stage (pre-build, has `node_modules`) rather than the final `runner` stage used for an actual deploy — so this compose file is a *dev* configuration. Before the Phase 0 cloud deploy step (`System_Design_and_Requirements.md` §9.5), we'll need a production-style compose/deploy config that uses the full multi-stage build instead. Tracked in `PROGRESS.md`.

### ADR-012: Persona C's US-side tax figure is a flat-rate placeholder, not an IRC-verified computation
- **Date:** 2026-09-17
- **Decision:** In `docs/personas.md`, Persona C (Meera, crosses the DTAA 90-day line) uses an assumed flat 30% effective US federal rate on her US-taxable presumptive income, at an assumed Rs. 83 = $1, to produce an illustrative US-tax figure for testing the Article 25 credit *mechanism*.
- **Why:** Article 25 relief requires knowing the actual US tax paid, which depends on 26 U.S.C. Section 871(b)/872 and Form 1040-NR mechanics (graduated rates on a nonresident alien's net effectively-connected income) -- a body of US tax law this project has not researched or verified. Inventing a precise figure without that research would violate `WORKING_PRINCIPLES.md` rule 3. A flat, clearly-labeled placeholder lets the credit-capping logic (`min(US tax paid, India tax attributable)`) be tested without pretending the US-side number is verified law.
- **Alternatives considered:** Doing the full NRA-taxation research now -- rejected for this pass as a real scope expansion; deferred until/unless the tax engine needs to actually compute US tax rather than just apply a credit cap to a given figure.
- **Source:** `docs/personas.md`, Persona C.

### ADR-013: Persona D apportions presumptive 44ADA income by gross-receipts ratio, not statute
- **Date:** 2026-09-17
- **Decision:** In `docs/personas.md`, Persona D (Devika, Article 15(1)(a) fixed-base branch) apportions her lump-sum 44ADA presumptive income to the US-attributable share using the same ratio as her underlying gross receipts by engagement (37.5% in her case).
- **Why:** Section 44ADA produces one deemed income figure from total gross receipts; it does not decompose by client or engagement, and neither the Income-tax Act nor the India-US DTAA text specifies how to reconcile a presumptive-taxation regime with Article 15(1)(a)'s "income attributable to the fixed base" language. No worked example exists in either primary source. Gross-receipts pro-ration is a reasonable, defensible modeling choice, but it is a choice this project is making, not a verified rule -- documented here so it isn't silently treated as settled law later.
- **Alternatives considered:** Treating the full presumptive income as either fully attributable or fully non-attributable to the fixed base (simpler, but ignores the treaty's explicit apportionment requirement); none of these alternatives are backed by primary-source guidance either.
- **Source:** `docs/personas.md`, Persona D.

### ADR-014: A firm on 44ADA cannot additionally deduct partner remuneration under Section 40(b)
- **Date:** 2026-09-17
- **Decision:** In `docs/personas.md`, Persona E (Sharma & Associates, partnership firm) treats 44ADA's presumptive income as the firm's final taxable business income, with no further deduction for partner remuneration under Section 40(b) -- even though the remuneration figure used would fit comfortably within Section 40(b)'s own cap under normal computation.
- **Why:** Section 44ADA(2) deems all sections-30-to-38 deductions "already given full effect to" within the presumptive figure and allows no further deduction under those sections, with no proviso for firms. By direct comparison (all three sections read from the current consolidated 1961 Act text): Section 44AD(2) (general business) has the identical "no further deduction" language with no carve-out; Section 44AE(3) (goods carriage) has an explicit proviso -- "where the assessee is a firm, the salary and interest paid to its partners shall be deducted... subject to the conditions and limits specified in clause (b) of section 40." The 2025 Act's Section 58(5) carries the exact same asymmetry forward (carve-out scoped to "Table: Sl. No. 2", the 44AE successor, only). Since the carve-out demonstrably exists elsewhere in the same family of provisions, its absence from 44AD and 44ADA is textual evidence of intent, not an oversight this project is filling in by assumption.
- **Alternatives considered:** Allowing the remuneration deduction on top of the presumptive figure (matches how a firm would compute under normal provisions) -- rejected because nothing in 44ADA's text supports it, and the 44AE contrast argues affirmatively against it, not just by silence.
- **Caveat:** This is a structural/textual inference cross-checked across three sections and two Acts, not an explicit statutory statement or case law. If this project needs stronger confidence than that (e.g. for anything beyond a class project), it would need a CBDT circular or judicial precedent, not just this reading.
- **Source:** `docs/personas.md`, Persona E; `corpus/india/it-act-section-40b/2025-26.txt`; `corpus/india/it-act-2025-section-58/2026-27.txt`.

### ADR-015: Corpus and personas now explicitly span both the Income-tax Act, 1961 and the Income-tax Act, 2025
- **Date:** 2026-09-17
- **Decision:** The project's scope is expanded from "the Income Tax Act" (treated generically) to explicitly cover two distinct Acts: the Income-tax Act, 1961 (in force through FY2025-26) and the Income-tax Act, 2025 [No. 30 of 2025] (in force from FY2026-27 onward, repealing the 1961 Act). Both are maintained as parallel, separately-tagged corpus threads rather than one superseding the other in place.
- **Why:** India enacted a new Income-tax Act effective 1 April 2026. All work in this project prior to this decision implicitly assumed "the Income Tax Act" meant the 1961 Act only. Since the current tax year (FY2026-27, per the environment's clock) is already governed by the new Act, silently continuing to treat the 1961 Act as current would itself be a temporal-misgrounding bug -- the exact failure mode ADR-009's metadata design exists to prevent. This decision makes that design apply across Acts, not just across dates within one Act.
- **What changed concretely:** New corpus documents for the 2025 Act's Section 58 (consolidates 44AD/44AE/44ADA), Section 35(e) (successor to Section 40(b)), and Section 62(4) (successor to Section 44AA(1)) -- see `corpus/README.md`. Section numbers do not map between the two Acts (a trap documented in `corpus/README.md`); each corpus directory is named per-Act to avoid collision.
- **Not yet done:** No persona is dated FY2026-27 / built against the 2025 Act yet -- tracked in `docs/personas.md`'s "Still open" section. `Implementation_Plan.md` and `System_Design_and_Requirements.md` (Claude Project docs, referenced generically as "the Income Tax Act") have not yet been updated to reflect this dual-Act scope.
- **Alternatives considered:** Treating the 2025 Act as out of scope / future work only -- rejected per explicit direction ("i think we should consider the latest act") once the new Act's existence and current-year applicability were confirmed.
- **Source:** `corpus/india/it-act-2025-section-58/2026-27.txt`, `-35e/`, `-62/`; `corpus/README.md`.

### ADR-016: The Income-tax Act, 2025 is the project's default legal base going forward; the 1961 Act is retained as prior-year support, not as "the real one"
- **Date:** 2026-09-20
- **Decision:** Any new persona, demo query, or default assumption (when a tax year isn't specified) uses the Income-tax Act, 2025. The 1961 Act corpus is kept, not archived or removed -- it's what any FY2025-26-or-earlier query needs, and it's the concrete evidence that the project's temporal-filtering design (ADR-009) actually does something.
- **Why:** The new Act being amended annually by future Finance Acts was raised as a concern for adopting it as the base. It isn't a reason to hold off: the 1961 Act was amended just as often (Section 40(b)'s cap changed in 2009 and again in 2024; 44ADA's threshold changed in 2023), and ADR-009's `effective_date`-level tagging already exists specifically to handle exactly that. The Income-tax Act, 2025 replacing the 1961 Act from FY2026-27 is simply another instance of the same versioning problem this project already built for, not a new category of problem.
- **Working convention adopted:** don't fork a new corpus file for every incremental Finance Act tweak -- only when an amendment changes a figure or rule an in-scope computation actually depends on. Note the amendment inline in that file's metadata (as already done in `corpus/india/it-act-section-40b/2025-26.txt` and `-35e/2026-27.txt`), matching how the source 2025 Act PDF itself is already versioned ("as amended by FA Act 2026").
- **What's kept, and why:** Section 536 of the 2025 Act preserves pending 1961-Act matters (litigation, assessments in progress) -- a real reason the 1961 Act isn't simply obsolete, though no current persona models a pending-litigation scenario, so this is documented as a talking point rather than built out.
- **Alternatives considered:** Treating the 1961 Act as legacy/deprecated and only maintaining the 2025 Act going forward -- rejected because a real filer very often files for the prior year, and because it would make the project's own temporal-versioning claim untestable (nothing left to filter between).
- **Source:** user direction, 2026-09-20; `corpus/india/it-act-section-90/2025-26.txt`, `corpus/india/it-act-2025-section-159/2026-27.txt` (added the same session, as evidence the dual-Act pattern continues to be followed rather than just declared).

### ADR-017: Residential status (Section 6) is an explicit out-of-scope input, not computed
- **Date:** 2026-09-20
- **Decision:** Every persona states "resident in India" as a given fact. This project does not implement Section 6's residency-determination logic (the 182-day / 60-day-plus-365-day tests, the "not ordinarily resident" sub-classification, or the >Rs. 15L-income deemed-residency rule) in v1. This mirrors how FR-14 already excludes non-US treaties: it's a formal non-goal, not a silent gap.
- **Why:** Residential status is a precondition for 44ADA and Article 15 to apply at all, but it's a self-contained body of law separate from this project's actual thesis (presumptive taxation + DTAA relief), and building it out is real, uncosted scope for a two-person, 15-week project. The alternative -- leaving it as a silently-assumed fact with no documentation -- was flagged as a real gap once raised, and this ADR is the fix: make the boundary explicit rather than just hoping nobody notices it.
- **What was done instead of building it:** Section 6 was curated once (`corpus/india/it-act-section-6/2025-26.txt`) for a single purpose -- sanity-checking that Persona C's stated facts aren't self-contradictory. Result: her 110 US days still leaves ~255 days in India, clearing the 182-day threshold (sub-clause (1)(a)) on its own, so her premise holds. That file is explicitly marked as not wired into any computation, to avoid it being mistaken later for a built capability.
- **Alternatives considered:** Building a lightweight basic-day-count-only check (skipping the NOR sub-classification) as real Phase 1 scope -- available if priorities change, but not taken now. Leaving the assumption undocumented -- rejected as the least honest option once the gap was identified.
- **Source:** user direction, 2026-09-20; `corpus/india/it-act-section-6/2025-26.txt`; `docs/personas.md` Persona C.

### ADR-018: Closed two verification gaps surfaced by a pre-commit review (Rule 128 method ambiguity; Persona F's uncurated citation)
- **Date:** 2026-09-20
- **Decision:** Before committing the 2026-09-17/09-20 batch of corpus and persona work, two gaps flagged by a review were closed rather than committed as-is: (1) `corpus/india/it-rules-rule-128/2025-26.txt` claimed "direct visual page-read" without stating whether the qpdf-split workaround (required because its ~104MB source PDF exceeds the page-image tool's 100MB limit -- the same condition that caused three other files' overstated claims, already caught and fixed) had actually been used; (2) `docs/personas.md` Persona F's central conclusion (Karan falls through to Section 44AD instead of a flat 44ADA rejection) rested on Section 44AD(6)'s exclusion list, which had never itself been added to `corpus/` -- only recalled.
- **Why:** Both are exactly the failure mode `WORKING_PRINCIPLES.md` rule 3 exists to prevent: a load-bearing legal claim resting on something other than verified primary-source text. Neither was safe to commit silently.
- **What was done:** Rule 128 re-checked via a qpdf-split single-page PDF read directly as a page image -- word-for-word match, no discrepancy, ambiguity resolved (see the file's own `verification_confirmed (2026-09-20)` note). Section 44AD (full text, sub-sections 1-6 and Explanation) added as a new corpus file (`corpus/india/it-act-section-44ad/2025-26.txt`), sourced and visually confirmed from the same 1961 Act PDF used for the other 1961-Act files -- sub-section (6)'s exclusion list matches word-for-word what Persona F had assumed. `docs/personas.md` updated to cite the real file.
- **Not yet done:** The same verification-method ambiguity plausibly affects the four Income-tax Act, 2025 corpus files (`it-act-2025-section-58`, `-35e`, `-62`, `-159`) -- all claim "direct visual page-read" from a source PDF whose size was never recorded, dated the same batch as the files that turned out to be overstated. This could not be re-checked in this pass because the source PDF (`Income_Tax_Act_2025_as_amended_by_FA_Act_2026.pdf`) is no longer available in either the cloud workspace or the connected project folder -- it will need to be re-supplied before this is closed out. Tracked in `PROGRESS.md` and `docs/personas.md`'s "Still open" list.
- **Source:** pre-commit review, 2026-09-20; `corpus/india/it-rules-rule-128/2025-26.txt`; `corpus/india/it-act-section-44ad/2025-26.txt`; `docs/personas.md` Persona F.

### ADR-019: Closed the remaining ADR-018 gap (2025-Act files) once the source PDF was re-supplied; recorded a genuine Act drafting anomaly
- **Date:** 2026-09-20
- **Decision:** Re-checked all four Income-tax Act, 2025 corpus files (`it-act-2025-section-58`, `-35e`, `-62`, `-159`) against the re-supplied source PDF via genuine direct visual page-image read. No discrepancy found against the previously committed text in any of the four.
- **Why this was worth doing even though nothing was known to be wrong:** ADR-018 flagged that these four files carried the same "direct visual page-read" claim as three files that had turned out, on inspection, to be pdftotext-only (source PDF over the page-image tool's 100MB limit). The source PDF wasn't available to check at the time, so the claim was left as an open, unresolved risk rather than assumed fine.
- **What was found:** The risk didn't actually apply here -- the source PDF is ~3.1MB, nowhere near the 100MB threshold that caused the earlier problem, so there was no structural reason for these four to have been mis-verified. Independent re-confirmation still turned up zero discrepancies against the committed text.
- **One new observation, not a discrepancy:** Section 58(5) and (7) both reference "the income computed under sub-section (1)", but sub-section (1) only disapplies sections 26-54 -- the actual computation happens in sub-section (2)'s Table. Confirmed on the rendered page image itself, not a pdftotext or transcription artifact. Likely inherited from 1961-Act Section 44AE(3)'s identical phrasing (correct there, since 44AE's own sub-section (1) does compute the figure) without the cross-reference being updated for Section 58's different structure. Documented in `corpus/india/it-act-2025-section-58/2026-27.txt`'s `cross_reference_anomaly` note; doesn't change any persona's conclusion.
- **Source:** re-supplied `Income_Tax_Act_2025_as_amended_by_FA_Act_2026.pdf`; `corpus/india/it-act-2025-section-58/2026-27.txt`, `-35e/`, `-62/`, `-159/`; ADR-018.

### ADR-020: Formal corpus metadata schema (v1) defined and retrofitted onto all 15 corpus files
- **Date:** 2026-09-20
- **Decision:** Adopted `corpus/METADATA_SCHEMA.md` as the formal schema for the `jurisdiction`/`effective_date`/`tax_year` metadata ADR-009 depends on. Added an 11-field `schema_v1_*` block to every existing corpus document, alongside (not replacing) the existing free-text header fields.
- **Why:** This was the last unchecked item under Phase 0 in `PROGRESS.md`. The existing header fields are prose (`tax_year: "currently applicable for FY 2023-24 (AY 2024-25) through the present..."`), which has real value for a human reader but can't be filtered on by a WHERE clause the way ADR-009's "filter before ranking" design requires. The new fields are typed and comparable; the prose stays for the reasoning behind them.
- **Key design choice:** `jurisdiction` (coarse: IN / US / IN-US-DTAA, matching the DB column) is kept separate from a new `legal_instrument` field (which Act/Rules/treaty specifically) -- this is what actually disambiguates the 1961 Act from the 2025 Act, both of which are `jurisdiction: IN`. Fields are namespaced `schema_v1_*` to avoid colliding with the existing same-named free-text keys.
- **What the retrofit found:** normalizing all 15 files against the schema surfaced no new legal-accuracy problems (this was a metadata-structuring pass, not new legal research), but it did force three files' genuine unknowns into an explicit `schema_v1_ambiguous_fields` value instead of leaving them implicit in prose: Section 6's Finance-Act-2020-era sub-provisions (date not independently verified, per that file's own pre-existing header), and both DTAA articles (treaty entry-into-force date used for `effective_from`, not a separately confirmed first-applicable Indian assessment year -- these two things can differ for a treaty and this project hasn't checked).
- **Open question, not resolved:** the current `documents`/`document_chunks` DB design (`System_Design_and_Requirements.md` §4) has single `effective_date`/`tax_year` columns, not a start/end range -- fine for the still-current Income-tax Act 2025 documents, but the superseded 1961-Act documents genuinely need a range once a query asks about a past tax year. Whether to add range columns or insert one row per amendment is left as a Phase 2 ingestion-design decision, documented in `corpus/METADATA_SCHEMA.md` rather than silently assumed.
- **Source:** `corpus/METADATA_SCHEMA.md`; all 15 files under `corpus/`.

<!-- New entries go below this line, in the same format, as decisions are made during implementation. -->

### ADR-021: Split `docker-compose.yml` into a production-shaped base plus a `docker-compose.override.yml` for dev-only settings
- **Date:** 2026-09-20
- **Decision:** `docker-compose.yml` now defines the lean, deployable shape of each service (frontend built to its `runner` stage, no source volume mounts, no dev-server command overrides, `restart: unless-stopped` added). All of ADR-011's dev-convenience settings (source bind mounts, `uvicorn --reload` / `npm run dev`, the frontend's `deps` build target) moved to a new `docker-compose.override.yml`. Compose auto-merges the override file on top of the base whenever `docker compose up` is run with no extra flags, so the day-to-day local workflow is unchanged; a deploy that wants the production shape runs `docker compose -f docker-compose.yml up -d --build`, explicitly excluding the override file.
- **Why:** Flagged as a trade-off to resolve back in ADR-011 -- the dev config's frontend service targeted the `deps` build stage (just `node_modules`, nothing actually built) and ran dev servers via source mounts, neither of which is usable for the actual cloud deploy step in `System_Design_and_Requirements.md` §9.5. The base+override split is Compose's own documented pattern for exactly this dev/prod split, and keeps `docker compose up` working identically to before for local iteration.
- **Alternatives considered:** A separate, fully self-contained `docker-compose.prod.yml` alongside the untouched existing file -- simpler to reason about (no merge order to track) and was raised as the "easier under time pressure" option, but rejected in favor of the override pattern per explicit direction, accepting the trade-off that the `db` service definition isn't duplicated but the merge behavior needs to be understood once.
- **Confirmed working (2026-09-20):** `docker compose config` was run from the user's own machine and the resolved merge matches this ADR's description exactly -- `backend` picks up the `--reload` command and its source bind mount from the override, `frontend` picks up `target: deps`, `npm run dev`, and its bind mounts, and `db` is untouched by the override (as expected -- it has no `db` block). The user then ran `docker compose down` followed by `docker compose up --build` and confirmed hot reload on both services still works unchanged. The production-only path (`docker compose -f docker-compose.yml up -d --build`, excluding the override) has not yet been exercised -- that's the remaining unverified piece, needed before the actual cloud deploy step (§9.5).
- **Source:** `docker-compose.yml`, `docker-compose.override.yml`; ADR-011.

### ADR-022: `Implementation_Plan.md` and `System_Design_and_Requirements.md` updated to reflect the dual-Act scope
- **Date:** 2026-09-20
- **Decision:** Closed the gap flagged back in ADR-015 ("`Implementation_Plan.md` and `System_Design_and_Requirements.md`... have not yet been updated to reflect this dual-Act scope"). Both docs now carry a dated scope note pointing to ADR-015/016, and the specific claims that assumed a single Act are corrected: `Implementation_Plan.md` §1/§4/§8, and `System_Design_and_Requirements.md`'s FR-3, the architecture diagram, and the request-flow walkthrough.
- **Also fixed, found while doing this:** `System_Design_and_Requirements.md` §9.1 asserted "one `docker-compose.yml`... used identically in dev and in production... no separate 'prod config' to maintain" as a design principle. That's no longer true and hadn't been since ADR-011 (which already accepted the opposite trade-off) -- today's ADR-021 base+override split made the contradiction impossible to leave alone. Rewrote §9.1 to describe the actual setup, with an explicit "Correction" note rather than silently rewriting history.
- **Also added:** FR-16, a functional requirement for Persona E's finding (a firm's presumptive income is never reduced by partner remuneration) -- this was real, tested system behavior with no corresponding requirement, backwards from `WORKING_PRINCIPLES.md` rule 1's "add the requirement first" intent. Persona F's general-business routing was folded into FR-3's description rather than given its own FR, since it's a mode of the same computation, not a separate capability.
- **Why now, not earlier:** Deprioritized in favor of corpus/engine work per explicit direction at the time (see PROGRESS.md, 2026-09-17). Picked up now alongside the Phase 0 Docker Compose work, since both are "sync the formal docs with what's actually true" tasks and the §9.1 contradiction was discovered while doing this.
- **Source:** `docs/Implementation_Plan.md`, `docs/System_Design_and_Requirements.md`; ADR-011, ADR-015, ADR-016, ADR-021.
