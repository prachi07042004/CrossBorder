# Hand-verified persona scenarios

Ground-truth test personas for Phase 1 (the deterministic tax engine). Each persona's expected output is worked by hand against the primary-source text in `corpus/`, per `WORKING_PRINCIPLES.md` rule 3 -- not against a summary or a guessed formula. Where a number depends on something we haven't verified yet, that gap is stated explicitly rather than filled in with an invented figure.

Currency: INR unless noted. FY2025-26 (AY 2026-27) is the assumed tax year for all six personas below -- the corpus's 44ADA text is confirmed current through this year (see `corpus/india/it-act-section-44ada/2025-26.txt`). **This is a prior-year snapshot, not the project's default going forward**: the current tax year is governed by the Income-tax Act, 2025 (see ADR-016 in `DECISIONS.md`), and any new persona added from here on should default to that Act unless it specifically needs to test 1961-Act-era behavior (e.g. a return being filed for FY2025-26).

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
- **Residency sanity check** (`corpus/india/it-act-section-6/2025-26.txt`): her 110 US days still leaves ~255 days in India, clearing Section 6(1)(a)'s 182-day threshold comfortably on its own -- her premise of being an Indian resident despite the US days isn't self-contradictory. This is a one-time hand-check, not a built capability: this project treats residential status as a given input, not something it computes (ADR-017).
- **Article 25 relief** (`corpus/treaty/india-us-dtaa/article-25.txt`, para 2(a)): India credits the US tax paid on the US-taxable income, capped at `min(US tax paid, India tax attributable to that income)`. The domestic machinery that actually operationalizes this: Section 90 (`corpus/india/it-act-section-90/2025-26.txt`) gives the treaty legal effect, and Rule 128 (`corpus/india/it-rules-rule-128/2025-26.txt`) sets the procedure -- Meera must file Form No. 67 (a statement of her US income and US tax paid, verified) on or before the end of the assessment year, with her return itself filed within the section 139(1)/(4) time limits. Missing that filing is a real, citable reason the credit could be denied even if the arithmetic is right.

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

## Persona E -- Sharma & Associates: partnership firm, partner remuneration under 44ADA

Accountancy partnership firm (two working partners), India resident, all work for India-based clients (deliberately no US presence, to isolate this from every treaty question already covered by C/D).

