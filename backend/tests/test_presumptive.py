"""Unit tests for the Section 44ADA / Section 58 (Sl. No. 3) presumptive
income computation (app.tax_engine.presumptive).

Covers Personas A, B1, B2, and G from docs/personas.md exactly, plus the
boundary cases docs/personas.md's "Still open" section flagged as not yet
built as standalone test cases (gross receipts exactly at the Rs. 50,00,000
/ Rs. 75,00,000 thresholds, and the cash-receipts proviso's own <=5%
boundary), plus the eligibility-gate exclusions (LLP, non-resident,
non-specified-profession) that the statute text states but no persona
individually isolates.

Per WORKING_PRINCIPLES.md rule 4: this suite is what makes the computation
logic mergeable, not a formality -- every assertion below traces to a
specific figure in docs/personas.md or a specific clause in the cited
corpus document, not to what "seems right".
"""
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.tax_engine.models import EntityType, LegalInstrument, PresumptiveIncomeInput
from app.tax_engine.presumptive import (
    compute_presumptive_income,
    select_legal_instrument,
)


def _eligible_individual(**overrides) -> PresumptiveIncomeInput:
    """Shared defaults for an eligible individual, India-resident, specified
    profession -- every persona below is this plus receipts/cash overrides.
    """
    base = {
        "persona_label": "test",
        "tax_year": "2025-26",
        "is_specified_profession": True,
        "entity_type": EntityType.INDIVIDUAL,
        "resident_in_india": True,
        "gross_receipts": Decimal(1),
        "cash_receipts": Decimal(0),
    }
    base.update(overrides)
    return PresumptiveIncomeInput(**base)


# --- Persona A -- Anika: clean baseline, India-only ---------------------

def test_persona_a_anika():
    result = compute_presumptive_income(
        _eligible_individual(
            persona_label="A -- Anika",
            tax_year="2025-26",
            gross_receipts=Decimal(3200000),
            cash_receipts=Decimal(0),
        )
    )
    assert result.legal_instrument is LegalInstrument.IT_ACT_1961
    assert result.eligible is True
    assert result.qualifies_for_presumptive_scheme is True
    assert result.presumptive_income == Decimal(1600000)
    assert result.threshold_applied == Decimal(7500000)  # 0% cash -> proviso applies
    assert result.cash_proviso_applied is True


# --- Persona B -- Rohan: the 44ADA cash-threshold boundary ---------------

def test_persona_b1_rohan_cash_within_5pct_qualifies_at_raised_threshold():
    result = compute_presumptive_income(
        _eligible_individual(
            persona_label="B1 -- Rohan",
            tax_year="2025-26",
            gross_receipts=Decimal(6800000),
            cash_receipts=Decimal(200000),  # 2.94%
        )
    )
    assert result.cash_proviso_applied is True
    assert result.threshold_applied == Decimal(7500000)
    assert result.qualifies_for_presumptive_scheme is True
    assert result.presumptive_income == Decimal(3400000)


def test_persona_b2_rohan_cash_above_5pct_disqualified_at_base_threshold():
    result = compute_presumptive_income(
        _eligible_individual(
            persona_label="B2 -- Rohan",
            tax_year="2025-26",
            gross_receipts=Decimal(6800000),
            cash_receipts=Decimal(400000),  # 5.88%
        )
    )
    assert result.cash_proviso_applied is False
    assert result.threshold_applied == Decimal(5000000)
    assert result.qualifies_for_presumptive_scheme is False
    assert result.presumptive_income is None


# --- Persona G -- Nikhil: clean baseline under the Income-tax Act, 2025 --

def test_persona_g_nikhil_matches_persona_a_across_the_act_boundary():
    result = compute_presumptive_income(
        _eligible_individual(
            persona_label="G -- Nikhil",
            tax_year="2026-27",
            gross_receipts=Decimal(3200000),
            cash_receipts=Decimal(0),
        )
    )
    assert result.legal_instrument is LegalInstrument.IT_ACT_2025
    assert result.qualifies_for_presumptive_scheme is True
    assert result.presumptive_income == Decimal(1600000)  # identical to Persona A -- the regression check itself


# --- Act-selection boundary (ADR-016) ------------------------------------

@pytest.mark.parametrize(
    "tax_year,expected",
    [
        ("2023-24", LegalInstrument.IT_ACT_1961),
        ("2025-26", LegalInstrument.IT_ACT_1961),
        ("2026-27", LegalInstrument.IT_ACT_2025),
        ("2030-31", LegalInstrument.IT_ACT_2025),
    ],
)
def test_legal_instrument_selection_boundary(tax_year, expected):
    assert select_legal_instrument(tax_year) is expected


# --- Threshold boundary cases (statute says "does not exceed" -- <=, not <) --

