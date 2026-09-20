"""Tests for DTAA Article 15 exposure and the Article 25 relief mechanism.

Grounded in Personas C and D (docs/personas.md), plus boundary cases for the
90-day test and the fixed-base/90-day precedence rule described in
app/tax_engine/dtaa.py's module docstring. As with test_presumptive.py, the
expected figures below are the personas' own hand-verified numbers, not
values derived from "what seems right" while writing the test.
"""
from decimal import Decimal

from app.tax_engine.dtaa import compute_article_15_exposure, compute_article_25_relief
from app.tax_engine.models import Article15Branch, Article15Input


def _article15_input(**overrides):
    base = {
        "persona_label": "test",
        "presumptive_income": Decimal(1000000),
        "gross_receipts": Decimal(2000000),
        "us_days_present": 0,
        "has_fixed_base_in_us": False,
        "fixed_base_attributable_gross_receipts": Decimal(0),
    }
    base.update(overrides)
    return Article15Input(**base)


def test_persona_c_meera_ninety_day_branch_all_or_nothing():
    result = compute_article_15_exposure(
        _article15_input(
            persona_label="C -- Meera",
            presumptive_income=Decimal(2250000),
            gross_receipts=Decimal(4500000),
            us_days_present=110,
            has_fixed_base_in_us=False,
        )
    )
    assert result.branch_triggered is Article15Branch.NINETY_DAY
    assert result.india_taxable_income == Decimal(2250000)
    assert result.us_taxable_income == Decimal(2250000)  # full amount, no attribution limitation
    assert result.attribution_ratio is None


def test_persona_d_devika_fixed_base_branch_apportioned():
    result = compute_article_15_exposure(
        _article15_input(
            persona_label="D -- Devika",
            presumptive_income=Decimal(2000000),
            gross_receipts=Decimal(4000000),
            us_days_present=45,
            has_fixed_base_in_us=True,
            fixed_base_attributable_gross_receipts=Decimal(1500000),
        )
    )
    assert result.branch_triggered is Article15Branch.FIXED_BASE
    assert result.india_taxable_income == Decimal(2000000)
    assert result.attribution_ratio == Decimal("0.375")  # 15,00,000 / 40,00,000
    assert result.us_taxable_income == Decimal(750000)  # 37.5% x 20,00,000


def test_neither_condition_met_article_15_does_not_apply():
    result = compute_article_15_exposure(
        _article15_input(us_days_present=30, has_fixed_base_in_us=False)
    )
    assert result.branch_triggered is Article15Branch.NOT_TRIGGERED
    assert result.us_taxable_income == Decimal(0)
    # Article 15 never removes India's own taxing right, even when it doesn't add the US's.
    assert result.india_taxable_income == Decimal(1000000)


def test_ninety_day_boundary_exactly_90_triggers():
    # "amounting to or exceeding in the aggregate 90 days" -- inclusive.
    result = compute_article_15_exposure(_article15_input(us_days_present=90))
    assert result.branch_triggered is Article15Branch.NINETY_DAY


def test_ninety_day_boundary_89_days_does_not_trigger_alone():
    result = compute_article_15_exposure(
        _article15_input(us_days_present=89, has_fixed_base_in_us=False)
    )
    assert result.branch_triggered is Article15Branch.NOT_TRIGGERED


def test_fixed_base_present_but_zero_attributable_receipts_does_not_trigger():
    # A fixed base with no work actually routed through it shouldn't expose any income.
    result = compute_article_15_exposure(
        _article15_input(
            us_days_present=10,
            has_fixed_base_in_us=True,
            fixed_base_attributable_gross_receipts=Decimal(0),
        )
    )
    assert result.branch_triggered is Article15Branch.NOT_TRIGGERED
    assert result.us_taxable_income == Decimal(0)


def test_both_conditions_met_ninety_day_takes_precedence_over_fixed_base():
    # 95 days AND a fixed base -- the all-or-nothing 90-day rule governs; the
    # fixed-base attribution ratio never narrows an already-full exposure.
    result = compute_article_15_exposure(
        _article15_input(
            presumptive_income=Decimal(1000000),
            gross_receipts=Decimal(2000000),
            us_days_present=95,
            has_fixed_base_in_us=True,
            fixed_base_attributable_gross_receipts=Decimal(500000),  # would be only 25% under branch (a)
        )
    )
    assert result.branch_triggered is Article15Branch.NINETY_DAY
    assert result.us_taxable_income == Decimal(1000000)  # full amount, not the 25% slice


def test_article_25_not_applicable_when_article_15_not_triggered():
    exposure = compute_article_15_exposure(_article15_input(us_days_present=10, has_fixed_base_in_us=False))
    relief = compute_article_25_relief(exposure)
    assert relief.relief_applicable is False
    assert relief.computation_status == "not_applicable"
    assert relief.us_tax_paid is None
    assert relief.india_tax_attributable is None
    assert relief.credit_amount is None


def test_article_25_pending_inputs_for_persona_c():
    exposure = compute_article_15_exposure(
        _article15_input(
            persona_label="C -- Meera",
            presumptive_income=Decimal(2250000),
            gross_receipts=Decimal(4500000),
            us_days_present=110,
        )
    )
    relief = compute_article_25_relief(exposure)
    assert relief.relief_applicable is True
    assert relief.us_taxable_income == Decimal(2250000)
    assert relief.computation_status == "pending_inputs"
    assert relief.pending_reason is not None
    # The engine must not fabricate a credit figure -- both cap inputs stay None.
    assert relief.us_tax_paid is None
    assert relief.india_tax_attributable is None
    assert relief.credit_amount is None


def test_article_25_pending_inputs_for_persona_d():
    exposure = compute_article_15_exposure(
        _article15_input(
            persona_label="D -- Devika",
            presumptive_income=Decimal(2000000),
            gross_receipts=Decimal(4000000),
            us_days_present=45,
            has_fixed_base_in_us=True,
            fixed_base_attributable_gross_receipts=Decimal(1500000),
        )
    )
    relief = compute_article_25_relief(exposure)
    assert relief.relief_applicable is True
    assert relief.us_taxable_income == Decimal(750000)
    assert relief.computation_status == "pending_inputs"
    assert relief.credit_amount is None


def test_fixed_base_attributable_cannot_exceed_gross_receipts():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        _article15_input(
            gross_receipts=Decimal(1000000),
            has_fixed_base_in_us=True,
            fixed_base_attributable_gross_receipts=Decimal(1000001),
        )
