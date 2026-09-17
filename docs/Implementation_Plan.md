# Implementation Plan: AI-Assisted Cross-Border Tax & Compliance System

*Companion to the project synopsis and research report. Timeline assumes a ~14-16 week semester, starting from a blank codebase.*

---

## 1. What we're actually building

A single-tenant web app where an Indian freelancer/consultant working with US clients uploads transactions, gets expenses auto-classified, and receives a source-cited estimate of their India tax (Section 44ADA presumptive scheme) and DTAA relief — with all math done by deterministic code and all legal interpretation grounded in retrieved, dated source documents. The LLM never computes a number; it only classifies and retrieves.

That split (LLM = interpretation/retrieval, code = arithmetic) is already the right call in the synopsis — the research confirms it's the field-standard pattern for legal/tax AI (fine-tuning underperforms RAG here because it can't be audited or updated without retraining). Nothing in this plan changes that decision; it just sequences the work and draws the line on what to leave out.

---

## 2. Research synthesis: what already exists, and what's actually new here

The research report's 12 sources map cleanly onto three claims worth stating explicitly in your report's related-work section:

**Single-jurisdiction legal RAG is a solved-ish pattern.** `ita-kg` (India IT Act), `bd-legal-rag` (Bangladesh), and the Austrian VAT paper each show a RAG pipeline grounded in one country's statute. Hierarchy-aware chunking (parsing Chapters/Sections before embedding, not naive character splits) is the consistent winning design across all of them.

**Nobody in your source list combines two jurisdictions plus a bilateral treaty.** None of the 12 resources retrieve across India *and* US sources and reconcile them through DTAA articles. That's the genuine gap this project sits in, and it's a legitimate framing for your introduction: existing tools are single-country; cross-border freelancers need treaty-aware reasoning, which requires retrieval over two legal corpora simultaneously plus a rule layer that knows which treaty article overrides which domestic rule.

**Grounding does not equal correctness, and this needs to shape your evaluation, not just your architecture.** Two things I found extend the "Temporal Misgrounding" paper already in your list:

