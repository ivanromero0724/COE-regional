# EOC-NET Americas · PAHO/WHO 2026 survey dashboard

Interactive **Streamlit** dashboard for the PAHO/WHO regional survey of Health Emergency Operations Centres (COE-S). The project summarizes **self-reported, concrete EOC capacities**; it deliberately **does not calculate composite maturity scores, five-pillar indices, or 0–100 ratings**.

## Application and data

- `app.py` — interactive regional and institutional views.
- `dashboard/data.py` — survey parsing and country-level aggregation, with one country per regional statistic (multiple Colombian institutions retained separately).
- `dashboard/charts.py` — Plotly charts and interactive Americas map.
- `data/Encuesta_OPS_2026_COEs.xlsx` — first worksheet is the live data source.
- `data/geografia/paises_americas.gpkg` — country borders reused from `el-nino-ops`.
- `logos/PAHO_eng.png` and `logos/logo_EOC.png` — original branding.

## Explore

**Regional overview:** country coverage, EOC operations, activation time, most widely reported capacities and key gaps.

**Capacities & gaps:** country-level counts and detailed PHEOC component matrix, including finance, SOPs, information systems, infrastructure and workforce.

**Operations & hazards:** hazard-frequency bands, physical resources, completed training and future priorities.

**Networks & cooperation:** EOC-NET, EMT and GOARN participation, and expertise countries can contribute.

**Country profiles:** separate reporting institutions, qualitative answers, component-level capacity status and hazard / training details. This dashboard does **not** generate or distribute country PDF fact sheets; the survey team produces its own reports independently.

**Methods & data:** explicit source rules, denominators, caveats and a non-personal country-level CSV export.

## Data methods

- The current source has **16 institutional responses from 15 countries**; the application recalculates counts after updates. Colombia has independent entries for the Ministry of Health and Social Protection and the National Institute of Health.
- Regional country capacity is considered "in place" if at least one institution in that country reports a qualifying positive/functional answer. Partially developed capacities are not treated as in place.
- Denominators are specific to each question: a blank response is not the same as a negative response. Survey items introduced later have fewer countries answering.
- Hazard frequencies are *ordinal bands*, not exact counts and cannot be summed across institutions.
- These are **preliminary, self-reported results**, not an external performance assessment or a ranking.
- Contact and personal columns are omitted; free-text responses should be reviewed for potential incidental personal details before a public launch. Keep the source repository private if the Excel includes contact information.

## Deployment

In Streamlit Community Cloud, connect `ivanromero0724/COE-regional` (branch `main`), set **Main file path** to `app.py` and select a suitable app slug, such as `coe-americas-ops`. See [STREAMLIT_DEPLOY.md](STREAMLIT_DEPLOY.md).

GitHub Actions validates the dashboard on source changes; it no longer generates PDF fact sheets.