- FY2025-26 gross receipts: Rs. 42,00,000. **44ADA**: Rs. 42,00,000 <= Rs. 50,00,000 base threshold -- qualifies. Presumptive income = 50% x Rs. 42,00,000 = **Rs. 21,00,000**.
- The partnership deed authorises Rs. 10,00,000 remuneration to each of the two working partners (Rs. 20,00,000 total) -- a figure that, if it were being computed against normal book-profit, would comfortably fit within Section 40(b)'s cap (first Rs. 6,00,000 of book-profit at 90%/Rs. 3,00,000 whichever more, balance at 60% -- see `corpus/india/it-act-section-40b/2025-26.txt`). That's deliberate: this persona isn't testing whether the remuneration figure itself is too high, it's testing whether the deduction is available *at all* once the firm is on 44ADA.
- **Resolution** (see `corpus/india/it-act-section-40b/2025-26.txt`'s `key_finding_for_persona_e`, and ADR-014 in `DECISIONS.md`): it is not. Section 44ADA(2) deems all sections-30-to-38 deductions "already given full effect to" within the presumptive figure, with no proviso carving out partner remuneration -- unlike Section 44AE (goods carriage), which has exactly that proviso referencing Section 40(b). The presence of the carve-out in one presumptive scheme and its absence from 44AD and 44ADA is textual evidence, not silence to read either way.
- **Firm's taxable business income: Rs. 21,00,000, full stop** -- the Rs. 20,00,000 partner remuneration is not separately deducted on top of that, regardless of what the deed authorises or what Section 40(b)'s cap would have allowed under normal computation.

What this tests: that the engine doesn't treat 44ADA's presumptive figure as merely a floor which ordinary Chapter IV-D deductions can still chip away at -- it's the final figure. This is the sharpest possible test of that, because the remuneration amount used is one that *would* pass Section 40(b)'s own cap, so a wrong implementation that applies 40(b) after 44ADA would produce a wrong, lower taxable figure that still looks internally consistent.

---

## Persona F -- Karan: profession not on the 44AA(1) list

Digital marketing consultant, India resident, works with a US client (remotely, no US days, no fixed base -- again isolated from the treaty questions already covered).

- FY2025-26 gross receipts: Rs. 28,00,000, received entirely via bank transfer (no cash).
- **44AA(1) / 44ADA eligibility check** (`corpus/india/it-act-section-44aa/2025-26.txt`): the named list is legal, medical, engineering, architectural, accountancy, technical consultancy, interior decoration, or Board-notified. "Digital marketing consultancy" isn't on it, and no CBDT notification adding it has been checked in this project (flagged, not resolved). **44ADA does not apply to Karan.**
- **This is not simply "no presumptive scheme available," though** -- Section 44AD(6) (`corpus/india/it-act-section-44ad/2025-26.txt`, curated and confirmed 2026-09-20) excludes only "(i) a person carrying on profession as referred to in sub-section (1) of section 44AA; (ii) a person earning income in the nature of commission or brokerage; or (iii) a person carrying on any agency business" from the *general-business* presumptive scheme. Since digital marketing consultancy isn't on the 44AA(1) list, and Karan's work is neither commission/brokerage nor agency business, none of (i)-(iii) excludes him. Read straight, that means Karan can likely still use **Section 44AD's** general-business presumptive scheme instead of 44ADA's -- and this reading is now grounded in the actual sub-section (6) text, not a recollection of it.
- If so: 6% of turnover (all received via bank transfer) = 6% x Rs. 28,00,000 = **Rs. 1,68,000** presumptive business income -- a completely different figure from what 44ADA's 50% rate would have produced (Rs. 14,00,000), had it (wrongly) been applied.

**Open item, stated explicitly rather than resolved:** this "falls through to 44AD instead" reading is now a direct textual reading of 44AD(6) (verbatim, primary-source confirmed), not an inference from memory as it was when this persona was first written -- but it still hasn't been checked against case law, a CBDT circular, or whether "digital marketing consultancy" might itself be swept in by a Board notification under 44AA(1) (the CBDT's separately-notified-professions list has not been curated in this project). Treat the Rs. 1,68,000 figure as illustrative of *why misclassification matters* (a 50%-rate scheme vs. an 8x-lower 6%-rate scheme is a massive difference), not as a settled answer.

What this tests: the "reject a false premise" path from the Phase 5 eval plan, but sharpened -- the correct behavior isn't a flat rejection, it's routing to a *different* rule entirely, which is a much easier place for an implementation to go quietly wrong than an outright error.

---

## Summary

| Persona | Gross receipts | 44ADA outcome | Article 15 branch | Notes |
|---|---|---|---|---|
| A -- Anika | Rs. 32,00,000 | Qualifies, Rs. 16,00,000 | Neither triggers | Clean baseline |
| B1 -- Rohan | Rs. 68,00,000, 2.94% cash | Qualifies (75L proviso), Rs. 34,00,000 | Neither triggers | Cash-threshold boundary, qualifying side |
| B2 -- Rohan | Rs. 68,00,000, 5.88% cash | Does NOT qualify -- normal provisions + possible audit | Neither triggers | Cash-threshold boundary, disqualifying side |
| C -- Meera | Rs. 45,00,000, 110 US days | Qualifies, Rs. 22,50,000 | 15(1)(b) -- 90-day, all-or-nothing | Article 25 credit mechanism defined; final rupee figure pending India slab calculator |
| D -- Devika | Rs. 40,00,000, 45 US days, fixed base | Qualifies, Rs. 20,00,000 | 15(1)(a) -- fixed base, apportioned | Apportionment is a documented modeling choice, not a verified rule |
| E -- Sharma & Assoc. | Rs. 42,00,000, partnership firm | Qualifies, Rs. 21,00,000 (no further deduction) | N/A (no US presence) | Partner remuneration not separately deductible on top of 44ADA -- ADR-014 |
| F -- Karan | Rs. 28,00,000, digital marketing | 44ADA does NOT apply (profession not listed) -- likely 44AD instead, Rs. 1,68,000 | N/A (no US presence) | False-premise/misrouting test, not resolved to case-law certainty |

## Still open (not blocking, tracked for later)

