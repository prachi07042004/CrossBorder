# System Design & Requirements Specification

*Companion to `Implementation_Plan.md`. That document answered "what order do we build things in." This one answers "have we actually thought this through" — it traces every major design choice back to a specific resource, then locks down requirements, architecture, data model, API surface, and tech stack in enough detail to start coding without re-litigating decisions later.*

**Scope note (2026-09-20):** India enacted the Income-tax Act, 2025 [No. 30 of 2025], in force from FY2026-27, after this document was first compiled. The requirements and architecture below reflect the resulting dual-Act scope (both the 1961 Act and the 2025 Act, selected by tax year) rather than the single-Act assumption this doc originally shipped with -- see ADR-015/016 in `DECISIONS.md` for the full reasoning, and §9.1 below for a related correction to the dev/production deployment model.

---

## 1. Resource → Decision traceability

This is the "did we actually analyze this" check. Every resource should earn its place by changing a concrete decision — if it doesn't, it's decoration, not research.

| Resource | Decision it drives | Where it shows up below |
|---|---|---|
| Temporal Misgrounding (arXiv, 2026) | Every document chunk carries `jurisdiction`, `effective_date`, `tax_year`; retrieval always filters on tax year before ranking | §5.3 data model, FR-6 |
| LLMs for Austrian VAT (arXiv, 2025) | RAG over fine-tuning, confirmed — no model training in scope | Tech stack §6, NFR-3 |
| Towards Reliable Retrieval in Legal RAG (arXiv, 2025) + Legal Chunking (ResearchGate) | Hierarchy-aware chunking (split on Section/Sub-section boundaries, not fixed character windows) | §5.2 ingestion pipeline |
| `bd-legal-rag` (GitHub) | Confirms the chunking pattern above with a working reference implementation | §5.2 |
| `ita-kg` (GitHub) | Knowledge-graph layer considered and explicitly deferred — see §7 | §7 non-goals |
| `Tax-Authority-RAG` (GitHub) | Citation-first, hybrid BM25+vector search pattern adopted directly | §5.2, FR-7 |
| `Form16x` (GitHub) | Reference pattern for parsing uploaded PDFs into structured JSON before they enter the pipeline | §5.1 ingestion |
| `freefile` (GitHub) | Confirms Next.js + FastAPI is a proven pairing for this exact user base (Indian freelancers) | Tech stack §6 |
| PaySim dataset | Used only as a schema reference for transaction fields, not as seed data (fraud patterns ≠ tax-correct scenarios) | §7 non-goals (carried over from Implementation Plan) |
| 44ADA / freelancer tax guides (TaxTap, TaxClue) | Concrete presumptive-tax formula and threshold logic for the deterministic engine | §5.4, FR-3 |
| How Much Do Legal RAG Systems Still Hallucinate? (arXiv, 2026) | Adversarial false-premise test set is a *required* part of the eval suite, not optional polish; "refuse if unsupported" is a functional requirement, not a nice-to-have | FR-9, NFR-2 |
| RAG Is Judgment (SSRN, 2026) | System must expose retrieval confidence to the LLM and let it decline — citations alone are not treated as sufficient | FR-9 |
| Citation Grounding via Legal Citation Graphs (arXiv, 2026) | Citation verification step (does the cited chunk actually contain the claim) added as a v1 requirement, not deferred | FR-8 |
| RAGAS (arXiv, 2023) + RAG Evaluation Survey (arXiv, 2024) | Use RAGAS's faithfulness / context-precision / context-recall metrics directly instead of inventing eval metrics | §8 evaluation |
| OpenFisca | Confirms "separate legislation model from application code, version by effective date" as the right pattern for the tax engine — adopted as a design principle, not as a dependency | §5.4 |
| DTAA India-US guide (dineshaarjav.com) | Article 15 (90-day test) and Article 25 (FTC cap) encoded as the actual DTAA module logic | §5.4, FR-4 |
| ANNA case study (ZenML) | External accuracy/cost reference point for the expense classifier instead of an arbitrary internal target | §8 evaluation |
| Embedding model comparison (premai.io, 2026) | Embedding model choice — see §6 | Tech stack §6 |
| Reranker guidance (folarin.dev, 2026) | Reranker explicitly deferred until retrieval eval shows it's needed | §7, Tech stack §6 |

