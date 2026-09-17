# Hand-verified persona scenarios

Ground-truth test personas for Phase 1 (the deterministic tax engine). Each persona's expected output is worked by hand against the primary-source text in `corpus/`, per `WORKING_PRINCIPLES.md` rule 3 -- not against a summary or a guessed formula. Where a number depends on something we haven't verified yet, that gap is stated explicitly rather than filled in with an invented figure.

Currency: INR unless noted. FY2025-26 (AY 2026-27) is the assumed tax year for all personas -- the corpus's 44ADA text is confirmed current through this year (see `corpus/india/it-act-section-44ada/2025-26.txt`).

Each persona is designed to isolate one specific rule boundary, not to be a "realistic" composite -- that's deliberate, so a wrong answer points at exactly one piece of logic.

---

## Persona A -- Anika: clean baseline, India-only

IT/technical consultant, India resident, serves a US client entirely remotely.

- FY2025-26 gross receipts: Rs. 32,00,000. Zero days physically present in the US. No US fixed base.
- **44ADA** (`corpus/india/it-act-section-44ada/2025-26.txt`): Rs. 32,00,000 <= Rs. 50,00,000 base threshold -- qualifies without even needing the Rs. 75,00,000 cash proviso. Presumptive income = 50% x Rs. 32,00,000 = **Rs. 16,00,000**.
- **DTAA Article 15** (`corpus/treaty/india-us-dtaa/article-15.txt`): no fixed base, 0 days present -- neither exception in para 1 is met, so the income is taxable only in India (the first-mentioned State).
- **Article 25 relief**: not applicable -- no US tax paid.

What this tests: the base case, with no treaty complications at all. If this one comes out wrong, the bug is in 44ADA itself, not in any interaction.

---

## Persona B -- Rohan: the 44ADA cash-threshold boundary

Engineering consultant, India resident. Same gross receipts, two cash-mix variants, to isolate the proviso logic from the threshold logic.

FY2025-26 gross receipts (both variants): Rs. 68,00,000. Zero days in the US, no fixed base (deliberately, so nothing from Article 15 leaks into this persona).

**B1 -- cash receipts Rs. 2,00,000** (2.94% of total, <= 5%):
First proviso applies -> effective threshold becomes Rs. 75,00,000 -> Rs. 68,00,000 qualifies. Presumptive income = 50% x Rs. 68,00,000 = **Rs. 34,00,000**.

**B2 -- cash receipts Rs. 4,00,000** (5.88% of total, > 5%):
First proviso does NOT apply -> threshold stays Rs. 50,00,000 -> Rs. 68,00,000 exceeds it. **44ADA does not apply this year.** Falls to normal-provisions computation of actual profit; if declared profit is lower than the deemed 50% figure and total income exceeds the basic exemption limit, sub-section (4)'s audit requirement (section 44AB) applies.

What this tests: that the engine checks the cash-percentage condition *before* comparing gross receipts to a threshold, not the other way around -- B1 and B2 have identical gross receipts and differ only in cash mix, so a threshold-first implementation would get one of them wrong.

Boundary note for whoever writes the comparison logic: the statute says "does not exceed," so a value exactly equal to the threshold (Rs. 50,00,000 or Rs. 75,00,000) still qualifies -- use `<=`, not `<`.

---

## Persona C -- Meera: crosses the DTAA 90-day line (Article 15(1)(b))

Management consultant, India resident, works with a US client.

- FY2025-26 gross receipts: Rs. 45,00,000 (kept under the Rs. 50,00,000 44ADA threshold on purpose, to isolate the treaty question from the 44ADA threshold question).
- 110 aggregate days physically present in the US this tax year (client site work). No fixed base.
- **44ADA**: Rs. 45,00,000 <= Rs. 50,00,000 -- presumptive income = 50% x Rs. 45,00,000 = **Rs. 22,50,000**. This computation is unaffected by her US days; 44ADA has no awareness of the treaty.
- **DTAA Article 15**: 110 days >= 90 -- triggers para 1(b). Unlike the fixed-base branch (a), branch (b) carries no "only the attributable portion" limitation in the treaty text -- once triggered, the full professional-service income becomes taxable in the US as well as India, not an apportioned slice.
- **26 U.S.C. Section 861(a)(3) check** (`corpus/us/irs-source-of-income/26-usc-861-a-3.txt`), for contrast: she fails this domestic-law exception on both counts -- 110 days > 90, and her income is far above the $3,000 cap -- confirming this is a treaty-Article-15 case, not a case the domestic sourcing exception would rescue. This is exactly the distinction flagged in that corpus file's metadata.
- **Article 25 relief** (`corpus/treaty/india-us-dtaa/article-25.txt`, para 2(a)): India credits the US tax paid on the US-taxable income, capped at `min(US tax paid, India tax attributable to that income)`.

**Open item -- not fully computed, by design:** The India-tax half of that cap needs India's progressive income-tax slab computation, which is not built yet (Phase 1 work, not yet started). Rather than hand-compute slabs that haven't been verified, this persona states the *mechanism* and leaves the final India-side credit figure as pending.