- **No persona yet exercises the Income-tax Act, 2025** (Section 58, effective FY2026-27 onward -- see `corpus/india/it-act-2025-section-58/2026-27.txt`). All six personas above are dated FY2025-26 under the 1961 Act. Given the corpus now has full Section 58/35(e)/62 coverage, a parallel FY2026-27 persona (most usefully, a Section-58-Sl.-No.-3 equivalent of Persona A) is the natural next addition.
- **No persona tests entity/residency-based false-premise rejection.** 44ADA explicitly excludes LLPs ("a partnership firm other than a limited liability partnership") and non-residents ("who is a resident in India") -- neither exclusion is exercised by any current persona. Persona F tests profession-based misrouting; an LLP or non-resident case would test a different rejection path.
- **No persona exercises 44ADA(4)'s audit-trigger branch** -- every current persona accepts the deemed 50% presumptive figure; none claims a lower actual profit (which, combined with total income exceeding the exemption limit, requires books of account and a Section 44AB audit).
- Exact boundary-value personas (gross receipts exactly Rs. 50,00,000 or Rs. 75,00,000; exactly 90 days present) are covered by the boundary notes above but not as standalone test cases.
- Persona C's final India-side credit figure remains pending India's progressive tax-slab computation (Phase 1, not yet built).
- **The four Income-tax Act, 2025 corpus files (Section 58, 35(e), 62, 159) have an unresolved verification-method question**, same shape as Rule 128's (now-resolved) one: all four claim "direct visual page-read" from a source PDF whose file size was never recorded, dated the same day as three files that turned out to have been pdftotext-only. Blocked on re-obtaining `Income_Tax_Act_2025_as_amended_by_FA_Act_2026.pdf` to check.
- CBDT's separately-notified-professions list beyond Section 44AA(1)/Section 62(4)'s named list has not been checked -- relevant to Persona F's certainty (whether digital marketing consultancy could be added by notification) and, in principle, to any profession not on the named list.

### Resolved since the previous version of this file
- **Persona F's core citation (Section 44AD(6)'s exclusion list) is now actually curated and primary-source confirmed** (`corpus/india/it-act-section-44ad/2025-26.txt`) -- previously the conclusion rested on a recalled paraphrase of the subsection, never verified against the Act text the way every other persona's claims were. No discrepancy found; the conclusion is unchanged, but it's now evidenced rather than asserted.
- **Rule 128's verification-method ambiguity is resolved.** The 2026-09-20 review noted that Rule 128's source PDF (~104MB) is over the page-image tool's 100MB limit, the same condition that caused three other files' "direct visual page-read" claims to be overstated -- but Rule 128's header didn't say whether the qpdf-split workaround had actually been used. It has now been explicitly re-confirmed via qpdf-split page image read; word-for-word match, no discrepancy.
- Section 44AA(1)'s notified-professions list is now verified to primary-source rigor (cross-checked against two independent sources, see `corpus/india/it-act-section-44aa/2025-26.txt`) -- no discrepancy found.
- Partnership-firm eligibility under 44ADA is now tested (Persona E), including the partner-remuneration interaction question.
- An earlier working note (during this session, before the comprehensive 1961 Act PDF was available) flagged the Income-tax Act 2025's Section 58(5) -- which ties the partner-remuneration carve-out to "Table: Sl. No. 2" (goods carriage) only -- as a possible drafting anomaly. Direct comparison against the current 1961 Act's Section 44AD/44AE/44ADA showed this is not an anomaly: the 2025 Act faithfully carries forward the same asymmetry already present in the 1961 Act. That earlier flag is retracted.
- Residential status (Section 6) was flagged as silently assumed. Resolution: it's now an explicit, documented out-of-scope input for v1 (FR-15, ADR-017), not a silent gap -- and Persona C's specific premise (110 US days, still an Indian resident) was hand-checked against the actual Section 6 text and holds. Full residency-determination logic is deliberately not built.
- Form 67 / Rule 128 is now curated (`corpus/india/it-rules-rule-128/2025-26.txt`), closing the gap that blocked fully grounding Persona C's Article 25 credit claim. Caught in the process: this isn't just a rule-number renumbering under the 2025 Act (Rule 128 -> Rule 76, `corpus/india/it-rules-2026-rule-76/2026-27.txt`) -- the **form number itself changes, Form No. 67 -> Form No. 44** -- the same category of trap as the Section 58 numbering collision already documented in `corpus/README.md`. Also caught: the filing deadline's wording changed ("end of the assessment year" -> "within twelve months from the end of the tax year"), not confirmed equivalent, flagged rather than assumed.
