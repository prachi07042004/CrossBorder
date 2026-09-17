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
- [ ] `jurisdiction` / `effective_date` / `tax_year` metadata schema finalized against the curated corpus

## Phase 1 — Deterministic tax engine (target: weeks 3-5)

- [ ] Pydantic models for persona, transaction, tax computation
- [ ] Section 44ADA presumptive income calculation
- [ ] DTAA Article 15 (90-day test) logic
- [ ] DTAA Article 25 (foreign tax credit) logic
- [ ] Hand-verified persona scenarios defined (ground truth, checked against primary sources per `docs/WORKING_PRINCIPLES.md` rule 3)
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