- [How Much Do Legal RAG Systems Still Hallucinate?](https://arxiv.org/html/2608.14210) (arXiv, 2026) benchmarks several legal-RAG configurations and finds even the best (BM25 + GPT-5) still hallucinates on ~1.5% of individual claims and ~20% of full answers — and on questions containing a *false premise*, hallucination jumps to 75-100%. That last number matters directly for you: users will ask things like "can I deduct my personal laptop under 44ADA?" with built-in wrong assumptions, and that's exactly the failure mode this paper shows RAG handles worst.
- [RAG Is Judgment: Why Grounding Does Not Solve the Legal Hallucination Problem](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6945200) (SSRN, 2026) argues retrieval reduces but doesn't eliminate the problem — the system still has to *judge* whether retrieved text actually answers the question, which is a reasoning step, not a lookup step.

The practical consequence: don't treat "we added RAG" as the finish line. Build an explicit eval harness (Section 7) including adversarial false-premise questions, and design the system to refuse or hedge rather than answer when retrieval confidence is low.

---

## 3. Additional resources found (beyond the original 12)

| # | Resource | Why it matters for this project |
|---|----------|----------------------------------|
| 1 | [How Much Do Legal RAG Systems Still Hallucinate?](https://arxiv.org/html/2608.14210) (arXiv, 2026) | Gives you a concrete benchmark methodology (claim-level + answer-level hallucination scoring) to adapt for your own evaluation, and a false-premise test design you should copy. |
| 2 | [RAG Is Judgment: Why Grounding Does Not Solve the Legal Hallucination Problem](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6945200) (SSRN, 2026) | Justifies why your system needs a "refuse if unsupported" behavior, not just citations — good citation for your report's discussion of limitations. |
| 3 | [Citation Grounding: Detecting and Reducing LLM Citation Hallucinations via Legal Citation Graphs](https://arxiv.org/abs/2606.00898) (arXiv, 2026) | A concrete technique for verifying that a cited section actually supports the claim made — directly applicable to your source-citation feature. |
| 4 | [RAGAS: Automated Evaluation of Retrieval Augmented Generation](https://arxiv.org/abs/2309.15217) | The standard open-source library for scoring faithfulness, answer relevance, and context precision/recall. Use this instead of building your own eval metrics from scratch. |
| 5 | [Evaluation of Retrieval-Augmented Generation: A Survey](https://arxiv.org/abs/2405.07437) (arXiv, 2024) | Reference for justifying your choice of eval metrics in the technical report. |
| 6 | [OpenFisca](https://openfisca.org/en/) — "rules as code" engine (France, Spain, Japan packages) | Not directly reusable (no India package exists), but its design pattern — separate the *legislation model* from the *application logic*, and version rules by effective date — is exactly the pattern your PostgreSQL schema already needs for 44ADA thresholds changing year to year. Worth citing as prior art for "rules as code" in tax systems generally. |
| 7 | [Legal Chunking: Evaluating Methods for Effective Legal Text Retrieval](https://www.researchgate.net/publication/386472016) | A second data point (beyond `bd-legal-rag`) confirming hierarchy-aware chunking beats naive chunking specifically for statutory text — useful corroboration for your methodology section. |
| 8 | [DTAA Between India and USA — Complete Guide](https://www.dineshaarjav.com/blog-detail/dtaa-between-india-and-the-usa) | Gives the actual mechanics your deterministic engine needs to encode: **Article 15** (Independent Personal Services — income stays taxable only in India unless the consultant has a fixed US base or is physically present in the US ≥90 days); **Article 25** (foreign tax credit, if US tax does apply, capped at the Indian tax attributable to that income); and the **Form 67 / Form 10F / Tax Residency Certificate** documentation chain. This is the concrete rule set for your DTAA module — treat it as a spec, verify it against the primary treaty text, and don't reinvent this logic from scratch. |
| 9 | [ANNA: Cost-Effective LLM Transaction Categorization for Business Banking](https://www.zenml.io/llmops-database/cost-effective-llm-transaction-categorization-for-business-banking) | An industry (not academic) case study of LLM-based transaction categorization at production scale — useful as a benchmark for what "good enough" accuracy and cost look like for your expense classifier, so you're not guessing at a target. |

Combined with the original 12, that's a solid literature base — you don't need to keep searching for more before you start building. Time is better spent implementing now.

---

## 4. Scope: what's in v1, what's later, what we're deliberately not building

This is the "don't over-engineer" section. The synopsis is well-scoped already; the risk is scope creep during implementation, not the plan itself.

**In scope for the semester (v1):**
- Transaction/invoice upload (CSV + a handful of PDF invoices)
- LLM-based expense classification (few-shot prompting against a fixed category taxonomy — no fine-tuning)
- RAG pipeline over a **curated, fixed** set of documents: the relevant India IT Act sections (44ADA), the India-US DTAA text (Articles 15 and 25 at minimum), and IRS guidance on source-of-income for independent personal services
- Deterministic engine: 44ADA presumptive tax calculation + DTAA Article 15 (90-day test) + Article 25 (FTC) for the specific persona scenarios you define
- Rule-based audit risk meter (a scoring function over missing-documentation flags, threshold proximity, low-confidence classifications — not a trained model)
- Source citations on every retrieved rule shown to the user
- Next.js dashboard, FastAPI backend, Dockerized single-instance deployment
- Evaluation suite (Section 7) and the technical report

**Explicitly out of scope / future work (say this in your report, don't apologize for it):**
- A knowledge-graph layer like `ita-kg` — valuable, but it's a second retrieval paradigm on top of RAG; adding it now is the classic over-engineering trap. Note it as future work.
- A general "rules as code" engine in the OpenFisca sense that could handle *any* country's tax law — you need exactly two jurisdictions and one treaty; build that, not a platform.
- Fine-tuning any model. Few-shot / prompted classification is sufficient at this scale and keeps the system auditable.
- Multi-tenant auth, role-based access, horizontal scaling, Kubernetes — single-instance Docker deployment is what the synopsis already specifies and is right for a prototype.
- Supporting arbitrary countries/treaties beyond India-US — the DTAA logic is treaty-specific; generalizing it is a research project on its own.
- PaySim as your actual seed data. It's a fraud-detection dataset (cash-in/cash-out/transfer patterns) — useful as a *schema reference* for transaction fields, but your personas need income/expense/invoice shapes specific to freelance consulting, not mobile-money fraud patterns. Build 4-6 hand-crafted personas instead (see Section 6).

---

## 5. Architecture (right-sized)

A modular monolith, not microservices — two people, one semester, single deployment target.

```
Next.js dashboard
      |
      v
FastAPI backend  ──────────────┐
 ├─ ingestion module           │
 ├─ expense classifier (LLM)   │
 ├─ RAG retrieval module ──────┼── PostgreSQL + pgvector
 │    (hybrid: BM25 + vector)  │    ├─ documents (chunked, versioned by effective_date/tax_year)
 ├─ deterministic tax engine   │    ├─ transactions / users (synthetic)
 │    (Pydantic + SQLAlchemy)  │    └─ audit flags / eval logs
 └─ audit risk scorer ─────────┘
```

Key design constraints worth stating in the report:
- **Document metadata schema must carry `jurisdiction`, `effective_date`, and `tax_year`** on every chunk — this is the direct fix for the temporal-misgrounding failure mode your own research flagged, and it's cheap to build in now versus retrofitting later.
- **Hybrid retrieval (BM25 + vector), not vector-only** — the research consistently shows pure vector search misses exact statutory phrase matches (section numbers, defined terms) that keyword search catches.
- **The LLM never touches arithmetic.** Every number in the final output traces to a Pydantic-validated function, unit-tested against hand-verified scenarios.

---

## 6. Data: synthetic personas over adapted datasets

Build 4-6 personas by hand (e.g., "software consultant, ₹40L/year from one US client, no US presence," "designer, mixed India+US clients, crosses the 90-day US visit threshold once") with realistic invoices and 20-40 transactions each. This gives you known-correct ground truth to test the tax engine against — something a generic fraud dataset like PaySim can't give you, since you need *tax-correct* answers to grade the deterministic engine, not just plausible-looking transactions. Use PaySim (or its schema) only if you need volume for stress-testing ingestion performance, not for tax-logic correctness testing.

---

## 7. Evaluation plan (this is what makes it "production grade," not the tech stack)

1. **Tax engine correctness**: unit tests for every persona scenario, hand-verified against the primary sources (IT Act text, actual DTAA articles) — not against a blog post. Treat the CA-guide sources in your research report as a starting point to check, not ground truth to trust blindly.
2. **RAG quality**: use RAGAS (or an equivalent lightweight faithfulness/context-precision/context-recall check) against a hand-labeled set of ~30-50 question-answer pairs drawn from your source documents.
3. **Adversarial false-premise test set**: 10-15 questions built with a wrong assumption baked in (e.g., "since I paid US tax, I don't need to file in India, right?") — directly modeled on the failure mode the 2026 hallucination paper identified. Track whether the system correctly pushes back rather than confidently answering the false premise.
4. **Citation verification**: spot-check that every cited section actually contains the claim attributed to it (manual for v1; the citation-graph paper in Section 3 is a good stretch goal if time allows).
5. **Expense classifier accuracy**: precision/recall against your hand-labeled persona transactions, benchmarked loosely against the ANNA case study's reported accuracy range so you have an external reference point, not just an internal number.

---

## 8. Phased timeline (~15 weeks, blank slate)

| Weeks | Phase | Deliverable |
|-------|-------|-------------|
| 1-2 | Setup & corpus curation | Repo, Docker Compose skeleton (db + backend + frontend) **deployed as a "hello world" to the real cloud target**, CI; curated + versioned source documents (44ADA text, DTAA Articles 15 & 25, relevant IRS guidance) with the jurisdiction/effective_date/tax_year metadata schema decided — see `System_Design_and_Requirements.md` §9 for the deployment specifics |
| 3-5 | Deterministic tax engine | Pydantic models, 44ADA calc, DTAA Article 15 (90-day test) + Article 25 (FTC) logic, full unit test suite against hand-verified persona scenarios — build and lock this down first, since the RAG layer grounds *into* it |
| 5-8 | RAG pipeline (overlaps engine work) | Ingestion + hierarchy-aware chunking, pgvector storage, hybrid BM25+vector retrieval, citation-required prompting; first pass of the RAGAS-style eval harness running continuously as the corpus grows |
| 8-10 | Expense classifier + audit risk meter | Few-shot classification against fixed taxonomy, confidence scoring, rule-based audit flag logic |
| 10-12 | Integration | FastAPI wiring, Next.js dashboard (upload, tax summary with citations, audit report), end-to-end flow working on all personas |
| 12-14 | Evaluation & hardening | Full eval suite run (tax engine, RAG, adversarial set, classifier), fix what breaks, write the technical report |
| 14-15 | Buffer | Mentor review iteration, demo prep, deployment polish |

Front-loading the deterministic engine (weeks 3-5) before the RAG pipeline is deliberate: it's the part with a checkable right answer, it's what the LLM output ultimately has to agree with, and it de-risks the highest-stakes correctness claim in the whole project before you're deep into retrieval tuning.

---

## 9. Risk register

| Risk | Mitigation |
|------|-----------|
| Temporal misgrounding (retrieving the wrong tax year's rule) | Mandatory effective_date/tax_year metadata filtering at retrieval time, tested explicitly |
| RAG hallucination, especially on false-premise questions | Adversarial eval set (Section 7.3) + explicit refuse-if-unsupported design, not just citations |
| DTAA logic is genuinely subtle (treaty interpretation, not just arithmetic) | Verify every rule against the primary treaty text and IT Act sections, not blog summaries; get faculty mentor sign-off on the persona scenarios before building the engine around them |
| Scope creep (knowledge graph, multi-country support, fine-tuning) | Section 4's explicit "not building" list — revisit only if core v1 is done early |
| Synthetic data unrealistic | Hand-crafted personas reviewed against real-world scenarios described in the freelancer tax guides already in your research report |

---

## 10. Deliverables checklist (maps to synopsis "Expected Outcome")

- [ ] Deployed web app: upload → classification → tax estimate with DTAA relief → citations → audit risk report
- [ ] Documented, unit-tested deterministic tax engine
- [ ] Functioning RAG pipeline with versioned, dated source corpus
- [ ] Evaluation results (RAGAS-style metrics + adversarial false-premise results + tax engine test coverage)
- [ ] Technical report: architecture, design decisions, related-work/gap framing (Section 2), evaluation results, limitations (explicitly: "educational prototype, not legally binding advice")

---

## References

**From the original research report:**
1. Temporal Misgrounding in Legal RAG: A Versioned-Corpus Benchmark for French Tax Law — arXiv, 2026
2. Using Large Language Models for Legal Decision-Making in Austrian VAT Law — arXiv, 2025
3. Towards Reliable Retrieval in RAG Systems for Large Legal Datasets — arXiv, 2025
4. The Impact of AI on Tax Compliance and Reporting — IJMSRT, 2024
5. srijanshukla18/ita-kg (Income Tax Act Knowledge Graph + RAG) — GitHub
6. rohitthink/freefile (Freelancer Tax Tracker) — GitHub
7. mralaminahamed/bd-legal-rag (Hierarchy-Aware Statutory RAG) — GitHub
8. Mbehbahani/Tax-Authority-RAG (Citation-First Tax Assistant) — GitHub
9. ri-sh/Form16x (Offline Tax Document Parsing) — GitHub
10. 44ADA for Software Developers — TaxTap
11. Freelancer Tax India: Section 44ADA, Foreign Clients & BRC — TaxClue
12. PaySim Synthetic Dataset — GitHub/Kaggle

**Newly identified (this session):**
13. [How Much Do Legal RAG Systems Still Hallucinate?](https://arxiv.org/html/2608.14210) — arXiv, 2026
14. [RAG Is Judgment: Why Grounding Does Not Solve the Legal Hallucination Problem](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6945200) — SSRN, 2026
15. [Citation Grounding: Detecting and Reducing LLM Citation Hallucinations via Legal Citation Graphs](https://arxiv.org/abs/2606.00898) — arXiv, 2026
16. [RAGAS: Automated Evaluation of Retrieval Augmented Generation](https://arxiv.org/abs/2309.15217) — arXiv, 2023
17. [Evaluation of Retrieval-Augmented Generation: A Survey](https://arxiv.org/abs/2405.07437) — arXiv, 2024
18. [OpenFisca](https://openfisca.org/en/) — rules-as-code engine (reference architecture, not a direct dependency)
19. [Legal Chunking: Evaluating Methods for Effective Legal Text Retrieval](https://www.researchgate.net/publication/386472016) — ResearchGate
20. [DTAA Between India and USA — Complete Guide](https://www.dineshaarjav.com/blog-detail/dtaa-between-india-and-the-usa) — verify against primary treaty text before encoding into the engine
21. [ANNA: Cost-Effective LLM Transaction Categorization for Business Banking](https://www.zenml.io/llmops-database/cost-effective-llm-transaction-categorization-for-business-banking) — ZenML LLMOps Database

*Compiled September 10, 2026.*