If any resource from the original 12 doesn't appear in this table, it was context, not a driver of a specific decision — that's fine, but worth knowing which is which when you write the report's related-work section.

---

## 2. Requirements

### 2.1 Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-1 | User can upload transactions (CSV) and invoices (PDF) for a persona | MVP |
| FR-2 | System classifies each transaction into an expense category and deductibility flag (LLM-based, few-shot) | MVP |
| FR-3 | System computes Indian presumptive tax under the applicable Act's presumptive scheme for a given persona/tax year -- Section 44ADA (Income-tax Act, 1961) through FY2025-26, Section 58 (Income-tax Act, 2025) from FY2026-27 onward, selected by tax year (ADR-016) -- including routing to the general-business scheme (Section 44AD / Section 58 Sl. No. 1) instead of outright rejection when a profession isn't on the specified-profession list | MVP |
| FR-4 | System computes DTAA relief: applies Article 15's 90-day test, and Article 25's foreign tax credit calculation when US tax applies | MVP |
| FR-5 | System retrieves relevant source passages (India IT Act, DTAA text, IRS guidance) for any classification or tax decision it makes | MVP |
| FR-6 | Retrieval is constrained to the document versions valid for the persona's tax year (temporal filtering) | MVP |
| FR-7 | Every number and classification shown to the user is accompanied by the specific source section it came from | MVP |
| FR-8 | Citations are verified — the system checks that the cited passage actually supports the claim before displaying it | MVP |
| FR-9 | When retrieval confidence is low or the question contains an unsupported premise, the system says so instead of answering confidently | MVP |
| FR-10 | System produces an audit-risk flag per transaction (missing documentation, threshold proximity, low classification confidence) | MVP |
| FR-11 | User can view a dashboard summarizing tax liability, DTAA relief applied, and audit risk report | MVP |
| FR-12 | System logs which document chunks and rule versions were used for every computation (for later evaluation and for the technical report) | MVP |
| FR-13 | Knowledge-graph-based statutory relationship modeling (à la `ita-kg`) | Stretch / future work |
| FR-14 | Support for jurisdictions/treaties beyond India-US | Out of scope |
| FR-15 | Determination of residential status under Section 6 -- v1 takes "resident in India" as a given input per persona, not a computed fact (see ADR-017) | Out of scope |
| FR-16 | A partnership firm's presumptive income (FR-3) is never further reduced by partner remuneration or any other Chapter IV-D deduction, regardless of what the partnership deed authorises -- neither Section 44ADA/58 Sl. No. 3 nor Section 44AD/58 Sl. No. 1 carve this out (unlike Sl. No. 2 / Section 44AE) | MVP |

### 2.2 Non-functional requirements

| ID | Requirement |
|---|---|
| NFR-1 | All tax arithmetic is performed by deterministic, unit-tested code — never by the LLM |
| NFR-2 | The system must be measurably evaluated for hallucination (adversarial false-premise set) before being called "done" — not just demoed on happy-path questions |
| NFR-3 | No model fine-tuning; all LLM use is via prompting against a hosted API |
| NFR-4 | Single-instance deployment (Docker Compose); no orchestration platform |
| NFR-5 | No real user financial data at any point — synthetic personas only |
| NFR-6 | Every retrieval and computation decision is logged with enough detail to reconstruct why the system said what it said (explainability, not just correctness) |
| NFR-7 | The system should degrade gracefully — a retrieval miss or low-confidence classification should produce a flagged, hedged answer, never a silent wrong one |
| NFR-8 | Cost-bounded: embedding and LLM API usage should run on a student budget (see §6) |

