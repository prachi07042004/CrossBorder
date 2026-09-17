# Source document corpus

First three documents curated as of 2026-09-17 (see `PROGRESS.md` session log): Section 44ADA (`india/it-act-section-44ada/2025-26.txt`), DTAA Articles 15 & 25 (`treaty/india-us-dtaa/`), and 26 U.S.C. §861(a)(3) (`us/irs-source-of-income/`). Each file's own header documents its source, retrieval method, and any discrepancies found — read that header before treating the text as ground truth.

## What goes here

The curated, version-tagged primary-source documents the RAG pipeline retrieves from:

- Indian Income Tax Act — Section 44ADA (presumptive taxation for professionals)
- India–US DTAA text — at minimum Articles 15 (Independent Personal Services) and 25 (Elimination of Double Taxation)
- Relevant IRS guidance on source-of-income rules for independent personal services

## Rules for adding a document (per `docs/WORKING_PRINCIPLES.md`)

1. **Primary source only.** Link to the actual Act text, the actual treaty text, or the actual IRS publication — not a blog's summary of it. The blog/CA guides in `docs/System_Design_and_Requirements.md`'s reference list are for understanding the rule, not for sourcing the document that gets chunked and embedded.
2. **Tag every document** with `jurisdiction`, `effective_date`, and `tax_year` before it goes into the pipeline — this is what the temporal-filtering design (ADR-009) depends on.
3. **Note the source and retrieval date** in a short header comment or a companion `.meta.json`, so a citation can always be traced back to exactly where it came from.

## Suggested structure (once populated)

```
corpus/
  india/
    it-act-section-44ada/
      2025-26.txt
      2026-27.txt          # only once the FY26-27 threshold/rules are confirmed
  treaty/
    india-us-dtaa/
      article-15.txt
      article-25.txt
  us/
    irs-source-of-income/
      ...
```
