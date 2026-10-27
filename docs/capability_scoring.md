# Capability Snapshot — 24-item indicative maturity rubric (2026)

This specification documents the scoring system used for the EOC-NET Americas fact sheets. It was reconstructed from the **original 2026 reference PDF** and the explanation supplied by the survey team. Its mappings reproduce the five reported pillar scores in **all 15 original reference profiles (75 of 75 pillar values)** when applied to the original survey workbook. Current reports use the subsequent cleaned dataset, so country coverage and reference lines update automatically.

**Not an official PAHO assessment or country ranking.** Survey data are self-reported and no external validation of operational performance has been undertaken. Category assignments—especially "do not know"/"not applicable" responses—should be formally endorsed by the survey team before official release.

## Exact formula

Each of the **24 selected questions** is converted to an integer between **1 (lowest/least developed)** and **5 (highest/most developed)**. All answered items in a pillar carry equal weight. For institution `r` and pillar `d`:

```
mean_1_to_5(r, d) = sum(rating(r, q) for scored questions q in d) / number_of_scored_questions
pillar_score(r, d) = round((mean_1_to_5(r, d) - 1) / 4 * 100)
```

Thus one point on the five-level scale corresponds to 25 points on the 0–100 scale. Only blank/unrecognized answers are excluded from the denominator. **Explicit** selections such as `No sabe`, `No aplica`, and `No está definido` receive a rating of **1** in the reconstructed reference rubric; this reproduces the supplied reference scores, but it is not equivalent to evidence that capacity is absent. Consider a missingness sensitivity analysis before interpreting or comparing entities.

### The five pillars and their original survey items

| Pillar (English label on PDF) | Original question numbers | Count |
|---|---|---:|
| Governance & legal | Q10 legal framework; Q12 legal support to decisions; Q13 inclusion in a national plan; Q14 financing; Q15 formal SOP | 5 |
| Operations & decisions | Q16 activation time; Q20 incident action plan; Q22 strategic committee; Q23 Incident Management System; Q24 risk assessment; Q25 operational/logistical readiness | 6 |
| Human resources | Q28 designated leader; Q30 documented roles; Q32 surge procedure; Q33 trained staff roster; Q34 response-team deployment | 5 |
| Information management | Q38 internal information exchange; Q39 technological tools; Q40 frequency/severity of data gaps; Q41 situation room; Q42 SITREP procedure | 5 |
| Coordination | Q18 intersectoral coordination; Q19 integration with national DRM; Q21 international cooperation | 3 |
| **TOTAL** | | **24** |

The program reads the first Excel sheet by zero-based column index. This table lists **actual answer-choice letters**, not a generic alphabetical ordinal scale. The order and direction differ by question.

### Explicit rating dictionaries

| Survey item | Excel column (zero-based) | Code → 1–5 rating |
|---|---:|---|
| Q10 Legal framework | 29 | a=1, b=2, c=3, d=4, e=5 |
| Q12 Legal support to decisions | 32 | a=1, b=2, c=3, d=4, e=5 |
| Q13 Included in national plan | 33 | a=5, b=1 |
| Q14 Financing | 36 | a=1, b=2, c=3, d=4, e=5 |
| Q15 Formal SOP | 37 | a=5, b=1, c=3 |
| Q16 Activation time | 39 | a=5 (<2h), b=4 (2–6h), c=2 (>6h), d=1 (not defined), e=1 |
| Q20 Incident action plan | 43 | a=5, b=3, c=1, d=1 |
| Q22 Strategic committee | 46 | a=5, b=3, c=1, d=1 |
| Q23 Incident Management System | 47 | a=5, b=1 |
| Q24 Risk assessment | 49 | a=1, b=2, c=3, d=4, e=5 |
| Q25 Operational/logistical readiness | 50 | a=1, b=2, c=3, d=4, e=5 |
| Q28 Coordinator | 66 | a=5, b=3, c=1 |
| Q30 Documented roles | 68 | a=5, b=3, c=1 |
| Q32 Surge staffing | 77 | a=1, b=2, c=3, d=4, e=5 |
| Q33 Staff roster | 78 | a=5, b=3, c=2, d=1, e=1 |
| Q34 Rapid-team deployment | 80 | a=5, b=3, c=1, d=1 |
| Q38 Information exchange | 105 | a=1, b=2, c=4, d=5 |
| Q39 Technology | 107 | a=1, b=2, c=3, d=4, e=5 |
| Q40 Information gaps (severity reversed) | 108 | a=1, b=2, c=3, d=5 |
| Q41 Situation room | 109 | a=5, b=1, c=1 |
| Q42 SITREPs | 110 | a=1, b=2, c=3, d=5, e=1 |
| Q18 Intersectoral coordination | 41 | a=1, b=3, c=5, d=1 |
| Q19 National DRM integration | 42 | a=1, b=2, c=4, d=5 |
| Q21 International cooperation | 44 | a=5, b=4, c=4, d=1, e=1 |

If the Excel questionnaire changes its choices or column order, both the dictionaries and the matching regression tests must be updated. The generator does not silently guess unknown values.

### Worked example: Argentina, Governance & legal

| Item | Selected response | Rating |
|---|---|---:|
| Q10 | Initial legal framework | 2 |
| Q12 | Legal framework does not support timely decisions | 1 |
| Q13 | Included in a national plan | 5 |
| Q14 | Initial/ad hoc financing | 2 |
| Q15 | No formal SOP | 1 |

Mean = `(2+1+5+2+1)/5 = 2.2`. Converted = `(2.2−1)/4×100 = 30/100`. This matches the Argentina reference infographic. Its other four scores are: **Operations 83, Human resources 55, Information management 65, Coordination 58**.

## Maturity levels

| English name on PDF | Score |
|---|---|
| Initial | `<40` |
| Developing | 40–59 |
| Functional | 60–79 |
| Advanced | ≥80 |

Bars in the PDF are color-coded by these levels; scores are always on a common 0–100 scale.

## Responding-country average (orange marker)

The orange vertical marker is **not an average for all countries of the Americas**. For each pillar, the generator:
1. Computes the score for each applicable institutional response.
2. Excludes respondents that explicitly report no EOC.
3. Averages valid institutional scores within each country where multiple institutions respond.
4. Averages those country values without weighting by number of institutions.

The reference is recomputed from the latest Excel upon every build. The responding country count is the number with a scorable value for a pillar, and may differ by pillar.

### Cautions

- An explicit uncertainty selection can produce a low reference score even though capacity is unknown. This is **a property of the reference scoring rubric**, not necessarily a statement about actual capacity.
- Genuine blank/unrecognized data are omitted, not imputed as 1. Denominators can therefore differ by institution.
- Each item has equal weight *inside its pillar*; the system displays five pillar scores. An overall composite is not required or calculated by the fact-sheet generator.
- Pilot-format answers mapped into the final survey (particularly Brazil) should be considered provisional until checked against the original source.
- Prior to external release, the survey owner should verify question selection, category mapping, treatment of unknowns and missing values, and the use of the word "maturity".