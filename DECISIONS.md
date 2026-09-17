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

<!-- New entries go below this line, in the same format, as decisions are made during implementation. -->
