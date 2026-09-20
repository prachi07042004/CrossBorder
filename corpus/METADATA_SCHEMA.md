# Corpus metadata schema (v1)

This formalizes the `jurisdiction` / `effective_date` / `tax_year` metadata that `corpus/README.md` has required informally since the corpus existed, and that ADR-009 depends on: retrieval must filter `document_chunks` on jurisdiction, effective date, and tax year *before* ranking runs, not after. That only works if those three things are stored as precise, machine-comparable values -- not as prose. This is the last open item under Phase 0 in `PROGRESS.md`.

## Why a new field set, not just tightening the existing one

Every corpus file already carries a free-text header (`jurisdiction:`, `effective_date:`, `tax_year:`, `retrieval_method:`, plus assorted notes). That prose has real, proven value -- it's how three separate retrieval-method overstatements got caught this session (ADR-018, ADR-019). This schema does not replace it. It adds a second, smaller block of **structured** fields alongside the existing prose, because two things the prose can't do reliably are: (1) get parsed into `documents`/`document_chunks` columns without a human reading every file, and (2) get compared against each other (`tax_year: "currently applicable for FY 2023-24 (AY 2024-25) through the present..."` is not something a WHERE clause can filter on).

The new fields are namespaced `schema_v1_*` so they're unambiguous against the legacy free-text keys of the same name (`jurisdiction:`, `retrieval_method:`) that already exist in every file and are kept as-is.

## Required fields, every document

| Field | Type | Description |
|---|---|---|
| `schema_v1_doc_id` | string, unique | Slug identifying this document -- matches its corpus directory path (e.g. `india-1961-sec-44ada`). |
| `schema_v1_jurisdiction` | enum: `IN` \| `US` \| `IN-US-DTAA` | Coarse jurisdiction, matching the `documents.jurisdiction` / `document_chunks.jurisdiction` columns in `System_Design_and_Requirements.md` §4. Deliberately coarser than "which Act" -- see next field. |
| `schema_v1_legal_instrument` | string, controlled vocabulary | The specific Act, Rules, or treaty this document is part of (e.g. `"Income Tax Act, 1961"`, `"Income-tax Act, 2025 [No. 30 of 2025]"`, `"Income-tax Rules, 1962"`, `"Income-tax Rules, 2026"`, `"India-US DTAA (1989)"`, `"26 U.S.C. (US Code)"`). This is what disambiguates the two Acts that share `jurisdiction: IN` -- `tax_year_start`/`tax_year_end` alone are sufficient to route a query to the right one **only if** they're populated correctly, so this field is a redundant, human-checkable cross-check, not just decoration. |
| `schema_v1_section_ref` | string | The section, article, or rule number (e.g. `"44ADA"`, `"58"`, `"Article 15"`, `"861(a)(3)"`, `"Rule 128"`). |
| `schema_v1_tax_year_start` | string `"YYYY-YY"` or `null` | Earliest Indian fiscal year (previous year) this document's *current* text governs. `null` only when genuinely not independently dated (flag in `schema_v1_ambiguous_fields`, don't guess). |
| `schema_v1_tax_year_end` | string `"YYYY-YY"` or `null` | Last fiscal year this document's text governs. `null` means still current / not yet superseded as of `retrieved_date`. |
| `schema_v1_effective_from` | ISO 8601 date or `null` | Calendar date the current text became legally operative. |
| `schema_v1_effective_to` | ISO 8601 date or `null` | Calendar date it stops (or stopped) applying; `null` if still current. |
| `schema_v1_retrieval_method` | enum: `visual_page_read` \| `text_extraction` \| `user_pasted_text` \| `web_fetch` | What was actually done, as a hard field rather than prose -- prose claims of this exact thing were overstated three separate times this session (ADR-018/019) before being caught. |
| `schema_v1_visually_confirmed` | boolean | `true` only if a rendered page image was genuinely read (not inferred from `retrieval_method` prose). This is the field meant to make the ADR-018 failure mode structurally harder to repeat: a reviewer can grep for `visually_confirmed: false` directly instead of having to notice a missing qualifier in a paragraph. |
| `schema_v1_ambiguous_fields` | string (comma list) or `"none"` | Any field above whose value required inference, or that a primary source couldn't fully confirm. Required to be explicit rather than silently picking a value -- per `WORKING_PRINCIPLES.md` rule 7. |

## Not required / stays free text

Everything else already in use (`why_curated`, `scope_note`, `relation_to_*`, `key_finding_for_persona_*`, `known_discrepancy_resolved`, `correction_from_previous_version`, `verification_correction`, `protocol_note`, `directionality_note`, `cross_reference_anomaly`, etc.) stays exactly as-is. This schema only formalizes the fields that need to be machine-comparable; the narrative fields are doing their job and constraining them would lose real information for no gain.

## Mapping to the eventual DB schema

`System_Design_and_Requirements.md` §4's `documents` and `document_chunks` tables take `jurisdiction`, `effective_date`, `tax_year` directly. The mapping at ingestion time (Phase 2, not yet built):

- `documents.jurisdiction` <- `schema_v1_jurisdiction`
- `documents.effective_date` <- `schema_v1_effective_from` (the DB column is singular; `schema_v1_effective_to` has no direct DB column yet -- see "Open question" below)
- `documents.tax_year` <- `schema_v1_tax_year_start` (same caveat)
- `documents.title` <- `schema_v1_legal_instrument` + `schema_v1_section_ref`, concatenated
- `document_chunks.jurisdiction` / `.effective_date` / `.tax_year` <- denormalized from the parent `documents` row per ADR-009, unchanged by this schema

**Open question, not resolved here:** the current DB schema has a single `effective_date`/`tax_year` column per row, not a start/end range. That's fine for documents that are still current (`_end`/`_to` = `null`), but Personas A-F's documents (1961 Act, superseded 2026-04-01) genuinely need a range to filter correctly once a query asks about a *past* tax year. Whether to add `tax_year_end`/`effective_to` columns to `document_chunks`, or to instead insert a new document row per amendment with non-overlapping single dates, is a real Phase 2 design decision -- flagged here rather than silently assumed either way when the ingestion pipeline gets built.

## Compliance pass against the current corpus (2026-09-20)

All 15 corpus documents as of this date have been given a `schema_v1_*` block, retrofitted from what each file's own existing header already stated (this was a normalization pass, not new legal research -- no new primary-source claims were made beyond what each file already asserted). Three files have a genuinely open `schema_v1_ambiguous_fields` entry, carried over from caveats already present in that file's own prose before this schema existed:

- `india/it-act-section-6/2025-26.txt` -- the Finance Act 2020-era sub-provisions' exact effective date was never independently verified (the file's own header already said so).
- `treaty/india-us-dtaa/article-15.txt` and `article-25.txt` -- `effective_from` is set to the treaty's entry-into-force date (1990-12-18), not a confirmed first-applicable Indian assessment year, which can be a different thing for a treaty; and `tax_year_start`/`tax_year_end` are left `null` for both, since a treaty doesn't have the same single-year applicability shape as a domestic statute -- filtering on `effective_from`/`effective_to` alone is what's meant to work for these two.

Two files (`it-act-section-44aa`, `it-act-section-90`) have `tax_year_start`/`effective_from` left `null` because their base text is described in their own headers as "long-standing," with no specific enactment date independently confirmed in this project -- also not new information, just now flagged in a structured field instead of only in prose.
