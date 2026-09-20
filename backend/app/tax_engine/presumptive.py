"""Section 44ADA / Income-tax Act 2025 Section 58 (Table Sl. No. 3) presumptive
income computation, including Persona E's finding: a partnership firm's
presumptive income is the FINAL taxable business income -- partner
remuneration authorised by the deed is never separately deducted on top of
it (ADR-014, corpus/india/it-act-section-40b/2025-26.txt). Fields/results
for this exist alongside the core computation rather than in a separate
module, since it's the exact same presumptive-income figure, just named
explicitly as "final" and paired with a citation note when relevant.

Both provisions are substantively identical for this computation (50% of
gross receipts, Rs. 50,00,000 base threshold / Rs. 75,00,000 where cash
receipts are <=5% of gross receipts, "whichever is higher" against a claimed
actual profit) -- confirmed by Persona A and Persona G producing the same
Rs. 16,00,000 result from identical facts under the two different Acts (see
docs/personas.md). This module therefore has ONE core computation function,
with the two Acts differing only in which legal_instrument/citation gets
attached to the result -- duplicating the arithmetic per Act would risk
exactly the kind of drift between the 1961 Act and 2025 Act text that
ADR-015/016 exist to guard against.

Persona F's finding is also handled here, not in a separate module: when a
profession is NOT on the specified list, that is not automatic
ineligibility -- Section 44AD(6) / Section 58(11)(a) only exclude commission/
brokerage income and agency business from the general-business presumptive
scheme, and neither applies to Persona F's digital-marketing consultancy.
So an unspecified profession routes to Section 44AD / Section 58 Sl. No. 1
(8%/6% blended rate by banking vs. cash receipts, Rs. 2/3 crore threshold --
both entirely different from the specified-profession scheme) instead of
being flatly rejected. True ineligibility (commission/brokerage or agency
business) still produces a flat rejection, just for a different reason.

Primary sources:
- corpus/india/it-act-section-44ada/2025-26.txt (1961 Act, Section 44ADA)
- corpus/india/it-act-2025-section-58/2026-27.txt (2025 Act, Section 58, Table Sl. No. 3)
- corpus/india/it-act-section-44aa/2025-26.txt (1961 Act profession list, Section 44AA(1))
- corpus/india/it-act-2025-section-62/2026-27.txt (2025 Act profession list, Section 62(4))
- corpus/india/it-act-section-44ad/2025-26.txt (1961 Act, Section 44AD, general business)
- corpus/india/it-act-2025-section-58/2026-27.txt, Table Sl. No. 1 (2025 Act, general business)
"""
from __future__ import annotations

from decimal import Decimal

from .models import (
    EntityType,
    LegalInstrument,
    PresumptiveIncomeInput,
    PresumptiveIncomeResult,
)

BASE_THRESHOLD = Decimal(5000000)  # Rs. 50,00,000
RAISED_THRESHOLD = Decimal(7500000)  # Rs. 75,00,000
CASH_PROVISO_LIMIT_PCT = Decimal(5)  # <=5% cash receipts
PRESUMPTIVE_RATE = Decimal("0.50")  # 50%

# General-business scheme (Section 44AD / Section 58 Sl. No. 1) -- entirely
# different numbers from the specified-profession scheme above. Same <=5%
# cash-proviso limit, confirmed identical in both corpus texts.
GENERAL_BUSINESS_BASE_THRESHOLD = Decimal(20000000)  # Rs. 2,00,00,000 (2 crore)
GENERAL_BUSINESS_RAISED_THRESHOLD = Decimal(30000000)  # Rs. 3,00,00,000 (3 crore)
GENERAL_BUSINESS_BANKING_RATE = Decimal("0.06")  # 6% -- portion received via specified banking/online mode
GENERAL_BUSINESS_CASH_RATE = Decimal("0.08")  # 8% -- the rest (cash / non-banking)


def select_legal_instrument(tax_year: str) -> LegalInstrument:
    """Selects 1961 Act Section 44ADA or 2025 Act Section 58 by tax year, per
    ADR-016: the Income-tax Act, 2025 governs FY2026-27 onward; the 1961 Act
    remains applicable for FY2025-26 and earlier. Mirrors
    corpus/METADATA_SCHEMA.md's tax_year_start/tax_year_end boundary exactly
    (44ADA: through 2025-26; Section 58: 2026-27 onward).
    """
    start_year = int(tax_year.split("-")[0])
    if start_year >= 2026:
        return LegalInstrument.IT_ACT_2025
    return LegalInstrument.IT_ACT_1961


