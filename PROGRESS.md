# Progress

Living checklist mirroring the phased plan in `docs/Implementation_Plan.md` §8. Update this at the end of every work session: tick what's done, note what's next, flag what's blocked. If a step produced a decision, link the `DECISIONS.md` entry.

Status legend: `[ ]` not started · `[~]` in progress · `[x]` done

---

## Phase 0 — Setup & corpus curation (target: weeks 1-2)

- [x] Repo structure created (`backend/`, `frontend/`, `docs/`, `corpus/`, CI stub)
- [x] Planning docs mirrored into `docs/` (Implementation Plan, System Design & Requirements, SRS/SDS report)
- [x] Decision log (`DECISIONS.md`) seeded with the 10 planning-stage decisions
- [x] Working principles documented (`docs/WORKING_PRINCIPLES.md`)
- [x] Docker Compose skeleton (db + backend + frontend) — hello-world, not yet deployed to cloud
- [x] Local dev workflow switched to volume-mounted hot reload (ADR-011) — `docker compose up` (no `--build`) now picks up code edits
- [x] Production-style compose/deploy config -- `docker-compose.yml` split into a production-shaped base (frontend `runner` stage, no source mounts) plus `docker-compose.override.yml` for dev-only settings (ADR-021). **Confirmed working, both paths (2026-09-20)** -- `docker compose config`'s resolved merge matches the design; `docker compose down` + `up --build` confirmed dev hot reload still works unchanged; `docker compose -f docker-compose.yml up -d --build` confirmed the production shape builds and serves correctly (frontend `runner` stage at `localhost:3000`, backend responding at `localhost:8000`).
- [ ] Skeleton deployed to the real cloud target (see `System_Design_and_Requirements.md` §9.5) — **next concrete step**
- [x] CI workflow running lint + tests on push — confirmed green on GitHub Actions after the initial push (2026-09-17)
- [x] Source documents curated and version-tagged: Section 44ADA text, DTAA Articles 15 & 25, relevant IRS guidance (§861(a)(3)) — see `corpus/`
- [x] `jurisdiction` / `effective_date` / `tax_year` metadata schema finalized against the curated corpus -- see `corpus/METADATA_SCHEMA.md` and ADR-020

## Phase 1 — Deterministic tax engine (target: weeks 3-5)

- [x] Pydantic models for persona, transaction, tax computation -- `backend/app/tax_engine/models.py` (`PresumptiveIncomeInput`/`PresumptiveIncomeResult`, `Article15Input`/`Article15Result`, `Article25ReliefResult`); scoped to the increments built so far, not the full persona/transaction domain
- [x] Section 44ADA presumptive income calculation -- `backend/app/tax_engine/presumptive.py`; covers both Acts (`select_legal_instrument()` picks Section 44ADA vs. Income-tax Act 2025 Section 58 by `tax_year`) so the 1961/2025 dual-Act scope (ADR-015/016) isn't duplicated logic
- [x] DTAA Article 15 (90-day test) logic -- `backend/app/tax_engine/dtaa.py`, `compute_article_15_exposure()`; covers both the 90-day (all-or-nothing) and fixed-base (apportioned) branches, plus their precedence when both are met
- [~] DTAA Article 25 (foreign tax credit) logic -- `compute_article_25_relief()` takes `us_tax_paid`/`india_tax_attributable` as OPTIONAL arguments and computes `min(...)` when both are supplied; at every call site today both are omitted, since neither has a verified source yet (US tax paid needs 26 U.S.C. Section 871(b)/872 + Form 1040-NR research not yet done, ADR-012; India tax attributable needs a progressive slab-rate calculator not yet built). The optional-argument design means neither this function nor its result model will need to change once those two calculators exist -- they just become new callers. Genuinely blocked on the underlying research, not on this code -- see `docs/personas.md` Persona C.
- [x] Hand-verified persona scenarios defined (ground truth, checked against primary sources per `docs/WORKING_PRINCIPLES.md` rule 3) -- seven personas (A-G), see `docs/personas.md`
- [x] Unit test suite passing against all seven defined personas (A-G), including boundary cases -- 38/38 passing. Covers: the specified-profession scheme (A, B1, B2, G) with its threshold/proviso boundaries and eligibility gates; DTAA Article 15/25 (C, D) with the 90-day/fixed-base boundary and precedence cases; firm remuneration (E); and now Persona F -- the general-business routing scheme, its blended-rate and threshold boundaries, and the genuine-ineligibility cases (commission/brokerage, agency business) that a flat rejection still correctly applies to.

## Phase 2 — RAG pipeline (target: weeks 5-8, overlaps Phase 1)

- [ ] Ingestion + hierarchy-aware chunking
- [ ] pgvector storage wired up
- [ ] Hybrid BM25 + vector retrieval
- [ ] Citation-required prompting
- [ ] Citation verification check
- [ ] First pass of RAGAS-style eval harness running

