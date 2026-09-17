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
- [ ] CI workflow running lint + tests on push
- [ ] Source documents curated and version-tagged: Section 44ADA text, DTAA Articles 15 & 25, relevant IRS guidance
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