def _citation_for(instrument: LegalInstrument) -> str:
    if instrument is LegalInstrument.IT_ACT_2025:
        return "corpus/india/it-act-2025-section-58/2026-27.txt, Table Sl. No. 3"
    return "corpus/india/it-act-section-44ada/2025-26.txt"


def _select_general_business_instrument(tax_year: str) -> LegalInstrument:
    """Same tax-year boundary as select_legal_instrument() -- the two Acts'
    general-business schemes replace each other on the identical FY2026-27
    line as the specified-profession schemes do.
    """
    start_year = int(tax_year.split("-")[0])
    if start_year >= 2026:
        return LegalInstrument.IT_ACT_2025_GENERAL_BUSINESS
    return LegalInstrument.IT_ACT_1961_GENERAL_BUSINESS


def _citation_for_general_business(instrument: LegalInstrument) -> str:
    if instrument is LegalInstrument.IT_ACT_2025_GENERAL_BUSINESS:
        return "corpus/india/it-act-2025-section-58/2026-27.txt, Table Sl. No. 1"
    return "corpus/india/it-act-section-44ad/2025-26.txt"


def _partner_remuneration_note(data: PresumptiveIncomeInput) -> str | None:
    """Shared by both the specified-profession and general-business paths --
    neither 44ADA/Section 58 Sl. No. 3 nor 44AD/Section 58 Sl. No. 1 carve
    out partner remuneration (unlike Sl. No. 2 / Section 44AE); see ADR-014.
    """
    if data.entity_type != EntityType.PARTNERSHIP_FIRM or data.partner_remuneration_authorized is None:
        return None
    return (
        f"Partnership deed authorises Rs. {data.partner_remuneration_authorized} in partner remuneration -- "
        "NOT deducted from final_taxable_business_income. Neither this presumptive scheme nor the general-"
        "business alternative carves out partner remuneration (unlike Section 44AE/Sl. No. 2's explicit "
        "proviso). See ADR-014."
    )


def compute_presumptive_income(data: PresumptiveIncomeInput) -> PresumptiveIncomeResult:
    instrument = select_legal_instrument(data.tax_year)
    citation = _citation_for(instrument)

    # Eligibility gate: profession, entity type, residency. Which professions
    # qualify is NOT decided here -- the caller resolves is_specified_profession
    # against the Section 44AA(1) / Section 62(4) named lists first (see
    # PresumptiveIncomeInput's field description). This function only
    # enforces the gate, matching 44ADA(1)'s "who is a resident in India...
    # engaged in a profession referred to in sub-section (1) of section 44AA"
    # and Section 58(11)(b)'s "specified assessee... who is a resident in
    # India" plus the Table's column B profession reference.
    if data.entity_type == EntityType.LLP:
        return PresumptiveIncomeResult(
            persona_label=data.persona_label,
            legal_instrument=instrument,
            eligible=False,
            ineligibility_reason=(
                "Section 44ADA(1) / Section 58(11)(b) both exclude a limited liability partnership "
                '("a partnership firm other than a limited liability partnership" / "other than a limited '
                'liability partnership") -- an LLP cannot use this scheme regardless of profession or receipts.'
            ),
        )
    if not data.resident_in_india:
        return PresumptiveIncomeResult(
            persona_label=data.persona_label,
            legal_instrument=instrument,
            eligible=False,
            ineligibility_reason="Both provisions require the assessee to be 'a resident in India'.",
        )
    if not data.is_specified_profession:
        # Persona F: NOT automatic ineligibility -- routes to the
        # general-business scheme unless separately excluded from that one
        # too (commission/brokerage, agency business).
        return _compute_general_business_presumptive(data)

    # Cash-receipts proviso computed BEFORE the threshold comparison, not
    # after -- this is the specific thing Persona B1/B2 exists to test (a
    # threshold-first implementation gets one of the two variants wrong
    # despite identical gross receipts).
    cash_pct = (data.cash_receipts / data.gross_receipts) * Decimal(100) if data.gross_receipts else Decimal(0)
    cash_proviso_applied = cash_pct <= CASH_PROVISO_LIMIT_PCT
    threshold = RAISED_THRESHOLD if cash_proviso_applied else BASE_THRESHOLD

    # Statute says "does not exceed" -- boundary-inclusive, <=, not <.
    qualifies = data.gross_receipts <= threshold

    if not qualifies:
        return PresumptiveIncomeResult(
            persona_label=data.persona_label,
            legal_instrument=instrument,
            eligible=True,
            threshold_applied=threshold,
            cash_proviso_applied=cash_proviso_applied,
            qualifies_for_presumptive_scheme=False,
            citation=citation,
        )

    deemed = (data.gross_receipts * PRESUMPTIVE_RATE).quantize(Decimal(1))
    presumptive_income = max(deemed, data.claimed_actual_profit) if data.claimed_actual_profit is not None else deemed

    # Persona E: presumptive_income IS the final taxable business income --
    # not a floor that partner remuneration (or any other Chapter IV-D
    # deduction) can still reduce.
    return PresumptiveIncomeResult(
        persona_label=data.persona_label,
        legal_instrument=instrument,
        eligible=True,
        threshold_applied=threshold,
        cash_proviso_applied=cash_proviso_applied,
        qualifies_for_presumptive_scheme=True,
        presumptive_income=presumptive_income,
        citation=citation,
        final_taxable_business_income=presumptive_income,
        partner_remuneration_note=_partner_remuneration_note(data),
    )