**Assumption used for the US-side figure (explicitly a simplification, not IRC-verified law):** assume a flat 30% effective US federal rate on the Rs. 22,50,000 US-taxable presumptive income, at an assumed rate of Rs. 83 = $1 -> approx. $27,108 of US-taxable income -> approx. **$8,132 of US tax** (approx. Rs. 6,75,000). This is a placeholder for testing the *credit mechanism*, not a researched figure -- actual US taxation of a nonresident alien's effectively-connected income runs through 26 U.S.C. Section 871(b)/872 and Form 1040-NR (graduated rates on net income after allowable deductions), none of which has been verified in this project. See ADR-012 in `DECISIONS.md`.

What this tests: the all-or-nothing 90-day trigger, and that the engine doesn't confuse the treaty's 90-day rule with Section 861(a)(3)'s differently-shaped 90-day rule.

---

## Persona D -- Devika: the fixed-base branch (Article 15(1)(a))

Architectural consultant, India resident.

- FY2025-26 gross receipts: Rs. 40,00,000 (kept under the 44ADA threshold, same isolation approach as Persona C). Presumptive income = 50% x Rs. 40,00,000 = **Rs. 20,00,000**.
- Maintains a serviced office / co-working desk in the US year-round for client meetings -- this is a "fixed base regularly available to him" under Article 15(1)(a). Total days physically present in the US: 45 -- well under 90, so branch (b) never triggers. This isolates the fixed-base test from the day-count test; a fixed base can pull in US taxing rights on far fewer than 90 days, since availability, not days, is what matters for this branch.
- Two engagements make up her gross receipts: Client 1, Rs. 15,00,000, work routed through the US fixed base (attributable); Client 2, Rs. 25,00,000, entirely remote from India, no connection to the fixed base (not attributable).
- **DTAA Article 15(1)(a)**: only "so much of the income as is attributable to that fixed base" may be taxed in the US -- i.e. the Rs. 15,00,000 slice, not the full Rs. 40,00,000 (contrast with Persona C, where crossing 90 days pulled in everything).

**Open item -- a modeling choice, not a verified rule:** 44ADA produces one lump deemed figure (Rs. 20,00,000) from total receipts; it doesn't decompose by client or engagement. Neither the statute nor the treaty text says how to reconcile a presumptive-taxation regime with a treaty attribution requirement -- there's no worked example in either primary source. The approach used here: pro-rate the presumptive income by the same ratio as the underlying gross receipts (Rs. 15,00,000 / Rs. 40,00,000 = 37.5% -> 37.5% x Rs. 20,00,000 = **Rs. 7,50,000 treated as US-attributable presumptive income**). This is a documented design decision, not settled law -- see ADR-013 in `DECISIONS.md`. A different, equally defensible approach could be argued; if this ever matters for a real filing rather than a class project, it would need a second opinion, not just this engine's output.

What this tests: apportionment logic (a genuinely different computation from Persona C's all-or-nothing trigger), and that the engine doesn't conflate "fixed base available" with "90+ days present" as the same trigger condition.

---

## Summary

| Persona | Gross receipts | 44ADA outcome | Article 15 branch | Notes |
|---|---|---|---|---|
| A -- Anika | Rs. 32,00,000 | Qualifies, Rs. 16,00,000 | Neither triggers | Clean baseline |
| B1 -- Rohan | Rs. 68,00,000, 2.94% cash | Qualifies (75L proviso), Rs. 34,00,000 | Neither triggers | Cash-threshold boundary, qualifying side |
| B2 -- Rohan | Rs. 68,00,000, 5.88% cash | Does NOT qualify -- normal provisions + possible audit | Neither triggers | Cash-threshold boundary, disqualifying side |
| C -- Meera | Rs. 45,00,000, 110 US days | Qualifies, Rs. 22,50,000 | 15(1)(b) -- 90-day, all-or-nothing | Article 25 credit mechanism defined; final rupee figure pending India slab calculator |
| D -- Devika | Rs. 40,00,000, 45 US days, fixed base | Qualifies, Rs. 20,00,000 | 15(1)(a) -- fixed base, apportioned | Apportionment is a documented modeling choice, not a verified rule |

## Still open (not blocking, tracked for later)

- Section 44AA(1)'s notified-professions list (which the personas' professions rely on) has not itself been verified to primary-source rigor this session -- only 44ADA, which references it, has been.
- Partnership-firm eligibility under 44ADA (the statute covers "an individual or a partnership firm other than a limited liability partnership") is untested -- all four personas are individuals.
- A persona that fails Section 44AA(1)'s eligibility gate entirely (not a notified profession) would exercise the "reject a false premise" path called out in the Phase 5 eval plan -- not yet built.
- Exact boundary-value personas (gross receipts exactly Rs. 50,00,000 or Rs. 75,00,000; exactly 90 days present) are covered by the boundary notes above but not as standalone test cases.