def test_base_threshold_exactly_50l_with_cash_above_5pct_qualifies():
    # cash 6% -> proviso does NOT apply -> base Rs. 50,00,000 threshold governs
    result = compute_presumptive_income(
        _eligible_individual(gross_receipts=Decimal(5000000), cash_receipts=Decimal(300000))
    )
    assert result.cash_proviso_applied is False
    assert result.threshold_applied == Decimal(5000000)
    assert result.qualifies_for_presumptive_scheme is True
    assert result.presumptive_income == Decimal(2500000)


def test_base_threshold_one_rupee_above_50l_with_cash_above_5pct_disqualifies():
    result = compute_presumptive_income(
        _eligible_individual(gross_receipts=Decimal(5000001), cash_receipts=Decimal(300000))
    )
    assert result.cash_proviso_applied is False
    assert result.qualifies_for_presumptive_scheme is False


def test_raised_threshold_exactly_75l_with_cash_at_5pct_qualifies():
    # cash exactly 5% of 75,00,000 = 3,75,000 -- proviso is "<=5%", inclusive
    result = compute_presumptive_income(
        _eligible_individual(gross_receipts=Decimal(7500000), cash_receipts=Decimal(375000))
    )
    assert result.cash_proviso_applied is True
    assert result.threshold_applied == Decimal(7500000)
    assert result.qualifies_for_presumptive_scheme is True
    assert result.presumptive_income == Decimal(3750000)


def test_raised_threshold_one_rupee_above_75l_disqualifies_even_with_proviso():
    result = compute_presumptive_income(
        _eligible_individual(gross_receipts=Decimal(7500001), cash_receipts=Decimal(300000))
    )
    assert result.cash_proviso_applied is True  # well under 5%
    assert result.threshold_applied == Decimal(7500000)
    assert result.qualifies_for_presumptive_scheme is False


def test_cash_proviso_boundary_exactly_5pct_applies():
    # 2,00,000 / 40,00,000 = exactly 5% -- proviso is "<=5%", inclusive
    result = compute_presumptive_income(
        _eligible_individual(gross_receipts=Decimal(4000000), cash_receipts=Decimal(200000))
    )
    assert result.cash_proviso_applied is True
    assert result.threshold_applied == Decimal(7500000)


def test_cash_proviso_boundary_just_above_5pct_does_not_apply():
    result = compute_presumptive_income(
        _eligible_individual(gross_receipts=Decimal(4000000), cash_receipts=Decimal(200001))
    )
    assert result.cash_proviso_applied is False
    assert result.threshold_applied == Decimal(5000000)
    # still qualifies at the lower threshold -- this case isolates the proviso
    # boundary from the qualification outcome, which the persona-level tests don't
    assert result.qualifies_for_presumptive_scheme is True


# --- Eligibility gate: LLP / non-resident / non-specified-profession -----

def test_llp_is_ineligible_regardless_of_receipts():
    result = compute_presumptive_income(
        _eligible_individual(entity_type=EntityType.LLP, gross_receipts=Decimal(1000000))
    )
    assert result.eligible is False
    assert "limited liability partnership" in result.ineligibility_reason
    assert result.qualifies_for_presumptive_scheme is None
    assert result.presumptive_income is None


def test_non_resident_is_ineligible():
    result = compute_presumptive_income(
        _eligible_individual(resident_in_india=False, gross_receipts=Decimal(1000000))
    )
    assert result.eligible is False
    assert "resident in India" in result.ineligibility_reason


def test_persona_f_karan_routed_to_general_business_scheme():
    # Karan (digital marketing consultant) is not on the specified-profession
    # list, but isn't excluded from the general-business scheme either -- so
    # this must NOT be a flat rejection, and must NOT use 44ADA's 50% rate.
    # All receipts via bank transfer -> pure 6% banking rate.
    result = compute_presumptive_income(
        _eligible_individual(
            persona_label="F -- Karan",
            is_specified_profession=False,
            gross_receipts=Decimal(2800000),
            cash_receipts=Decimal(0),
        )
    )
    assert result.eligible is True
    assert result.routed_to_general_business is True
    assert result.routing_note is not None
    assert result.qualifies_for_presumptive_scheme is True
    assert result.presumptive_income == Decimal(168000)  # 6% x 28,00,000 -- NOT 44ADA's 50% (14,00,000)
    assert result.final_taxable_business_income == Decimal(168000)
    assert result.legal_instrument in (
        LegalInstrument.IT_ACT_1961_GENERAL_BUSINESS,
        LegalInstrument.IT_ACT_2025_GENERAL_BUSINESS,
    )


