# Capability Snapshot: indicative scoring methodology

**Purpose.** The five bars are transparent, descriptive summaries of selected closed-answer items in the 2026 PAHO/WHO regional health EOC survey. They are **not** percentages of questions answered, not observed emergency performance, not an approved PAHO capacity assessment, and not a country ranking. The rubric is a technical, **unvalidated analytical choice** in this repository.

## Formula

For response record `r` and domain `d`, recode each eligible categorical answer using the mappings below to an illustrative value on a 0–100 scale. Then take the simple arithmetic average of **scorable** responses, rounded to the nearest whole number:

`score(r,d) = round(sum(item_score(r,i) for i in valid_items) / len(valid_items))`

No weights other than the equal weight of each answered item are applied. Missing or unsupported categories are excluded from the denominator (not scored zero). If all domain items are missing, the corresponding indicator is left blank. Values are calculated **per survey response/institution**, never pooled across institutions from the same country.

## Domains and questions

| Domain on PDF | Original survey questions | Items |
| --- | --- | ---: |
| Governance & legal | Q10 legal framework; Q13 national response plan; Q15 formal manual/SOP; Q14 operating finance | 4 |
| Operations & decisions | Q23 incident-management role; Q20 incident action plan; Q24 risk assessment; Q22 strategic committee; Q25 operational/logistical readiness | 5 |
| Human resources | Q28 designated leader; Q30 documented roles; Q32 surge staffing procedure; Q33 trained personnel roster; Q34 rapid response deployment | 5 |
| Information management | Q39 technical tools; Q42 SITREP procedures; Q41 integrated situation room | 3 |
| Coordination | Q18 intersectoral coordination; Q19 national disaster-risk integration; Q21 international cooperation | 3 |

The exact implementation is in `scripts/generate_country_profiles.py`, within `DOMAINS`, `score_by_index()` and `scores()`.

## Illustrative scoring schemes in the current implementation

- Five-level progress categories (e.g. legal/finance/logistics): `a,b,c,d,e` → **0,25,50,75,100**.
- Yes/no: positive answer **100**, negative **0**.
- Documented formal SOP: Yes **100**, No **0**, Developing **45**.
- Incident action plan: Systematic **100**, Sometimes **50**, No **0**.
- Risk assessment: None **0**, Informal **25**, Occasional **50**, Graded **75**, Systematic **100**.
- Strategic committee: Formal **100**, Developing **50**, No **0** (unrecognized/unknown omitted).
- Coordinator and roles: Formal **100**, Informal/partial **50**, No **0**.
- Trained roster: Updated **100**, Outdated **40**, In progress **35**, No **0** (unknown omitted).
- Deployment role: Leads **100**, Supports **50**, No **0**.
- Intersectoral coordination: Health only **0**, Occasional **50**, Formal and regular **100**.
- Disaster-risk integration: None **0**, Limited **35**, Moderate **65**, High **100**.
- International cooperation: Direct **100**, Via mechanism **85**, Inter-agency **75**, Limited **30**, None **0**.
- Information tools: None/Basic/Institutional/Integrated/Interoperable → **0/25/50/75/100**.
- SITREP: No/Informal/Irregular/Formal regular → **0/30/60/100**.
- Situation room: Integrated **100**, Not integrated **0**.

**Worked example — Argentina, Governance & legal** (current source workbook): framework **25**, national plan **100**, formal SOP **0**, finance **25**. Arithmetic mean: `(25 + 100 + 0 + 25)/4 = 37.5`, rounded to **38/100** on the PDF. This does **not** mean Argentina meets 38% of an internationally validated capacity standard.

## Methodological caveats

1. Domain definitions, thresholds, category weights, and color ranges are analyst choices; they were not externally validated. They can change substantially if the survey owner approves a different rubric.
2. Responses have varying missingness. Denominators should be checked before comparing two institutions; **missing is not a demonstrated lack of capacity**.
3. A high descriptive score can coexist with serious operational gaps, and no score measures actual emergency performance.
4. Brazil's pilot questionnaire required mapping some questions from an earlier format; its compatibility requires special caution.
5. Any public use of these scores should be preceded by technical validation and clear approval of scoring rules.