### 2.3 Constraints (carried over, restated for completeness)

Two-person team, ~15-week timeline, no real financial data, single cloud instance, faculty-mentor checkpoints, deliverable includes a technical report.

---

## 3. High-level architecture

```
                        ┌─────────────────────┐
                        │   Next.js Frontend   │
                        │ (upload, dashboard,  │
                        │  tax + audit views)  │
                        └──────────┬───────────┘
                                   │ REST (JSON)
                        ┌──────────▼───────────┐
                        │     FastAPI Backend    │
                        │                        │
                        │  ┌──────────────────┐  │
                        │  │ Ingestion         │  │
                        │  │ (CSV/PDF parse)   │  │
                        │  └────────┬─────────┘  │
                        │           │             │
                        │  ┌────────▼─────────┐  │
                        │  │ Expense Classifier│  │
                        │  │ (LLM, few-shot)   │  │
                        │  └────────┬─────────┘  │
                        │           │             │
                        │  ┌────────▼─────────┐  │      ┌───────────────────────┐
                        │  │ RAG Retrieval     │◄─┼──────┤ PostgreSQL + pgvector  │
                        │  │ (hybrid BM25+vec, │  │      │ - document_chunks      │
                        │  │  citation verify) │  │      │   (embedding, section, │
                        │  └────────┬─────────┘  │      │    jurisdiction,       │
                        │           │             │      │    effective_date,    │
                        │  ┌────────▼─────────┐  │      │    tax_year)          │
                        │  │ Deterministic Tax │  │      │ - transactions        │
                        │  │ Engine (44ADA/58 +│  │      │ - tax_computations    │
                        │  │  DTAA Art.15/25)  │  │      │ - citations           │
                        │  └────────┬─────────┘  │      │ - audit_flags         │
                        │           │             │      │ - eval_runs           │
                        │  ┌────────▼─────────┐  │      └───────────────────────┘
                        │  │ Audit Risk Scorer │  │
                        │  │ (rule-based)      │  │
                        │  └──────────────────┘  │
                        └────────────────────────┘
```

One database, one backend service, one frontend. No message queue, no separate vector database, no microservice boundaries — the "modules" above are Python packages inside one FastAPI app, not separate deployables.

### 3.1 Request flow (example: "what's my tax liability for FY26?")

1. Frontend sends persona + tax year to `POST /tax/estimate`
2. Backend pulls the persona's classified transactions (or triggers classification if not yet done)
3. Deterministic engine computes presumptive income under the applicable Act (Section 44ADA or Section 58, selected by tax year) and checks the DTAA Article 15 90-day/fixed-base tests
4. In parallel, the RAG module retrieves the specific IT Act and DTAA passages that justify each computed figure, filtered to the persona's tax year
5. Citation verification checks each retrieved passage actually supports the claim attached to it; unsupported claims are dropped and flagged rather than shown
6. Response assembles: computed numbers (from step 3, never from the LLM) + verified citations (from step 5) + an audit-risk score (from the rule-based scorer) + a confidence/hedge flag if anything in steps 4-5 came back weak
7. Everything in this flow is logged (rule version used, chunks retrieved, confidence scores) for the eval suite and the technical report

---

## 4. Data model (concrete)

```
personas(id, name, description, base_country, has_us_presence, notes)
transactions(id, persona_id, date, amount, currency, description, source_doc_id, category, deductible, classification_confidence)
documents(id, title, jurisdiction, source_url, tax_year, effective_date, version_note)
document_chunks(id, document_id, section_id, text, embedding vector, jurisdiction, effective_date, tax_year)
tax_computations(id, persona_id, tax_year, presumptive_income, india_tax, us_tax_applicable, dtaa_relief_amount, form67_required, computed_at)
citations(id, tax_computation_id OR transaction_id, document_chunk_id, verified boolean, claim_text)
audit_flags(id, transaction_id OR tax_computation_id, flag_type, severity, reason)
eval_runs(id, run_date, eval_type, metric_name, metric_value, notes)
```

