# EOC-NET Americas · Streamlit dashboard (2026)

Production-oriented dashboard for the *2026 PAHO/WHO regional survey of Health Emergency Operations Centres (COE-S)*.

## Start in Streamlit Community Cloud

1. Open **https://share.streamlit.io/**, connect GitHub, and select `ivanromero0724/COE-regional`.
2. Choose branch `main` and **main file `app.py`**.
3. Select Python **3.11** or another supported compatible version.
4. Deploy. The source survey workbook, GeoPackage, logos and computed PDF files are already tracked in the repository.
5. When the Excel in `data/` is changed and committed, Streamlit Cloud should redeploy the app from GitHub (use **Reboot app** if your deployment does not update automatically). No Streamlit secrets, database, API keys or external geographic services are needed.

To execute locally with the dependencies installed:

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

## Data and dependencies

- Survey: `data/Encuesta_OPS_2026_COEs.xlsx`, **first worksheet** only; one response per row.
- Boundaries: `data/geografia/paises_americas.gpkg` — copied **byte-for-byte** from the user’s `ivanromero0724/el-nino-ops` repository. Geographic IDs: `ISO_CC` (ISO-3), `COUNTRY`.
- Branding: `logos/logo_EOC.png` and `logos/PAHO_eng.png` are displayed at right in a consistent header; imagery is embedded locally, not hosted by an external CDN.
- Calculations: `dashboard/data.py`, shared 24-question scoring import from `scripts/generate_country_profiles.py`; visualization: `dashboard/charts.py`. Site styling: `app.py` and `.streamlit/config.toml`.
- Reference reports provided to guide design and definition: **PAHO EOC Regional Overview 2026 EN** (3 pages) and **PAHO EOC Country Profiles 2026 EN** (15 pages). The **live Excel, not the dated PDF reports**, is the definitive source for dynamic counts.

## Navigation

- **Regional overview → Overview**: coverage map, country KPIs, operating modes, activation, five maturity pillars and cooperation priorities.
- **Regional overview → Capacities & gaps**: by PHEOC component, capacity count and country matrix. Thresholds reflect capacities fully **in place** (not in development).
- **Regional overview → Operations & hazards**: ordinal hazard frequency heatmap, resources and training completed versus priorities.
- **Regional overview → Networks & cooperation**: EOC-NET, EMT and GOARN participation status. Denominators account for fewer countries answering late questionnaire items.
- **Country profiles**: country → institution, maturity radar with responding-country mean, hazards, equipment, training, open-ended original-language responses, PDF download.
- **Methods & data**: definitions, limitations, counts and safe export without personal fields.

## Methodology and safeguards

- All 16 (current) *institutional* survey records remain separate, including two in Colombia.
- Each of the 15 (current) responding countries contributes **one** observation to regional summaries. For “capacity in place” the country is positive if **any** of its institutions reports an in-place capacity. For regional maturity scores, institution scores are averaged within a country, then countries are weighted equally.
- The five 0–100 scores use **exactly the same 24-item recoding** as the fact-sheet generator. This is an **indicative, self-reported** maturity rubric, not externally validated, not a ranking.
- Hazards are categorical bands (none, 1–2, 3–5, >5); they are not treated as exact counts or summed across institutions.
- A “No response” is distinct from a negative response. Later networks and workforce questions were completed by fewer countries, and their denominator is correspondingly smaller.
- **Sensitive data:** the app does not publish the survey respondent’s name, email, phone or submission identifiers. The country-level CSV export contains only non-personal metrics. Survey free-text fields are redacted for telephone/email patterns but could contain other personally identifiable details: **review such fields before making the deployment public**.
- The GeoPackage, survey and logos are stored locally in this repo; the map is generated using Plotly/GeoPandas without an external basemap provider.

## Tests

```bash
python -m pytest tests/test_dashboard_data.py -q
```

The tests verify schema consistency, strict capacity denominators, ISO coverage, privacy-safe exports, and score equality with the existing PDF generator.