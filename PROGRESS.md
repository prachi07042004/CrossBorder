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
- [ ] Production-style compose/deploy config (full multi-stage frontend build, no source mounts) — needed before the cloud deploy step below, not yet written
- [ ] Skeleton deployed to the real cloud target (see `System_Design_and_Requirements.md` §9.5) — **next concrete step**
- [x] CI workflow running lint + tests on push — confirmed green on GitHub Actions after the initial push (2026-09-17)
- [x] Source documents curated and version-tagged: Section 44ADA text, DTAA Articles 15 & 25, relevant IRS guidance (§861(a)(3)) — see `corpus/`
- [x] `jurisdiction` / `effective_date` / `tax_year` metadata schema finalized against the curated corpus -- see `corpus/METADATA_SCHEMA.md` and ADR-020

## Phase 1 — Deterministic tax engine (target: weeks 3-5)

- [ ] Pydantic models for persona, transaction, tax computation
- [ ] Section 44ADA presumptive income calculation
- [ ] DTAA Article 15 (90-day test) logic
- [ ] DTAA Article 25 (foreign tax credit) logic
- [x] Hand-verified persona scenarios defined (ground truth, checked against primary sources per `docs/WORKING_PRINCIPLES.md` rule 3) -- seven personas (A-G), see `docs/personas.md`
- [ ] Unit test suite passing against all defined scenarios, including boundary cases

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
