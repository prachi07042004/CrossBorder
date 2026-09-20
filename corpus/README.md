# Source document corpus

Fifteen documents curated as of 2026-09-20 (started 2026-09-17) (see `PROGRESS.md` session log). Each file's own header documents its source, retrieval method, and any discrepancies found — read that header before treating the text as ground truth.

**1961 Act (India, valid through FY2025-26 — kept as prior-year support, see ADR-016):**
- Section 44ADA — presumptive taxation for professionals (`india/it-act-section-44ada/2025-26.txt`)
- Section 44AD(6) — general-business presumptive scheme's exclusion list (used only to ground Persona F's misrouting conclusion, not to build 44AD's own computation) (`india/it-act-section-44ad/2025-26.txt`)
- Section 44AA(1)-(2) — notified-profession list + bookkeeping thresholds (`india/it-act-section-44aa/2025-26.txt`)
- Section 40(b) — partnership-firm partner remuneration disallowance/cap (`india/it-act-section-40b/2025-26.txt`)
- Section 90 — the domestic provision giving the India-US DTAA legal effect (`india/it-act-section-90/2025-26.txt`)
- Section 6 — residential status test, curated for a single hand-check (Persona C), NOT wired into any computation -- residency is an explicit out-of-scope input for v1, see ADR-017 (`india/it-act-section-6/2025-26.txt`)

**Income-tax Act, 2025 (India, valid FY2026-27 onward — the project's default legal base going forward, ADR-016):**
- Section 58 — consolidated presumptive taxation (merges 44AD/44AE/44ADA into one table) (`india/it-act-2025-section-58/2026-27.txt`)
- Section 35(e) — successor to Section 40(b) (`india/it-act-2025-section-35e/2026-27.txt`)
- Section 62(4) — successor to Section 44AA(1) (`india/it-act-2025-section-62/2026-27.txt`)
- Section 159 — successor to Section 90 (merged with the old Section 90A) (`india/it-act-2025-section-159/2026-27.txt`)

**Subordinate legislation (Rules, not the Acts themselves):**
- Rule 128 of the Income-tax Rules, 1962 — foreign tax credit procedure, incl. Form No. 67 (`india/it-rules-rule-128/2025-26.txt`)
- Rule 76 of the Income-tax Rules, 2026 — successor to Rule 128, incl. Form No. 44 (`india/it-rules-2026-rule-76/2026-27.txt`)

**Treaty (India-US DTAA):** Articles 15 & 25 (`treaty/india-us-dtaa/`)

**US:** 26 U.S.C. §861(a)(3) (`us/irs-source-of-income/`)

Note the deliberate naming split: the 1961 Act's section numbers do **not** map onto the 2025 Act's — e.g. `incometaxindia.gov.in`'s "Section 58" lookup returns a completely different, unrelated 1961-Act provision. Corpus directories are named per-Act (`it-act-section-*` vs `it-act-2025-section-*`) specifically to avoid that collision; never assume a bare "Section N" reference without checking which Act it belongs to. The same trap exists one level down, in the Rules: **Form No. 67** (foreign tax credit statement, under the 1961 Act's Rule 128) becomes **Form No. 44** under the 2025 Act's Rule 76 — a bare "Form 67" reference for anything dated FY2026-27 or later is the wrong form, not just an old label for the right one.

## What goes here

The curated, version-tagged primary-source documents the RAG pipeline retrieves from — both Acts are kept in parallel (per ADR-009's temporal-tagging design), not overwritten as the law changes:

- Indian Income Tax Act (1961 and 2025) — presumptive taxation, bookkeeping/profession-eligibility gates, and partner-remuneration provisions for professional firms
- India–US DTAA text — at minimum Articles 15 (Independent Personal Services) and 25 (Elimination of Double Taxation)
- Relevant IRS guidance on source-of-income rules for independent personal services

## Rules for adding a document (per `docs/WORKING_PRINCIPLES.md`)

1. **Primary source only.** Link to the actual Act text, the actual treaty text, or the actual IRS publication — not a blog's summary of it. The blog/CA guides in `docs/System_Design_and_Requirements.md`'s reference list are for understanding the rule, not for sourcing the document that gets chunked and embedded.
2. **Tag every document** with `jurisdiction`, `effective_date`, and `tax_year` before it goes into the pipeline — this is what the temporal-filtering design (ADR-009) depends on.
3. **Note the source and retrieval date** in a short header comment or a companion `.meta.json`, so a citation can always be traced back to exactly where it came from.

## Current structure

```
corpus/
  india/
    it-act-section-44ada/
      2025-26.txt
    it-act-section-44aa/
      2025-26.txt
    it-act-section-44ad/
      2025-26.txt
    it-act-section-40b/
      2025-26.txt
    it-act-section-90/
      2025-26.txt
    it-act-section-6/
      2025-26.txt
    it-act-2025-section-58/
      2026-27.txt
    it-act-2025-section-35e/
      2026-27.txt
    it-act-2025-section-62/
      2026-27.txt
    it-act-2025-section-159/
      2026-27.txt
    it-rules-rule-128/
      2025-26.txt
    it-rules-2026-rule-76/
      2026-27.txt
  treaty/
    india-us-dtaa/
      article-15.txt
      article-25.txt
  us/
    irs-source-of-income/
      26-usc-861-a-3.txt
```

Note on verification rigor (2026-09-20): three gaps found in a pre-commit review were closed the same day -- Rule 128's "direct visual page-read" claim was ambiguous (source PDF over the page-image tool's 100MB limit, no explicit qpdf-split note like the other affected files) and has now been genuinely re-confirmed; Persona F's core legal claim (Section 44AD(6)'s exclusion list) had never actually been curated, only recalled -- now added and confirmed verbatim (`india/it-act-section-44ad/2025-26.txt`); and the four Income-tax Act, 2025 files (Section 58, 35(e), 62, 159) -- flagged as having the same possible 100MB-source-PDF ambiguity as Rule 128 -- were re-checked once the source PDF was re-supplied (it's actually only ~3.1MB, well under the limit) via genuine direct visual page-image read. No discrepancy found in any of the four. One new observation surfaced in the process, not a discrepancy: Section 58's sub-sections (5) and (7) both reference "sub-section (1)" where the actual computation happens in sub-section (2) -- confirmed as a genuine drafting artifact in the Act itself (see that file's own `cross_reference_anomaly` note), not a transcription error.