def _compute_general_business_presumptive(data: PresumptiveIncomeInput) -> PresumptiveIncomeResult:
    """Section 44AD / Section 58 Sl. No. 1 -- the fallback for a profession
    that is not on the specified list (Persona F). Called only from
    compute_presumptive_income() when is_specified_profession is False; the
    LLP and residency gates have already been checked by the caller, since
    both schemes share those same two gates.
    """
    instrument = _select_general_business_instrument(data.tax_year)
    citation = _citation_for_general_business(instrument)

    if data.earns_commission_or_brokerage or data.carries_on_agency_business:
        excluded_by = []
        if data.earns_commission_or_brokerage:
            excluded_by.append("commission/brokerage income (Section 44AD(6)(ii) / Section 58(11)(a)(iv))")
        if data.carries_on_agency_business:
            excluded_by.append("agency business (Section 44AD(6)(iii) / Section 58(11)(a)(v))")
        return PresumptiveIncomeResult(
            persona_label=data.persona_label,
            legal_instrument=instrument,
            eligible=False,
            ineligibility_reason=(
                "Not a specified profession (Section 44AA(1) / Section 62(4)), and separately excluded from the "
                f"general-business scheme by: {'; '.join(excluded_by)}. Neither presumptive scheme applies."
            ),
        )

    # Same <=5% cash-proviso limit as the specified-profession scheme,
    # confirmed identical in both corpus texts -- but a completely different
    # threshold (Rs. 2/3 crore, not Rs. 50/75 lakh).
    cash_pct = (data.cash_receipts / data.gross_receipts) * Decimal(100) if data.gross_receipts else Decimal(0)
    cash_proviso_applied = cash_pct <= CASH_PROVISO_LIMIT_PCT
    threshold = GENERAL_BUSINESS_RAISED_THRESHOLD if cash_proviso_applied else GENERAL_BUSINESS_BASE_THRESHOLD

    qualifies = data.gross_receipts <= threshold
    routing_note = (
        "Profession not on the Section 44AA(1) / Section 62(4) specified list -- routed to the general-business "
        "presumptive scheme (Section 44AD / Section 58 Sl. No. 1) instead of a flat rejection, since neither the "
        "commission/brokerage nor agency-business exclusion applies here. Rate and threshold are entirely "
        "different from the specified-profession scheme. See docs/personas.md, Persona F."
    )

    if not qualifies:
        return PresumptiveIncomeResult(
            persona_label=data.persona_label,
            legal_instrument=instrument,
            eligible=True,
            threshold_applied=threshold,
            cash_proviso_applied=cash_proviso_applied,
            qualifies_for_presumptive_scheme=False,
            citation=citation,
            routed_to_general_business=True,
            routing_note=routing_note,
        )

    # Blended rate: the banking/online-received portion at 6%, the rest
    # (cash / non-banking) at 8% -- both provisions state it as this same
    # two-part sum, not a single blended percentage applied to the whole.
    banking_portion = data.gross_receipts - data.cash_receipts
    deemed = (
        banking_portion * GENERAL_BUSINESS_BANKING_RATE + data.cash_receipts * GENERAL_BUSINESS_CASH_RATE
    ).quantize(Decimal(1))
    presumptive_income = max(deemed, data.claimed_actual_profit) if data.claimed_actual_profit is not None else deemed

    return PresumptiveIncomeResult(
        persona_label=data.persona_label,
        legal_instrument=instrument,
        eligible=True,
        threshold_applied=threshold,
        cash_proviso_applied=cash_proviso_applied,
        qualifies_for_presumptive_scheme=True,
        presumptive_income=presumptive_income,
        citation=citation,
        final_taxable_business_income=presumptive_income,
        partner_remuneration_note=_partner_remuneration_note(data),
        routed_to_general_business=True,
        routing_note=routing_note,
    )