`document_chunks.embedding` is a `pgvector` column; `jurisdiction` + `effective_date` + `tax_year` are indexed and filtered on before the vector search runs, not after — that ordering is what actually fixes the temporal-misgrounding failure mode, not just having the columns.

---

## 5. API surface (v1)

| Endpoint | Purpose |
|---|---|
| `POST /personas` / `GET /personas/{id}` | Create/read synthetic personas |
| `POST /transactions/upload` | Upload CSV/PDF, triggers parsing (Form16x-style) |
| `POST /transactions/{id}/classify` | Run expense classifier on one or all pending transactions |
| `POST /tax/estimate` | Run the deterministic engine + grounded citations for a persona/tax year |
| `GET /tax/{computation_id}` | Retrieve a prior computation with its citations |
| `GET /audit-risk/{persona_id}` | Aggregated audit risk report |
| `POST /rag/query` | Internal/debug endpoint — raw retrieval + citation-verification, useful for the eval harness |
| `GET /eval/results` | Surface latest eval run metrics (for your own dashboard while building, and for the report) |

Keep this list flat — no versioned `/v1/` prefix, no GraphQL layer, no auth beyond a single shared dev token for the prototype. Add real auth only if the deployment target requires it (e.g., a public demo link) — otherwise it's a requirement nobody asked for.

---

## 6. Tech stack (with the "why," and what was rejected)

