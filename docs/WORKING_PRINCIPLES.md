# Working Principles

How this project gets built, step by step, without either the AI system we're building *or* the development process around it drifting into things nobody actually verified.

These are two different concerns and this repo treats them separately:

- **The system's own anti-hallucination design** (citation verification, refuse-if-unsupported, temporal filtering) is a product requirement — see FR-8, FR-9, NFR-2 in `docs/System_Design_and_Requirements.md`. That's what stops the *deployed app* from hallucinating tax advice.
- **This document** is about how *we*, building it, avoid the equivalent failure mode during development: adding scope that was never decided, encoding a tax rule nobody checked against a primary source, or losing track of why a choice was made.

## Rules we're actually following

1. **Every feature traces to a requirement.** If it's not an FR/NFR in `docs/System_Design_and_Requirements.md`, it doesn't get built yet — add the requirement there first (even one line), then build it. This stops silent scope creep in either direction.
2. **Every non-trivial decision gets an ADR entry.** Before (or immediately after) making a call that isn't already covered in the planning docs, add an entry to `DECISIONS.md`: what, why, what else we considered, what evidence it's based on. If we can't articulate the "why," that's a sign we're guessing.
3. **Legal and tax facts get verified against primary sources, not summaries.** The blog guides and CA-written explainers in our reference list (44ADA thresholds, DTAA articles) are a starting point for understanding, not what gets encoded into the tax engine. Before a number or rule goes into code, trace it to the actual Income Tax Act section or treaty article text, and note the source in a code comment next to the constant.
4. **The tax engine is never "probably correct."** No computation logic merges without a passing unit test against a hand-verified persona scenario (see `docs/Implementation_Plan.md` §6-7). If a scenario hasn't been hand-verified yet, that's tracked as an open task, not assumed fine.
5. **RAG output ships with its citation-verification check, not before.** We don't add a "trust the model this once" shortcut, even temporarily, even for a demo.
6. **`PROGRESS.md` is updated every work session** — what got done, what's next, what's blocked, and which `DECISIONS.md` entries (if any) it produced. State lives in the repo, not in anyone's memory of the last conversation.
7. **Uncertainty gets flagged, not smoothed over.** If something in the plan turns out to be wrong, or a fact can't be confirmed, that gets written down as an open question (in `PROGRESS.md` or the relevant doc) rather than quietly worked around.

## Where things live

| What | Where |
|---|---|
| Why we're building this, requirements, scope | `docs/System_Design_and_Requirements.md` |
| Phased build order and timeline | `docs/Implementation_Plan.md` |
| The formal SRS+SDS submission | `docs/SRS_SDS_Report_CrossBorderTax.docx` |
| Decisions made along the way, with reasoning | `DECISIONS.md` |
| Current status, next step, blockers | `PROGRESS.md` |
