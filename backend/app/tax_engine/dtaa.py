"""India-US DTAA Article 15 (Independent Personal Services) exposure, and the
Article 25 (Relief From Double Taxation) mechanism.

Article 15 is fully computed by this module. Article 25's credit is computed
too, but ONLY when the caller supplies both us_tax_paid and
india_tax_attributable as optional arguments to compute_article_25_relief()
-- neither is computed by this project yet (US NRA taxation under 26 U.S.C.
Section 871(b)/872 and India's progressive slab-rate calculation are both
separate, not-yet-started work; see ADR-012 and PROGRESS.md). Taking them as
optional inputs rather than hardcoding "always None" means the two future
calculators just need to be wired in as callers of this function later --
this function's own logic won't need to change. Until then, it reports
exactly which of the two inputs is still missing.

Scope, matching Personas C and D in docs/personas.md exactly:
- Article 15(1)(b), the 90-day test: aggregate US days >= 90 exposes the
  FULL presumptive income to US tax -- the treaty text carries no
  attribution limitation for this branch (Persona C).
- Article 15(1)(a), the fixed-base test: a fixed base "regularly available"
  in the US exposes only the income "attributable to that fixed base" --
  here, presumptive_income is pro-rated by the same ratio as the underlying
  gross receipts (Persona D; ADR-013 -- a documented modeling choice, not a
  rule stated by either the statute or the treaty).
- If both conditions are met (90+ days AND a fixed base), the 90-day branch
  governs: its all-or-nothing rule already exposes the full income, so there
  is nothing left for the fixed-base attribution to narrow. Not exercised by
  any current persona, but is the only reading consistent with para 1(b)'s
  plain text ("may also be taxed" with no limitation) rather than treating
  the two branches as if they had to combine into some other figure.
- Neither condition met: Article 15 does not apply at all; income remains
  taxable only in India (para 1's default rule).

Explicitly NOT implemented here (see PROGRESS.md, ADR-012):
- 26 U.S.C. Section 861(a)(3), the domestic-law sourcing exception distinct
  from Article 15 -- flagged in that corpus file as scope-undecided, not
  built into this engine.
- Section 6 residential-status determination -- taken as a given input
  upstream (ADR-017); this module assumes India residency has already been
  established for the assessee it's called on.

Primary sources:
- corpus/treaty/india-us-dtaa/article-15.txt
- corpus/treaty/india-us-dtaa/article-25.txt
"""
from __future__ import annotations

from decimal import Decimal

from .models import (
    Article15Branch,
    Article15Input,
    Article15Result,
    Article25ReliefResult,
)

NINETY_DAYS = 90  # Article 15(1)(b): "amounting to or exceeding in the aggregate 90 days" -- inclusive

ARTICLE_15_CITATION = "corpus/treaty/india-us-dtaa/article-15.txt, Article 15(1)"
ARTICLE_25_CITATION = "corpus/treaty/india-us-dtaa/article-25.txt, Article 25(2)(a)"


def compute_article_15_exposure(data: Article15Input) -> Article15Result:
    if data.us_days_present >= NINETY_DAYS:
        return Article15Result(
            persona_label=data.persona_label,
            branch_triggered=Article15Branch.NINETY_DAY,
            india_taxable_income=data.presumptive_income,
            us_taxable_income=data.presumptive_income,
            attribution_ratio=None,
            citation=ARTICLE_15_CITATION,
        )

    if data.has_fixed_base_in_us and data.fixed_base_attributable_gross_receipts > 0:
        ratio = data.fixed_base_attributable_gross_receipts / data.gross_receipts
        us_taxable = (data.presumptive_income * ratio).quantize(Decimal(1))
        return Article15Result(
            persona_label=data.persona_label,
            branch_triggered=Article15Branch.FIXED_BASE,
            india_taxable_income=data.presumptive_income,
            us_taxable_income=us_taxable,
            attribution_ratio=ratio,
            citation=ARTICLE_15_CITATION,
        )

    return Article15Result(
        persona_label=data.persona_label,
        branch_triggered=Article15Branch.NOT_TRIGGERED,
        india_taxable_income=data.presumptive_income,
        us_taxable_income=Decimal(0),
        attribution_ratio=None,
        citation=ARTICLE_15_CITATION,
    )


def compute_article_25_relief(
    article_15_result: Article15Result,
    us_tax_paid: Decimal | None = None,
    india_tax_attributable: Decimal | None = None,
) -> Article25ReliefResult:
    """us_tax_paid and india_tax_attributable are optional -- omit either (or
    both) and the result reports which is still missing rather than
    computing a credit. Supply both once they're available from their own
    (not-yet-built) calculators and this function computes the actual
    Article 25(2)(a) credit: min(us_tax_paid, india_tax_attributable).
    """
    if article_15_result.us_taxable_income == 0:
        return Article25ReliefResult(
            persona_label=article_15_result.persona_label,
            relief_applicable=False,
            us_taxable_income=Decimal(0),
            computation_status="not_applicable",
            citation=ARTICLE_25_CITATION,
        )

    if us_tax_paid is not None and india_tax_attributable is not None:
        return Article25ReliefResult(
            persona_label=article_15_result.persona_label,
            relief_applicable=True,
            us_taxable_income=article_15_result.us_taxable_income,
            computation_status="computed",
            us_tax_paid=us_tax_paid,
            india_tax_attributable=india_tax_attributable,
            credit_amount=min(us_tax_paid, india_tax_attributable),
            citation=ARTICLE_25_CITATION,
        )

    missing = []
    if us_tax_paid is None:
        missing.append(
            "US tax paid (needs 26 U.S.C. Section 871(b)/872 + Form 1040-NR research not yet done, ADR-012)"
        )
    if india_tax_attributable is None:
        missing.append(
            "India tax attributable to the US-taxable income (needs the progressive slab-rate computation, "
            "separate not-yet-started Phase 1 work)"
        )

    return Article25ReliefResult(
        persona_label=article_15_result.persona_label,
        relief_applicable=True,
        us_taxable_income=article_15_result.us_taxable_income,
        computation_status="pending_inputs",
        us_tax_paid=us_tax_paid,
        india_tax_attributable=india_tax_attributable,
        pending_reason=(
            "Credit = min(US tax paid, India tax attributable to the US-taxable income), per Article 25(2)(a). "
            "Still missing: " + "; ".join(missing) + ". See docs/personas.md Persona C."
        ),
        citation=ARTICLE_25_CITATION,
    )
