"""Pydantic models for the deterministic tax engine -- Phase 1, first increment.

Scope of this increment (see PROGRESS.md, 2026-09-20): the Section 44ADA /
Income-tax Act 2025 Section 58 (Table Sl. No. 3) presumptive-income
computation only, covering Personas A, B1, B2, and G from docs/personas.md.
DTAA Article 15/25 logic (Personas C, D), partnership-firm remuneration
interaction (Persona E), and misrouting to Section 44AD / Section 58 Sl. No. 1
for an ineligible profession (Persona F) are NOT yet implemented -- see the
"Next" note in PROGRESS.md. Fields needed only for those are deliberately
left out of these models rather than added unused, per Implementation_Plan.md
Section 4's "don't over-engineer" scoping.
"""
from __future__ import annotations

from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


class LegalInstrument(str, Enum):
    """Which Act's presumptive-taxation provision governs a given tax year.

    Selection is by tax year per ADR-016: the Income-tax Act, 2025 governs
    FY2026-27 onward; the Income-tax Act, 1961 remains the applicable law for
    FY2025-26 and earlier and is retained as prior-year support, not
    deprecated. This mirrors corpus/METADATA_SCHEMA.md's tax_year_start /
    tax_year_end convention exactly, so the same "YYYY-YY" strings used to
    tag corpus documents are what this engine takes as input.
    """

    IT_ACT_1961 = "Income Tax Act, 1961 (Section 44ADA)"
    IT_ACT_2025 = "Income-tax Act, 2025 [No. 30 of 2025] (Section 58, Table Sl. No. 3)"


class EntityType(str, Enum):
    INDIVIDUAL = "individual"
    PARTNERSHIP_FIRM = "partnership_firm"  # not an LLP
    LLP = "llp"  # excluded from 44ADA / Section 58 Sl. No. 3 -- see the eligibility gate in presumptive.py


class PresumptiveIncomeInput(BaseModel):
    """One tax year's facts for a single assessee, as needed to run the
    Section 44ADA / Section 58 (Sl. No. 3) presumptive-income computation.
    Matches the fact pattern each of Personas A, B1, B2, G states in
    docs/personas.md.
    """

    persona_label: str = Field(description="For traceability back to docs/personas.md, e.g. 'A -- Anika'.")
    tax_year: str = Field(
        description='Previous year in "YYYY-YY" form, e.g. "2025-26". Selects the legal_instrument per ADR-016.'
    )
    is_specified_profession: bool = Field(
        description="Whether the assessee's profession is on the Section 44AA(1) / Section 62(4) named list (or "
        "Board-notified). This engine does NOT itself determine this -- see "
        "corpus/india/it-act-section-44aa/2025-26.txt and corpus/india/it-act-2025-section-62/2026-27.txt for the "
        "named lists; the caller must resolve this first. A false value is rejected (see "
        "PresumptiveIncomeResult.eligible) rather than silently computed, since 44ADA / Section 58 Sl. No. 3 do not "
        "apply at all in that case (Persona F's fact pattern -- not yet implemented, see PROGRESS.md)."
    )
    entity_type: EntityType
    resident_in_india: bool = Field(
        description="Taken as a given input, not computed -- Section 6 residency determination is an explicit "
        "out-of-scope input for this project (FR-15, ADR-017)."
    )
    gross_receipts: Decimal = Field(gt=0, description="Total gross receipts of the profession for the previous year, in INR.")
    cash_receipts: Decimal = Field(
        ge=0,
        description="The portion of gross_receipts received in cash (or a cash-equivalent per the deeming provisos: a "
        "non-account-payee cheque/draft), in INR.",
    )
    claimed_actual_profit: Decimal | None = Field(
        default=None,
        description="If the assessee claims a specific actual profit instead of accepting the deemed presumptive "
        "figure, that number. Both 44ADA(1) and Section 58(2) col. E allow 'a sum higher than the aforesaid sum "
        "claimed to have been earned' -- i.e. the assessee can declare MORE than the presumptive figure, and the "
        "deemed profit is whichever is higher. None of Personas A/B1/B2/G exercise this; included because both "
        "source provisions state it as part of the same sentence being modeled, not as a separate optional feature.",
    )

    @field_validator("cash_receipts")
    @classmethod
    def _cash_not_negative_relative_to_gross(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("cash_receipts cannot be negative")
        return v

    @model_validator(mode="after")
    def _cash_not_more_than_gross(self) -> PresumptiveIncomeInput:
        if self.cash_receipts > self.gross_receipts:
            raise ValueError("cash_receipts cannot exceed gross_receipts")
        return self


class PresumptiveIncomeResult(BaseModel):
    persona_label: str
    legal_instrument: LegalInstrument
    eligible: bool = Field(description="False if the profession/entity/residency gate fails -- see ineligibility_reason.")
    ineligibility_reason: str | None = None
    threshold_applied: Decimal | None = Field(
        default=None, description="Rs. 50,00,000 or Rs. 75,00,000 -- whichever threshold the cash-receipts test resolved to."
    )
    cash_proviso_applied: bool | None = Field(
        default=None, description="True if the <=5% cash-receipts proviso raised the threshold to Rs. 75,00,000."
    )
    qualifies_for_presumptive_scheme: bool | None = Field(
        default=None,
        description="False if gross_receipts exceeds the applicable threshold -- '44ADA/Section 58 does not apply "
        "this year' (Persona B2's outcome). Normal-provisions computation and the Section 44AB/63 audit-trigger "
        "check are out of scope for this increment.",
    )
    presumptive_income: Decimal | None = Field(
        default=None,
        description="50% of gross_receipts, or claimed_actual_profit if higher -- only set when "
        "qualifies_for_presumptive_scheme is True.",
    )
    citation: str | None = Field(default=None, description="The specific corpus document this figure traces to.")