def test_general_business_blended_rate_mixed_cash_and_banking_receipts():
    # Rs. 20,00,000 total: Rs. 15,00,000 banking (6%) + Rs. 5,00,000 cash (8%).
    result = compute_presumptive_income(
        _eligible_individual(
            is_specified_profession=False,
            gross_receipts=Decimal(2000000),
            cash_receipts=Decimal(500000),
        )
    )
    assert result.routed_to_general_business is True
    # 15,00,000 x 0.06 = 90,000; 5,00,000 x 0.08 = 40,000; total 1,30,000.
    assert result.presumptive_income == Decimal(130000)


def test_unspecified_profession_with_commission_income_is_genuinely_ineligible():
    result = compute_presumptive_income(
        _eligible_individual(
            is_specified_profession=False,
            earns_commission_or_brokerage=True,
            gross_receipts=Decimal(2800000),
        )
    )
    assert result.eligible is False
    assert result.routed_to_general_business is False
    assert "commission/brokerage" in result.ineligibility_reason


def test_unspecified_profession_with_agency_business_is_genuinely_ineligible():
    result = compute_presumptive_income(
        _eligible_individual(
            is_specified_profession=False,
            carries_on_agency_business=True,
            gross_receipts=Decimal(2800000),
        )
    )
    assert result.eligible is False
    assert result.routed_to_general_business is False
    assert "agency business" in result.ineligibility_reason


def test_general_business_threshold_two_crore_boundary():
    # Exactly Rs. 2,00,00,000 with cash above 5% -- base threshold, still qualifies.
    result = compute_presumptive_income(
        _eligible_individual(
            is_specified_profession=False,
            gross_receipts=Decimal(20000000),
            cash_receipts=Decimal(2000000),  # 10% -- above the 5% proviso limit
        )
    )
    assert result.cash_proviso_applied is False
    assert result.threshold_applied == Decimal(20000000)
    assert result.qualifies_for_presumptive_scheme is True


def test_general_business_threshold_one_rupee_above_two_crore_disqualifies():
    result = compute_presumptive_income(
        _eligible_individual(
            is_specified_profession=False,
            gross_receipts=Decimal(20000001),
            cash_receipts=Decimal(2000000),
        )
    )
    assert result.qualifies_for_presumptive_scheme is False
    assert result.presumptive_income is None


def test_persona_e_sharma_associates_firm_remuneration_not_deducted():
    # The remuneration figure used (Rs. 20,00,000) is deliberately one that
    # WOULD pass Section 40(b)'s own cap under normal computation -- this is
    # the sharpest test that final_taxable_business_income is the presumptive
    # figure, full stop, not a floor a wrong implementation could still chip
    # away at (see docs/personas.md, Persona E).
    result = compute_presumptive_income(
        _eligible_individual(
            persona_label="E -- Sharma & Associates",
            entity_type=EntityType.PARTNERSHIP_FIRM,
            gross_receipts=Decimal(4200000),
            cash_receipts=Decimal(0),
            partner_remuneration_authorized=Decimal(2000000),
        )
    )
    assert result.eligible is True
    assert result.qualifies_for_presumptive_scheme is True
    assert result.presumptive_income == Decimal(2100000)
    assert result.final_taxable_business_income == Decimal(2100000)  # NOT 21,00,000 - 20,00,000
    assert result.partner_remuneration_note is not None
    assert "ADR-014" in result.partner_remuneration_note


def test_partner_remuneration_note_absent_when_not_a_firm():
    # An individual has no partners -- the note shouldn't appear even if the
    # field were somehow set, and it's simply never set for a non-firm.
    result = compute_presumptive_income(_eligible_individual(gross_receipts=Decimal(3200000)))
    assert result.partner_remuneration_note is None
    assert result.final_taxable_business_income == result.presumptive_income


def test_partnership_firm_is_eligible_entity_type():
    # Persona E's entity type (though Persona E's own partner-remuneration
    # question is a separate, not-yet-built increment) -- confirms firms
    # aren't excluded outright, only LLPs are.
    result = compute_presumptive_income(
        _eligible_individual(entity_type=EntityType.PARTNERSHIP_FIRM, gross_receipts=Decimal(4200000))
    )
    assert result.eligible is True
    assert result.qualifies_for_presumptive_scheme is True
    assert result.presumptive_income == Decimal(2100000)


# --- Model-level validation ------------------------------------------------

def test_cash_receipts_cannot_exceed_gross_receipts():
    with pytest.raises(ValidationError):
        _eligible_individual(gross_receipts=Decimal(1000000), cash_receipts=Decimal(1000001))


def test_claimed_actual_profit_used_when_higher_than_deemed_figure():
    result = compute_presumptive_income(
        _eligible_individual(
            gross_receipts=Decimal(3200000),
            cash_receipts=Decimal(0),
            claimed_actual_profit=Decimal(2000000),  # higher than the deemed 16,00,000
        )
    )
    assert result.presumptive_income == Decimal(2000000)
