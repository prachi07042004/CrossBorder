"""Pydantic models for the deterministic tax engine.

Increment 1 (2026-09-20): Section 44ADA / Income-tax Act 2025 Section 58
(Table Sl. No. 3) presumptive-income computation, covering Personas A, B1,
B2, and G from docs/personas.md.

Increment 2 (2026-09-20, cont.): DTAA Article 15 (Independent Personal
Services) exposure and Article 25 (relief from double taxation), covering
Personas C and D. Article 15 is fully computed. Article 25 is represented
only as far as docs/personas.md's own Persona C file goes: the credit
mechanism (min(US tax paid, India tax attributable)) is modeled, but both
inputs to that cap are left explicitly pending rather than guessed --
India's progressive slab-rate computation is separate not-yet-started
Phase 1 work, and the US-side figure needs 26 U.S.C. Section 871(b)/872 +
Form 1040-NR research this project has not done (ADR-012). See PROGRESS.md.

Partnership-firm remuneration interaction (Persona E) and misrouting to
Section 44AD / Section 58 Sl. No. 1 for an ineligible profession (Persona F)
are NOT yet implemented -- see the "Next" note in PROGRESS.md. Fields needed
only for those are deliberately left out of these models rather than added
unused, per Implementation_Plan.md Section 4's "don't over-engineer" scoping.
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
    partner_remuneration_authorized: Decimal | None = Field(
        default=None,
        ge=0,
        description="For a PARTNERSHIP_FIRM only: the total remuneration the partnership deed authorises to "
        "working partners under Section 40(b) / Section 35(e), for citation/audit-trail purposes ONLY. This "
        "figure is carried through to PresumptiveIncomeResult.partner_remuneration_note but is NEVER subtracted "
        "from presumptive_income -- Section 44ADA(2) / Section 58(5) deem all sections-30-to-38 deductions "
        "already given effect to within the presumptive figure, with no carve-out for partner remuneration "
        "(unlike Section 44AE/Sl. No. 2's explicit proviso). See ADR-014, Persona E in docs/personas.md.",
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
    final_taxable_business_income: Decimal | None = Field(
        default=None,
        description="Equal to presumptive_income whenever qualifies_for_presumptive_scheme is True -- named "
        "separately (rather than just reusing presumptive_income) to make explicit that this IS the final figure, "
        "not a floor that ordinary Chapter IV-D deductions -- including partner remuneration -- can still reduce. "
        "See partner_remuneration_note and ADR-014.",
    )
    partner_remuneration_note: str | None = Field(
        default=None,
        description="Set only when entity_type is PARTNERSHIP_FIRM and partner_remuneration_authorized was "
        "provided -- states that the authorized amount is NOT deducted from final_taxable_business_income, "
        "regardless of what Section 40(b)/35(e)'s own cap would have allowed under normal computation, per "
        "ADR-014.",
    )


class Article15Branch(str, Enum):
    """Which paragraph of Article 15(1), if any, gives the US taxing rights
    over the India-resident's professional income. See
    corpus/treaty/india-us-dtaa/article-15.txt.
    """

    NOT_TRIGGERED = "not_triggered"  # income taxable only in India -- para 1's default rule
    NINETY_DAY = "article_15_1_b_ninety_day"  # para 1(b) -- all-or-nothing, no attribution limitation
    FIXED_BASE = "article_15_1_a_fixed_base"  # para 1(a) -- only the fixed-base-attributable portion


class Article15Input(BaseModel):
    """Facts needed to determine Article 15 exposure for one tax year, on top
    of an already-computed PresumptiveIncomeResult. Matches Persona C's and
    Persona D's fact patterns in docs/personas.md.
    """

    persona_label: str
    presumptive_income: Decimal = Field(
        gt=0,
        description="The India-source professional income already computed by compute_presumptive_income() -- "
        "Article 15 exposure is assessed against this figure, not against raw gross_receipts.",
    )
    gross_receipts: Decimal = Field(
        gt=0,
        description="Same gross_receipts used to produce presumptive_income -- needed as the base of the "
        "fixed-base attribution ratio (see fixed_base_attributable_gross_receipts). Not used at all for the "
        "90-day branch, which is all-or-nothing.",
    )
    us_days_present: int = Field(ge=0, description="Aggregate days physically present in the US in the tax year.")
    has_fixed_base_in_us: bool = Field(
        description="Whether a fixed base is 'regularly available' to the assessee in the US, per Article "
        "15(1)(a). This engine does not itself determine what counts as a fixed base -- the caller resolves that "
        "fact; this field is the resolved answer."
    )
    fixed_base_attributable_gross_receipts: Decimal = Field(
        default=Decimal(0),
        ge=0,
        description="The slice of gross_receipts attributable to work actually routed through the US fixed base "
        "(Persona D: Rs. 15,00,000 of Rs. 40,00,000, one of two client engagements). Ignored if "
        "has_fixed_base_in_us is False or if the 90-day branch triggers instead (see ADR-013 for why "
        "presumptive_income -- a single lump deemed figure -- is pro-rated by this same ratio rather than "
        "decomposed some other way; this is a documented modeling choice, not settled law).",
    )

    @model_validator(mode="after")
    def _attributable_not_more_than_gross(self) -> Article15Input:
        if self.fixed_base_attributable_gross_receipts > self.gross_receipts:
            raise ValueError("fixed_base_attributable_gross_receipts cannot exceed gross_receipts")
        return self


class Article15Result(BaseModel):
    persona_label: str
    branch_triggered: Article15Branch
    india_taxable_income: Decimal = Field(
        description="Always equal to presumptive_income -- Article 15's exception clause only ever ADDS US "
        "taxing rights on top of India's; it never removes India's own right to tax the same income."
    )
    us_taxable_income: Decimal = Field(
        description="0 if branch_triggered is NOT_TRIGGERED. The full presumptive_income if NINETY_DAY (para "
        "1(b) carries no attribution limitation in the treaty text). The pro-rated attributable slice if "
        "FIXED_BASE."
    )
    attribution_ratio: Decimal | None = Field(
        default=None, description="fixed_base_attributable_gross_receipts / gross_receipts -- only set for the "
        "FIXED_BASE branch, kept on the result for audit/citation purposes."
    )
    citation: str


class Article25ReliefResult(BaseModel):
    """Represents, but does not fully compute, Article 25(2)(a) relief.

    Per Persona C's own file in docs/personas.md: the credit is
    min(US tax paid, India tax attributable to the US-taxable income), and
    right now this engine can supply neither half of that cap with a
    verified figure. This result type makes that gap explicit rather than
    inventing a number -- WORKING_PRINCIPLES.md rule 4.
    """

    persona_label: str
    relief_applicable: bool = Field(description="False if us_taxable_income is 0 -- no double taxation to relieve.")
    us_taxable_income: Decimal = Field(description="Carried over from the Article15Result this was computed from.")
    computation_status: str = Field(
        description="'not_applicable' (relief_applicable is False), or 'pending_inputs' -- both cap inputs "
        "(US tax paid, India tax attributable) are unverified, see pending_reason."
    )
    pending_reason: str | None = None
    us_tax_paid: Decimal | None = Field(
        default=None, description="Always None in this increment -- needs 26 U.S.C. Section 871(b)/872 + Form "
        "1040-NR research not yet done (ADR-012)."
    )
    india_tax_attributable: Decimal | None = Field(
        default=None, description="Always None in this increment -- needs India's progressive slab-rate "
        "computation, separate not-yet-started Phase 1 work."
    )
    credit_amount: Decimal | None = Field(
        default=None, description="Always None in this increment -- cannot be computed until both cap inputs "
        "above are available."
    )
    citation: str
