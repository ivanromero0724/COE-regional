# PAHO / EOC-NET Americas — 2026 country fact sheets

Automated, print-ready English-language **one-page PDF per country**, based on the first sheet of the PAHO/WHO 2026 survey. Both tracked institutional logos are used. The palette is PAHO-inspired navy / cyan with orange highlights.

## Inputs

- `data/Encuesta_OPS_2026_COEs.xlsx` — first worksheet is the survey data source.
- `logos/PAHO_eng.png` — PAHO/WHO identity.
- `logos/logo_EOC.png` — EOC-NET identity.

## Outputs

- `output/PAHO_EOC_Country_Fact_Sheets_2026.pdf` — complete PDF, **one page per responding country**.
- `output/countries/{country}.pdf` — separate PDFs for distribution.

Currently there are **18 survey submissions from 15 countries**. Bolivia, Colombia and Ecuador have two records each: their single-page fact sheet places the submissions in **separate institutional panels**, not an artificial national average. No respondent names, phone numbers or email addresses are printed.

## Automatic updates

GitHub Actions workflow: **Build EOC country fact sheets** (`.github/workflows/fact-sheets.yml`). It runs after changes to `data/`, `logos/`, the generator or workflow configuration, and can also be started in **Actions → Build EOC country fact sheets → Run workflow**. It installs dependencies, regenerates/validates the PDFs, stores a 90-day workflow artifact, and commits the new PDFs into `output/` using `GITHUB_TOKEN`. Commits to `output/` alone do not trigger a new build.

To rebuild locally on Ubuntu or macOS (DejaVu fonts required):

```bash
python -m pip install -r requirements.txt
python scripts/generate_country_profiles.py
```

## Methodology and limitations

- Content is **self-reported** and has not been externally validated. This is a descriptive technical summary, **not an official PAHO country assessment or ranking**.
- The 5 capability bars are *indicative survey-derived domain indicators*, scored 0–100. Each bar is an equally weighted average of the non-missing mapped questionnaire items in that domain, not a validated capacity scale. The exact mappings and included item indices are explicit in `scripts/generate_country_profiles.py` (`DOMAINS`, `score_by_index`). Missing/unknown answers are excluded from the denominator, **not treated as zero**. Do not compare values without checking response completeness.
- The printed indicators, resources, training and hazard frequency are derived directly from closed questionnaire fields. The PDF cannot reproduce all 50 survey questions in one page; see the workbook for full responses.
- Where a source response contains open-ended Spanish/Portuguese text, existing English editorial paraphrases of reported strengths/areas are only shown if the narrative text has **not changed** from the 2026 reviewed version (SHA-256 fingerprint, no personal data). If it changes or if a new institution is added, the script instead generates short English-language insights from closed questions; **untranslated free text is not published**.
- The **Brazil** survey record was imported from an earlier March 2026 pilot. Some variables were mapped to the later questionnaire, so it may not be strictly comparable with subsequent records.
- Ecuador contains conflicting institutional statuses (one reports a centre/equivalent and another reports none); both submissions remain separate and are not reconciled without clarification.
- The workbook can include personal contact information. **Keep the GitHub repository private**, restrict distribution of raw data, and check country narratives before external publication. Only non-personal institutional indicators are exported.

## When the survey schema changes

Column-position mappings are in `scripts/generate_country_profiles.py`. If questionnaire fields are inserted, renamed or reordered, update the mappings and check country output before release. The generator is deterministic and does not call translation or generative AI APIs.