## Phase 3 — Expense classifier + audit risk meter (target: weeks 8-10)

- [ ] Few-shot classification against fixed taxonomy
- [ ] Confidence scoring
- [ ] Rule-based audit-flag logic

## Phase 4 — Integration (target: weeks 10-12)

- [ ] FastAPI endpoints wired to all modules
- [ ] Next.js dashboard: upload, classification review, tax & DTAA summary, audit report
- [ ] End-to-end flow working on all personas

## Phase 5 — Evaluation & hardening (target: weeks 12-14)

- [ ] Full eval suite run (tax engine, RAG, adversarial false-premise set, classifier)
- [ ] Technical report written
- [ ] Demo prep, deployment polish

---

## Session log

Add a dated entry each time work happens — a few lines is enough.

### 2026-09-10 — Phase 0 scaffold
- Created repo structure, docs mirror, decision log, progress tracker, Docker Compose skeleton with hello-world FastAPI backend and minimal Next.js frontend.
- **Next:** deploy the hello-world skeleton to the real cloud target (§9.5), then start curating the source document corpus.
- **Blocked on:** nothing yet — cloud target (PaaS vs VM) still needs to be picked before the deploy step.

### 2026-09-17 — Docker-only dev workflow
- Switched `docker-compose.yml` to volume-mounted hot reload for both services (ADR-011) so day-to-day edits don't need a rebuild; updated README's "Running locally" section to match.
- **Next:** deploy hello-world to the real cloud target (still the top open item — see above), and before that, write the production-style build config this dev setup doesn't cover.
- **Blocked on:** nothing — cloud target still needs picking.