| Layer | Choice | Why | Rejected alternative |
|---|---|---|---|
| Backend | FastAPI + Pydantic + SQLAlchemy | Already specified in the synopsis; async support, validation, and ORM in one stack matches team size | Django (heavier, more scaffolding than needed) |
| Frontend | Next.js | Already specified; team likely has some familiarity; server components keep the upload/dashboard flow simple | A separate SPA + API gateway (unnecessary split for one team) |
| Database | PostgreSQL + pgvector | One database for both relational data and vectors — avoids running a second system (Pinecone/Weaviate/Chroma) that a 2-person team then has to operate and keep in sync | Dedicated vector DB — real advantage only shows up past millions of vectors, which this project won't reach |
| Embeddings | A free/self-hosted model (BGE-M3 or Nomic Embed Text v1.5) by default | Corpus is small (a handful of curated documents, not millions), so a free CPU-capable model is very likely sufficient, and it removes a per-query cost variable entirely for a student budget | A premium API embedding model (OpenAI text-embedding-3-large, Gemini embedding-001) — reasonable fallback *only if* the free model's retrieval eval scores are actually inadequate; don't default to the expensive option pre-emptively |
| Reranker | None in v1 | Rerankers only pay off when recall@50 is good but recall@3 ordering is poor — that's an empirical question you can't answer before you have retrieval eval numbers. Measure first (§8), add a cross-encoder reranker only if the data says so | Adding a reranker upfront "to be safe" — the exact over-engineering pattern the research itself warns about |
| Retrieval | Hybrid BM25 + vector (e.g. Postgres full-text search + pgvector, combined) | Confirmed by multiple sources (`Tax-Authority-RAG`, general RAG literature) that pure vector search misses exact statutory terms/section numbers | Vector-only search |
| LLM (classification + generation) | One hosted API, cost-effective tier (e.g., Claude Haiku or an equivalent small/cheap model) for classification; a stronger tier only for the final citation-grounded answer generation if the cheap tier's quality isn't sufficient | No model training or self-hosted LLM — inference infra for a fine-tuned or self-hosted model is real ops overhead this team doesn't need to take on | Fine-tuning any model (rejected per NFR-3); self-hosting an open-weight LLM (adds GPU/ops burden neither student nor free-tier hosting easily provides) |
| Deployment | Docker Compose, single VM (a $5-10/mo droplet, or a provider's free/hobby tier — check GitHub Student Developer Pack for available credits across providers before paying) | Matches the synopsis's "single cloud-hosted instance" and NFR-4 | Kubernetes, multi-region, autoscaling — none of this is needed for a prototype with a handful of concurrent demo users |
| Testing | pytest for the tax engine (unit + a handful of property-based tests via `hypothesis` for boundary conditions like the 44ADA threshold and the 90-day test edge cases); RAGAS for RAG quality; one or two Playwright smoke tests for the frontend happy path | Property-based testing specifically for the tax engine is worth the small extra effort because threshold logic is exactly where off-by-one bugs hide, and this is the component with a checkable right answer | A full E2E test suite across every UI state — not proportional to a 2-person team's time budget |
| CI | One GitHub Actions workflow: lint + type-check + pytest on every push | Keeps quality gates without build complexity | Multiple environments/matrix builds, separate deploy pipelines |
| Observability | Structured logging of every retrieval + computation decision (already required by FR-12/NFR-6), written to a table you can query, plus plain stdout logs | Doubles as your audit trail and your evaluation data — don't build a separate logging stack | A full APM/tracing platform (Datadog, etc.) |
| Secrets | `.env` file, not committed; environment variables in the container | Standard, sufficient for a prototype | A secrets manager service |

---

## 7. Non-goals, reaffirmed and sharpened

Carried over from the Implementation Plan, now justified against specific findings rather than just asserted:

- **No knowledge graph in v1.** `ita-kg` is a legitimate second retrieval paradigm, but it solves a problem (missing statutory cross-references) you haven't yet measured as a problem in your own corpus. Add it only if your retrieval eval (§8) shows relationship-dependent questions failing specifically.
- **No reranker in v1**, for the same reason — measure recall@3 first (§6 table).
- **No fine-tuning, no self-hosted LLM.** Confirmed twice over now: once by the Austrian VAT paper (RAG beats fine-tuning for auditability), once by your own team's ops capacity.
- **No generalized "any country, any treaty" rules engine.** OpenFisca's pattern (versioned rules-as-code) is worth adopting; OpenFisca's scope (dozens of countries) is not.
- **No premium embedding API by default.** Start free/self-hosted; upgrade only against measured evidence.
- **No auth system, no multi-tenancy, no Kubernetes** — unchanged from before.

---

## 8. Evaluation — the actual gate for "production grade"

Nothing above is "done" until it's measured. Minimum bar before calling v1 complete:

1. Tax engine: 100% pass on hand-verified persona scenarios, including boundary cases (income just above/below the 44ADA threshold, exactly 90 days of US presence)
2. Retrieval: recall@3 and recall@50 on a ~30-50 question hand-labeled set — this number is also what decides whether you need a reranker (§6)
3. RAGAS faithfulness / context-precision / context-recall scores on the same set
4. Adversarial false-premise set (10-15 questions) — track refusal/hedge rate, modeled directly on the 2026 hallucination paper's methodology
5. Citation verification: spot-check rate of "cited section actually supports the claim"
6. Expense classifier precision/recall, referenced loosely against the ANNA case study's reported range

If you're short on time near the deadline, cut a stretch feature (§7) before cutting an evaluation step — the evaluation results are what make the difference between "we built a demo" and "we built and validated a system," which is the actual bar for a BTech AI capstone.

---

## 9. Deployment & infrastructure (made explicit)

This was implicit in the tech-stack table above; it's worth its own section because "deploy at the end" is the most common way student projects lose a week right before the demo.

### 9.1 Containers

**Correction (2026-09-20):** this section originally specified one `docker-compose.yml` "used identically in dev and in production... no separate 'prod config' to maintain." That assumption didn't survive contact with actually building it. Dev needs live source mounts and `--reload`/`next dev` for fast iteration (ADR-011); production needs the frontend's fully-built `runner` stage, not the pre-build `deps` stage dev was pragmatically left on, and shouldn't run against bind-mounted source at all. Rather than force one file to serve both purposes, or maintain two fully separate files that can drift apart, the actual setup is Compose's own recommended split (ADR-021):

- `docker-compose.yml` -- the production-shaped base: each service builds and runs from its image as-built, no source mounts, no dev-server commands, `restart: unless-stopped`.
- `docker-compose.override.yml` -- dev-only settings (source mounts, `--reload`/`next dev`, the frontend's `deps` build target). Compose merges this automatically on top of the base whenever `docker compose up` runs with no extra flags, so local dev is a single unchanged command.

A deploy that wants the lean production shape alone runs `docker compose -f docker-compose.yml up -d --build`, explicitly excluding the override file. Three services either way:

```
services:
  db:        # postgres image with the pgvector extension (e.g. pgvector/pgvector:pg16)
  backend:   # FastAPI app, built from a single Dockerfile
  frontend:  # Next.js app, built from its own Dockerfile (or served via a PaaS's native Next.js support — see 9.2)
```

No separate containers for the RAG module, the classifier, or the tax engine — those are Python packages inside the one `backend` service, not independently deployed services. That boundary (modular monolith, not microservices) is the thing to protect as the app grows; it's easy to accidentally split into "one container per feature" and that's real, unrewarded operational overhead for a two-person team.

### 9.2 Cloud target — pick one lane, don't mix

Two reasonable options; pick based on how much you want to manage yourselves:

- **PaaS (Render / Railway free-or-hobby tier)**: push `docker-compose`-equivalent services, get TLS, a public URL, and restart-on-crash for free/near-free. Least ops work — recommended default for a two-person team without dedicated DevOps time.
- **Raw VM (a $5-10/mo droplet, or a VM funded via GitHub Student Developer Pack credits on a provider of your choice)**: run `docker compose up -d` directly on the VM, put Caddy in front for automatic HTTPS (simplest TLS option — avoids hand-rolling certbot). More control, more to babysit (OS updates, restarts after a crash, backups).

Either way, this satisfies the synopsis's "single cloud-hosted instance" requirement as-is — don't reach for anything with autoscaling, load balancers, or multiple regions; there's no traffic pattern in this project that needs it.

### 9.3 Database hosting

Two options, same reasoning as above:
- Self-hosted in the `db` container on the same VM — simplest, free, matches "single instance" literally. You own backups (a scheduled `pg_dump` via cron or a GitHub Actions scheduled workflow is enough — don't build a backup service).
- A managed Postgres with pgvector support (e.g., Neon or Supabase free tier) — slightly less to babysit (automatic backups, no OS to patch) at the cost of a second provider dependency. Reasonable if you'd rather not think about VM disk failure at all.

Default to self-hosted-in-the-same-VM unless a mentor/demo requirement (uptime during a scheduled review, say) makes the managed option worth the extra moving part.

### 9.4 CI/CD

One GitHub Actions workflow: on push to `main`, run lint + tests (already in §6), build the Docker images, and — only after tests pass — either push to the PaaS (most PaaS providers auto-deploy on a Git push, so this step may not need to exist at all) or `ssh` into the VM and run `docker compose pull && docker compose up -d`. No staging environment, no manual approval gate, no blue-green deploy — a single `main`-to-production pipeline is proportional to this project's risk level.

### 9.5 When to actually stand this up

Don't wait until Phase 4 (integration) to deploy for the first time. Add one concrete task to Phase 0 (weeks 1-2, already in `Implementation_Plan.md`): get a "hello world" version of all three containers running on the real cloud target before any real feature work starts. It's a few hours of work up front and it means every subsequent phase deploys into an environment you already know works, instead of discovering a Docker networking or environment-variable problem during the final week.

*Compiled September 10, 2026.*