### 2026-09-17 — Corpus curation: Section 44ADA, DTAA Articles 15 & 25, 26 U.S.C. §861(a)(3)
- Curated and wrote the first three tagged primary-source documents into `corpus/`, per `docs/WORKING_PRINCIPLES.md` rule 3 (verify against primary sources, surface discrepancies rather than resolving them silently).
- Section 44ADA confirmed to statute level: base text (Indian Kanoon) + the Finance Act 2023 Clause 17 amendment (₹50L base / ₹75L threshold when cash receipts ≤5%). Note: the amendment came from a WebFetch extraction, not a byte-verified source — flagged in the file's own metadata header.
- DTAA Articles 15 & 25 confirmed against the actual scanned treaty PDF (user-supplied `irs.gov/pub/irs-trty/india.pdf`), read directly page-by-page rather than through WebFetch — this was necessary because two separate WebFetch calls to the same PDF returned non-identical "verbatim" text for Article 15 (WebFetch runs fetched content through an intermediate summarizing model, so it isn't reliably byte-exact). Direct visual transcription resolved the discrepancy.
- Found and recorded: the same-day Protocol clarifies Article 15's PE/fixed-base attribution timing (deferred payment still taxable); the same-day Exchange of Notes says no tax-sparing credit is currently provided under Article 25, contingent on future US law changes — no evidence found that this has since triggered. No later amending protocol to the treaty was located.
- 26 U.S.C. §861(a)(3) confirmed (Cornell LII) and explicitly flagged as a *distinct* rule from DTAA Article 15 (different conditions: 90 days AND $3,000 cap AND specific employer relationship, vs. Article 15's 90 days OR fixed base, no cap). Whether §861(a)(3) is in scope for the v1 tax engine is still an open call — not yet decided.
- **Next:** define 2-3 hand-verified persona scenarios grounded in this confirmed text; finalize the `jurisdiction`/`effective_date`/`tax_year` metadata schema formally (informal version already used in the corpus file headers).
- **Blocked on:** nothing.

### 2026-09-17 — All corpus documents re-verified against official primary-source PDFs
- User supplied three more official PDFs to close the reliability gap flagged earlier that day: the Income Tax Department's own official per-section export of 44ADA, GovInfo's official compiled U.S. Code text of 26 U.S.C. 861, and a copy of "Finance Act, 2023" (gstcouncil.gov.in mirror).
- 44ADA: the Income Tax Department's own official section export (already reflecting the 2023 amendment) was read directly and used to replace the corpus file. Minor wording fix from the earlier WebFetch-derived version: "Provided that in case of an assessee where the amount..." (official) vs. "Provided that where the amount..." (previous) -- substance unchanged, phrasing corrected. Every corpus document now carries either a direct-PDF-transcription source or is confirmed word-for-word against one; no open WebFetch-reliability caveats remain in `corpus/`.
- 26 U.S.C. 861(a)(3): confirmed word-for-word against the official GovInfo PDF -- zero discrepancy from the earlier Cornell LII/WebFetch version. Reliability caveat removed from that file.
- Finance Act, 2023 PDF the user supplied turned out to be a partial 10-page extract (gstcouncil.gov.in mirror) that omits the entire Income-tax Act chapter (jumps from gazette page 1 straight to page 56, Customs Act) -- it does not contain Clause 17 and could not be used. Not a blocker: the Income Tax Department's own current section text (above) is a stronger source for the *current* law than the amending clause in isolation, but if the standalone Clause 17 text is ever needed, a complete Gazette copy of Finance Act No. 8 of 2023 would need to be sourced separately (see PROGRESS.md this entry for context if revisited).
- **Next:** define 2-3 hand-verified persona scenarios grounded in this confirmed text.
- **Blocked on:** nothing.

### 2026-09-17 — Hand-verified persona scenarios defined (docs/personas.md)
- Defined four personas (Anika, Rohan x2 variants, Meera, Devika), each isolating one specific rule boundary rather than being a realistic composite: 44ADA baseline, the 44ADA cash-threshold proviso (qualifying and disqualifying sides), DTAA Article 15's 90-day all-or-nothing branch, and Article 15's fixed-base apportioned branch.
- Two genuine gaps surfaced and were documented rather than papered over, each now its own ADR: Persona C's US-side tax figure is an explicitly-labeled flat-rate placeholder (ADR-012) since NRA US taxation under 26 U.S.C. 871(b)/872 hasn't been researched; Persona D's apportionment of lump-sum 44ADA income to a fixed-base share is a documented modeling choice (ADR-013), not a rule either the statute or the treaty actually specifies.
- Still open, not blocking: Section 44AA(1)'s notified-professions list hasn't itself been verified to primary-source rigor; partnership-firm eligibility under 44ADA is untested (all four personas are individuals); a false-premise / ineligible-profession persona (for the Phase 5 adversarial eval set) isn't built yet.
- **Next:** Phase 1 proper -- Pydantic models for persona/transaction/computation, then the 44ADA calculation logic tested against these personas.
- **Blocked on:** nothing.

### 2026-09-17 -- Section 44AA/40(b) verified; Income-tax Act 2025 dual-scope expansion; Personas E & F added
- Verified Section 44AA(1)-(2) and Section 40(b) (1961 Act) against two independent sources -- user-pasted bare-act text and a comprehensive official consolidated Act PDF -- catching one real discrepancy: the pasted text's partner-remuneration caps (Rs. 3,00,000/Rs. 1,50,000) were stale by one amendment; the current figures (per Act No. 15 of 2024, w.e.f. 1-4-2025) are Rs. 6,00,000/Rs. 3,00,000. Written to `corpus/india/it-act-section-44aa/2025-26.txt` and `corpus/india/it-act-section-40b/2025-26.txt`.
- Discovered and confirmed: India's new **Income-tax Act, 2025** [No. 30 of 2025] is in force from 1 April 2026, repealing the 1961 Act; FY2025-26 remains under the 1961 Act, FY2026-27 onward (the current year) is under the new Act. Per explicit direction, the project's scope now spans both Acts in parallel (ADR-015) rather than treating the new Act as future work. Section 58 (consolidates 44AD/44AE/44ADA), Section 35(e) (successor to 40(b)), and Section 62(4) (successor to 44AA(1)) verified by direct page-read of the user-uploaded 686-page Act PDF and written to `corpus/india/it-act-2025-section-58/2026-27.txt`, `-35e/`, `-62/`.
- Resolved Persona E's open question with cross-Act, cross-section evidence (ADR-014): a firm on 44ADA cannot additionally deduct partner remuneration under Section 40(b) on top of the presumptive income -- confirmed by comparing 44AD(2) (no carve-out), 44AE(3) (explicit carve-out), and 44ADA(2) (no carve-out), a pattern the 2025 Act's Section 58(5) carries forward unchanged.
- Added Persona E (Sharma & Associates, partnership firm) and Persona F (Karan, profession not on the 44AA(1)/62(4) list -- likely misrouted to Section 44AD's general-business scheme instead of a flat rejection) to `docs/personas.md`. Six personas total now.
- An earlier same-session flag calling the 2025 Act's Sl.-No.-2-only remuneration carve-out a possible drafting anomaly was retracted once the 1961 Act comparison showed it's a faithful continuation, not a new oddity -- documented in `docs/personas.md`'s "Resolved since the previous version" note rather than silently corrected.
- **Next:** a Section-58/FY2026-27 persona (the corpus now supports one but none exists yet); Phase 1 proper (Pydantic models, 44ADA/Section 58 calculation logic against all six personas); `Implementation_Plan.md`/`System_Design_and_Requirements.md` still need updating to reflect the dual-Act scope (Claude Project docs, not yet touched).
- **Blocked on:** nothing.

### 2026-09-20 -- ITA-2025 adopted as default legal base; Section 90/159 (DTAA enabling provision) curated
- Resolved the "which Act is our real base" question raised by the user: adopted the Income-tax Act, 2025 as the project's default going forward (new personas, demo queries, unspecified-year assumptions), while explicitly keeping the 1961 Act as prior-year support rather than deprecating it -- ADR-016. The "amended annually" concern that prompted the question turned out to already be handled by ADR-009's effective_date-level tagging, which the 1961 Act had already been exercising (Section 40(b)'s 2009 and 2024 amendments, 44ADA's 2023 amendment).
- Curated Section 90 (1961 Act) and its 2025-Act successor Section 159 -- the actual domestic-law provisions that give the India-US DTAA legal force in India, which nothing in the corpus covered before (only the treaty text itself was curated). Section 90/159 written to `corpus/india/it-act-section-90/2025-26.txt` and `corpus/india/it-act-2025-section-159/2026-27.txt`; both visually confirmed against their source PDFs. Flagged a directionality nuance in both: the TRC (tax residency certificate) sub-section is worded for non-residents claiming relief in India, not directly the resident-claiming-FTC-for-tax-paid-abroad direction this project's personas use.
- Reviewed corpus/treaty sufficiency against the project's own FR list (`System_Design_and_Requirements.md` §2.1) rather than open-ended brainstorming. Confirmed GST, FEMA/remittance rules, and non-US treaties are correctly out of scope (FR-14). Surfaced two real gaps instead: Form 67/Rule 128 (foreign-tax-credit procedural requirement -- referenced by the data model's `form67_required` column but no primary source sourced yet; blocked, not decided against) and Section 6 residential-status determination (silently assumed "resident in India" in every persona; Persona C's 110 US days is the fact pattern where that assumption is least safe). Both added to `docs/personas.md`'s "Still open" section rather than resolved by guesswork.
- **Next:** source an official copy of the Income-tax Rules, 1962 (or specifically Rule 128 / Form 67) to unblock that corpus gap; otherwise the standing next items are unchanged (Section 58/FY2026-27 persona, Phase 1 proper, Implementation Plan/System Design doc updates for the dual-Act scope).
- **Blocked on:** a primary source for Rule 128 / Form 67.

### 2026-09-20 (cont.) -- Form 67/Rule 128 gap closed
- User supplied official Income-tax Rules PDFs (1962 and 2026). Curated Rule 128 (1961 Rules, Form No. 67) and its successor Rule 76 (2026 Rules, Form No. 44) -- both visually confirmed against source pages. This closes the blocker from earlier today and fully grounds Persona C's Article 25 credit claim (treaty -> Section 90/159 -> Rule 128/76 -> Form 67/44 is now a complete, citable chain).
- Caught a second renumbering trap while curating, same category as the Section 58 collision: it's not just the rule number that changes (128 -> 76), the **form number itself changes (Form 67 -> Form 44)** under the new Act's Rules. Documented in `corpus/README.md` alongside the existing Section 58 trap note. Also flagged, not assumed: the filing-deadline wording changed between the two rules ("end of assessment year" vs. "twelve months from end of tax year") -- not confirmed equivalent.
- `docs/personas.md`'s "Still open" list updated: Form 67/Rule 128 item moved to "Resolved."
- **Next:** unchanged from earlier today -- Section 58/FY2026-27 persona, Phase 1 proper, Implementation Plan/System Design doc updates for the dual-Act scope. Residential-status (Section 6) gap still open and still not built out.
- **Blocked on:** nothing.

### 2026-09-20 (cont.) -- Section 6 closed out as explicit out-of-scope; a verification process gap caught and fixed
- Residential status decision made (per user direction): Section 6 residency determination is a formal out-of-scope input for v1 (FR-15, ADR-017), not a silently assumed fact. Curated Section 6 once (`corpus/india/it-act-section-6/2025-26.txt`) for a single purpose -- hand-checking that Persona C's 110-US-days premise isn't self-contradictory with her being an Indian resident. It isn't: ~255 days in India clears the 182-day threshold on its own. That file is explicitly marked as not wired into any computation.
- **Process gap caught and fixed:** while sourcing Section 6, discovered the comprehensive 1961 Act PDF (179MB) exceeds the page-image tool's 100MB limit -- meaning the "direct visual page-read" claimed in three earlier corpus files (`it-act-section-44aa`, `it-act-section-40b`, `it-act-section-90`, all 2025-26.txt) had actually only ever been pdftotext text-extraction, never true page-image confirmation, contrary to what those files' own metadata said. Fixed same-day: found a workaround (qpdf splits the relevant page range into a small standalone PDF, small enough to read directly) and retroactively performed genuine visual confirmation on all three -- no discrepancies found, but the earlier metadata was overstating what had actually been verified, and has been corrected in place (`verification_correction` notes added) rather than silently left as-is. Noting this qpdf-split technique for future large-PDF sourcing.
- **Next:** unchanged from earlier today.
- **Blocked on:** nothing.

### 2026-09-20 (cont.) -- Pre-commit review: two verification gaps closed
- Before committing the 09-17/09-20 batch, a review surfaced two gaps: Rule 128's "direct visual page-read" claim was ambiguous (104MB source PDF, over the page-image tool's 100MB limit, no confirmation the qpdf-split workaround used for other affected files had actually been applied here); and Persona F's central conclusion depended on Section 44AD(6), which had never been curated into `corpus/` -- only recalled from memory.
- Both closed same-day: Rule 128 re-confirmed via genuine qpdf-split page-image read (no discrepancy). Section 44AD (sub-sections 1-6 + Explanation) added as a new corpus file, visually confirmed against the 1961 Act PDF; sub-section (6)'s exclusion list matches Persona F's assumption verbatim. `docs/personas.md`, `corpus/README.md`, `DECISIONS.md` (ADR-018) updated accordingly.
- Fifteen corpus documents now (was fourteen).
- Deleted a stale `.git/index.lock` (dated 2026-09-17, left over from an earlier session) that would have blocked `git add`/`git commit`.
- **Closed same day:** user re-supplied the 2025 Act PDF (~3.1MB, well under the 100MB limit that caused the problem elsewhere -- the risk never actually applied to these four). All four re-checked via genuine visual page-image read; no discrepancy found. Surfaced one new, non-blocking observation: Section 58(5)/(7) reference "sub-section (1)" where computation actually happens in sub-section (2) -- a genuine Act drafting artifact, confirmed on the page image, documented in ADR-019 and the section-58 corpus file, not a bug in our transcription.
- **Note on process going forward:** at the user's explicit instruction, `git add`/`commit`/`push` are no longer run automatically as part of this kind of review/fix pass -- content and doc changes are made and left uncommitted for the user to review and commit themselves.
- **Next:** user to review and commit this batch (2026-09-17 through 2026-09-20's corpus/persona/decision work, plus this same-day fix pass); then a Section-58/FY2026-27 persona; then Phase 1 proper (Pydantic models, 44ADA/Section 58 calculation logic against all six personas).
- **Blocked on:** nothing -- ready for commit.

### 2026-09-20 (cont.) -- Persona G (first FY2026-27 persona) and formal metadata schema
- Added Persona G (Nikhil): deliberately the same facts as Persona A, dated FY2026-27 under the Income-tax Act, 2025 (Section 58 Table Sl. No. 3), as a regression check across the Act boundary -- same Rs. 16,00,000 result, as expected. Exercises Section 58(11)(b)'s "specified assessee" definition and Section 62(4)'s expanded profession list ("information technology", "company secretary"), neither reached by any other persona. Seven personas total (A-G).
- Defined and adopted the formal corpus metadata schema (`corpus/METADATA_SCHEMA.md`, ADR-020) -- the last unchecked Phase 0 item. Retrofitted an 11-field `schema_v1_*` structured block onto all 15 existing corpus documents (namespaced to avoid colliding with the existing free-text `jurisdiction:`/`retrieval_method:` keys), computed from what each file's own header already stated -- a normalization pass, not new legal research. Flagged three files' genuine unknowns explicitly (`schema_v1_ambiguous_fields`) rather than guessing: Section 6's Finance-Act-2020 sub-provision dates, and both DTAA articles' effective-date/tax-year applicability.
- Left one open design question for Phase 2 rather than deciding it now: the DB schema's single `effective_date`/`tax_year` columns don't support a start/end range, which the superseded 1961-Act documents will need once retrieval has to answer a query about a past tax year. Documented in `corpus/METADATA_SCHEMA.md`.
- **Next:** Phase 0 is now fully checked except the two infra items (production-style compose config, cloud deploy) that have been open since 2026-09-17. Phase 1 proper is otherwise unblocked: Pydantic models, then 44ADA/Section 58 calculation logic, tested against all seven personas.
- **Blocked on:** nothing.

### 2026-09-20 (cont.) -- Phase 1 tax engine, first increment: presumptive income, non-treaty personas
- Built the first slice of the deterministic tax engine, scoped deliberately narrow: Section 44ADA/Section 58 presumptive-income calculation only, tested against the four personas that don't involve DTAA relief, firm remuneration, or misrouting (A, B1, B2, G). DTAA (Article 15/25), Persona E's firm-remuneration interaction, and Persona F's 44AD misrouting are explicitly out of scope for this increment, flagged as such in code docstrings/ineligibility messages, and left as open Phase 1 items below.
- `backend/app/tax_engine/models.py`: `PresumptiveIncomeInput`/`PresumptiveIncomeResult` Pydantic models, plus `LegalInstrument`/`EntityType` enums. `backend/app/tax_engine/presumptive.py`: `select_legal_instrument()` picks the 1961 Act (Section 44ADA) vs. the 2025 Act (Section 58, Table Sl. No. 3) by `tax_year`, and `compute_presumptive_income()` shares one computation path across both Acts so the near-identical provisions can't drift apart -- verified by Persona A (1961 Act) and Persona G (2025 Act, identical facts) producing the identical Rs. 16,00,000 figure.
- `backend/tests/test_presumptive.py`: 20 tests, all passing -- the four personas, the Act-selection boundary (FY2025-26 vs. FY2026-27), six threshold/cash-proviso boundary cases (exact Rs. 50L/75L, one rupee over each, exact 5% cash split both sides), and four eligibility-gate cases (LLP excluded, non-resident excluded, non-specified profession excluded here -- Persona F's territory, partnership firm correctly still eligible).
- Per `docs/WORKING_PRINCIPLES.md` rule 4, ran the suite before calling this done: `pytest tests/test_presumptive.py -v` -- 20/20 passed on first run. Also ran `ruff check` on the new files to match the CI lint step; fixed the real findings (an `Optional[X]` -> `X | None` style pass, unsorted imports, a `dict()` call rewritten as a literal) via `ruff check --fix` plus one manual fix. The remaining `EXE002` ("file executable, no shebang") flags on these files are a mount-environment artifact, not a real issue -- `git config core.fileMode` is `false` in this repo and existing tracked files (`main.py`, `test_health.py`) are stored as `100644` despite showing as executable on this filesystem too, confirmed via `git ls-files -s`.
- **Next:** DTAA Article 15/25 logic (Personas C/D), firm-remuneration interaction (Persona E), 44AD-misrouting logic (Persona F) -- each its own follow-up increment per the same test-first discipline. Phase 0's two infra items (production-style compose config, cloud deploy) remain open and deprioritized.
- **Blocked on:** nothing -- ready for the user to review and commit.

### 2026-09-20 (cont.) -- Phase 1 tax engine, second increment: DTAA Article 15/25, Personas C & D
- Before writing any code, walked through the two Article 15 branches and Article 25's relief mechanism with the user against the actual treaty text and Personas C/D, and separately checked whether new corpus documents were needed. Conclusion: no new sourcing needed for this increment; India's progressive slab rates (for Article 25's India-tax-attributable cap input) and US nonresident-alien taxation under 26 U.S.C. Section 871(b)/872 (for the US-tax-paid cap input) are both genuinely missing from the corpus, but deliberately deferred to future increments per the user's decision, not needed to compute Article 15 or represent Article 25's mechanism.
- `backend/app/tax_engine/dtaa.py`: `compute_article_15_exposure()` -- the 90-day test (branch (b), all-or-nothing, no attribution limitation) and the fixed-base test (branch (a), apportioned by the same gross-receipts ratio as the underlying presumptive income, per ADR-013). Where both conditions are met, the 90-day branch governs (not exercised by any persona, but the only reading consistent with the treaty text -- documented as such in the module docstring). `compute_article_25_relief()` models the `min(US tax paid, India tax attributable)` cap but leaves both inputs `None`/pending, matching Persona C's own file rather than inventing a number.
- `backend/tests/test_dtaa.py`: 11 new tests -- Personas C and D directly, the 90-day boundary (89 vs. exactly 90), a fixed-base-present-but-zero-attribution edge case, the both-conditions-met precedence case, Article 25's not-applicable vs. pending-inputs states, and an input-validation case (attributable receipts can't exceed gross receipts).
- Verified per `docs/WORKING_PRINCIPLES.md` rule 4 before calling this done: full suite (`test_dtaa.py` + `test_presumptive.py`) -- 31/31 passing, no regressions in the first increment. `ruff check` on the new file caught one unsorted-import issue, fixed via `--fix`; re-ran the suite after the fix to confirm nothing broke.
- **Next:** Persona E (firm remuneration) and Persona F (44AD misrouting) are the remaining personas without engine coverage. India progressive slab-rate calculator and US NRA taxation research are open, explicitly deferred sub-tasks needed before Article 25 can produce an actual credit figure -- not blocking, but worth picking up before this increment is considered "finished" rather than "as far as we can go right now."
- **Blocked on:** nothing -- ready for the user to review and commit.

### 2026-09-20 (cont.) -- Phase 1 tax engine, third increment: partner remuneration, Persona E
- Extended (rather than duplicated) the existing presumptive-income engine: `PresumptiveIncomeInput` gained `partner_remuneration_authorized` (citation-only, for a PARTNERSHIP_FIRM), and `PresumptiveIncomeResult` gained `final_taxable_business_income` (explicitly the final figure, not a floor) and `partner_remuneration_note` (populated only for a firm with a remuneration figure on record, citing ADR-014). `compute_presumptive_income()` in `presumptive.py` sets both.
- This is Persona E's whole point: prove the engine doesn't treat 44ADA's presumptive figure as something ordinary Chapter IV-D deductions -- including partner remuneration -- can still chip away at, using a remuneration figure (Rs. 20,00,000) that would itself pass Section 40(b)'s cap under normal computation, so a wrong implementation applying 40(b) after 44ADA would produce a wrong-but-plausible-looking lower figure.
- `backend/tests/test_presumptive.py`: 2 new tests -- Persona E directly (`final_taxable_business_income == presumptive_income`, not `presumptive_income - remuneration`), and a check that the note stays absent for a non-firm.
- Verified per rule 4: `test_presumptive.py` + `test_dtaa.py` -- 33/33 passing, no regressions. `ruff check` clean on the first pass this time.
- **Next:** Persona F (misrouting to Section 44AD/Section 58 Sl. No. 1 for a non-specified profession) is the last persona without engine coverage. India slab-rate calculator and US NRA taxation research (for Article 25's actual credit figure) remain open, deliberately deferred.
- **Blocked on:** nothing -- ready for the user to review and commit.

### 2026-09-20 (cont.) -- Phase 1 tax engine, fourth increment: general-business routing, Persona F (all seven personas now covered)
- Grounded first (Section 44AD's corpus file, Section 58 Table Sl. No. 1, ADR-014's comparison text) before writing any code: an unspecified profession is NOT automatic ineligibility. Section 44AD(6) / Section 58(11)(a) only exclude commission/brokerage income and agency business from the general-business scheme -- Karan's digital-marketing consultancy is neither, so it routes to that scheme (8%/6% blended rate by banking vs. cash receipts, Rs. 2/3 crore threshold) instead of a flat rejection.
- Extended `presumptive.py` rather than adding a new module, since `compute_presumptive_income()` is the single entry point callers use regardless of profession: the `if not data.is_specified_profession` branch now calls a new `_compute_general_business_presumptive()` instead of returning a stub rejection. Two new `LegalInstrument` values (Section 44AD / Section 58 Sl. No. 1) and two new input fields (`earns_commission_or_brokerage`, `carries_on_agency_business`) added to `models.py`, plus `routed_to_general_business`/`routing_note` on the result so a caller can always tell which scheme actually ran. Factored the partner-remuneration note (Persona E) into a small shared helper used by both paths, since neither scheme carves it out.
- Replaced the old placeholder test (which asserted the Persona F fact pattern was "not yet implemented") with the real test, plus 4 more: the blended-rate calculation with mixed cash/banking receipts, both genuine-ineligibility cases (commission/brokerage, agency business -- confirming a flat rejection still correctly applies there, just for a different reason than "wrong profession"), and the Rs. 2 crore threshold boundary.
- Verified per rule 4: `test_presumptive.py` + `test_dtaa.py` -- 38/38 passing (5 new), no regressions in any prior increment. `ruff check` clean on the first pass.
- **All seven personas (A-G) from docs/personas.md now have engine coverage.** Remaining open Phase 1 work is not persona-specific: India's progressive slab-rate calculator and US NRA taxation research, both needed before Article 25 (Personas C/D) can produce an actual credit figure instead of the current pending-inputs state.
- **Next:** decide whether to pick up the slab-rate calculator or the US NRA research next (or move to Phase 2 RAG work and return to these later); Phase 0's two infra items (production-style compose config, cloud deploy) remain open and deprioritized.
- **Blocked on:** nothing -- ready for the user to review and commit.

### 2026-09-20 (cont.) -- Article 25 refactor: optional credit-cap inputs
- Small design refactor, prompted by comparing notes with an external suggestion (NotebookLM) the user brought: `compute_article_25_relief()` now takes `us_tax_paid` and `india_tax_attributable` as optional keyword arguments rather than only ever returning `None` fields with no way to supply real values. Supply both and it computes the actual `min(...)` credit; supply one, or neither, and `pending_reason` names exactly which is still missing (the supplied one is carried through on the result, not dropped).
- Deliberately did NOT adopt the external suggestion's own code as-is: its sketch collapsed Article 15 to a single `is_article_15_exempt` boolean, which would have thrown away the 90-day/fixed-base branch distinction and the apportionment logic Persona D depends on. Also declined to cite its "Section 202" claim for the India-side default-regime provision -- unverified against primary source, not written into DECISIONS.md or any corpus file.
- `backend/tests/test_dtaa.py`: 3 new tests -- credit computed when both inputs supplied, the credit correctly capped at the lower of the two (India's figure governing, not just US's), and a partial-supply case confirming the still-missing input is named correctly and the supplied one isn't silently dropped.
- Verified per rule 4: `test_presumptive.py` + `test_dtaa.py` -- 41/41 passing after fixing one over-strict test assertion of my own (a substring check that incorrectly flagged "US tax paid" appearing in the fixed formula-explanation sentence, not the missing-inputs list). `ruff check` clean.
- **Next:** unchanged -- India slab-rate calculator and US NRA taxation research remain the two open threads, now with a slightly cleaner integration point waiting for them.
- **Blocked on:** nothing -- ready for the user to review and commit.

### 2026-09-20 (cont.) -- Phase 0: production-style Docker Compose config (base + override split)
- Discussed the design choice before implementing, per the user's request: base+override (Compose's own recommended pattern for a dev/prod split) vs. a fully separate `docker-compose.prod.yml`. Went with base+override.
- `docker-compose.yml` is now the production-shaped default: frontend builds to the `runner` stage (the actual compiled Next.js standalone output -- previously it built to `deps`, which has no built app at all), neither service mounts source or overrides its command, `restart: unless-stopped` added to all three services. `docker-compose.override.yml` holds everything dev-specific from ADR-011 (source mounts, `--reload`/`npm run dev`, the frontend `deps` target) -- Compose merges it automatically on `docker compose up` with no flags, so local dev is unaffected.
- **Confirmed no rebuild was needed for this session's tax-engine work**, separately from the compose split itself: the backend service already bind-mounts `./backend:/app` and runs with `--reload`, and none of today's changes touched `requirements.txt` or the Dockerfile (pydantic/pytest were already pinned there) -- ADR-011's own rule ("only `--build` when requirements/Dockerfile change") already covered this.
- **Caveat, documented in ADR-021 and worth repeating here:** Docker isn't available in this environment, so `docker compose config` (the authoritative merge-resolution check) has not been run. Both files pass YAML syntax validation; the merge semantics (build.target merging into the base's build mapping, command/volumes being additions not conflicts) were reasoned through manually against Compose's documented merge rules but not executed.
- **Next:** run `docker compose config` (needs Docker, so from the user's own machine or wherever Docker is available) to confirm the merge resolves as described, then a normal `docker compose up` to confirm dev workflow still works unchanged, and `docker compose -f docker-compose.yml up -d --build` to confirm the production shape actually builds and serves. Only after that should the actual cloud deploy step (§9.5) be attempted. Separately: `docs/Implementation_Plan.md` and `docs/System_Design_and_Requirements.md` (and their Claude Project copies) still need the dual-Act-scope update flagged back in ADR-015 -- agreed as a next task, not yet done.
- **Blocked on:** nothing for the compose split itself; the "confirmed working" claim is blocked on the user running the commands above somewhere Docker exists.

### 2026-09-20 (cont.) -- Docker Compose base+override split confirmed working against real Docker
- User ran `docker compose config` on their own machine; the resolved merge matched ADR-021's description exactly (`backend`'s `--reload` command and bind mount, `frontend`'s `target: deps`/`npm run dev`/bind mounts, `db` untouched by the override). This closes the "validated YAML syntax only, never run" caveat from the previous entry.
- User then stopped the previously-running dev containers (`docker compose down`) and brought them back up with `docker compose up --build`; confirmed hot reload on both backend and frontend still works exactly as before the split. ADR-021 updated in place to record this rather than left as an open caveat.
- Also ran the production-only path the same day: `docker compose -f docker-compose.yml up -d --build`, explicitly excluding the override. All three containers built and started cleanly; confirmed both `localhost:3000` (frontend, built `runner` stage, no dev-mode indicators) and `localhost:8000` (backend) responded correctly -- the last unexercised piece from ADR-021 is now closed too.
- **Both paths this ADR describes (dev via plain `docker compose up`, production via the explicit `-f` exclusion) are now confirmed working locally.** What's left before this is genuinely deploy-ready is doing the same on the real cloud target (§9.5), not just on the user's own machine.
- **Blocked on:** nothing.

### 2026-09-20 (cont.) -- Docs sync: Implementation_Plan.md and System_Design_and_Requirements.md updated for dual-Act scope
- Closed the flag from ADR-015 (these two docs hadn't been updated since the 2025 Act was discovered). Added a dated scope note to the top of each; fixed the specific claims that assumed a single Act (Implementation_Plan §1/§4/§8; System_Design's FR-3, architecture diagram box -- padding recomputed programmatically so the box-drawing alignment wasn't broken -- and the request-flow walkthrough).
- Found and fixed a real, unrelated inaccuracy while doing this: System_Design §9.1 claimed the Docker Compose setup was "used identically in dev and in production... no separate 'prod config' to maintain" -- false since ADR-011, and directly contradicted by today's ADR-021 work. Rewrote with an explicit dated correction note rather than silently editing over it.
- Added FR-16 (Persona E's partner-remuneration finding) -- real, tested behavior that had no corresponding functional requirement. Folded Persona F's general-business routing into FR-3 rather than a new FR, since it's the same capability, not a separate one.
- ADR-022 records this. Both docs' "Compiled September 10, 2026" footers were left as-is (historical compile date), with the new scope notes explaining what changed since.
- **Next:** these two docs are now believed current against everything built so far; worth a re-check whenever the next major scope decision lands (e.g. once Article 25's credit is actually computable, or RAG work starts). `docs/SRS_SDS_Report_CrossBorderTax.docx` (the formal submission doc) was NOT touched -- not checked for the same drift, flagging that as open.
- **Blocked on:** nothing.
