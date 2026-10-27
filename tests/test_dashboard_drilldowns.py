"""Every regional bar opens country evidence without changing its denominator."""
import re

import pandas as pd

import app as ui
from dashboard.data import (
    CAPACITIES, COOPERATION_MODES, COOPERATION_SKILLS, NETWORK_NAMES,
    RESOURCE_LABELS, TRAINING_LABELS, capacity_table, country_aggregate,
    country_capacity, load_data,
)


def source_countries():
    records, _ = load_data()
    return country_aggregate(records)


def test_capability_rows_match_their_regional_counts_for_every_component():
    countries = source_countries()
    for _, item in capacity_table(countries).iterrows():
        rows = ui.regional_indicator_rows(countries, item)
        assert rows is not None, (item["component"], item["capacity"])
        assert len(rows) == len(countries)
        assert sum(value is True or value == True for _, value in rows if value is not None) == int(item["in_place"])
        assert sum(value is not None for _, value in rows) == int(item["denominator"])


def test_custom_gap_and_cooperation_rows_resolve_exact_source_columns():
    countries = source_countries()
    examples = [
        {"capacity": "Sustainable financing", "col": 36, "positive": ("d", "e")},
        {"capacity": "Formal surge staffing", "col": 77, "positive": ("d", "e")},
        {"capacity": "Structured information exchange", "col": 105, "positive": ("d",)},
        {"capacity": "Strategic leadership", "status_col": "Skill: Strategic leadership"},
        {"capacity": "Exchange of experience", "status_col": "Mode: Exchange of experience"},
        {"capacity": "Dedicated room", "status_col": "Dedicated room"},
    ]
    for item in examples:
        rows = ui.regional_indicator_rows(countries, pd.Series(item))
        assert rows is not None, item
        assert len(rows) == len(countries)
        if "col" in item:
            manual = [country_capacity(row, item["col"], item["positive"])
                      for _, row in countries.sort_values("country").iterrows()]
            assert [value for _, value in rows] == manual


def test_category_disclosures_list_only_countries_in_exact_category():
    countries = source_countries()
    order = ["24/7 continuous", "Response + monitoring", "Response only",
             "Not formally defined", "Not reported"]
    html = ui.distribution_html(countries.operating_mode, "Operating mode", order,
                                "#005A8B", countries, "operating_mode")
    expected_bars = sum((countries.operating_mode == value).any() for value in order)
    assert html.count('<details class="eoc-capacity-disclosure">') == expected_bars
    assert html.count('class="eoc-country-category-item"') == len(countries)
    for group in order:
        count = int((countries.operating_mode == group).sum())
        if count:
            denominator = int(countries.operating_mode.isin(order).sum())
            assert f'{100*count/denominator:.0f}% ({count}/{denominator})' in html
    assert 'class="status-chip status-yes"' not in html


def test_all_regional_capacity_bars_embed_country_statuses():
    countries = source_countries()
    frame = capacity_table(countries)
    for group in CAPACITIES:
        selected = frame[frame.component == group]
        html = ui.capacity_rows_html(selected,country=countries)
        assert html.count('<details class="eoc-capacity-disclosure">') == len(selected)
        assert html.count('class="eoc-country-capacity-item"') == len(selected) * len(countries)
        assert 'class="measure-fill"' in html


def test_training_disclosures_show_both_workforce_series_and_valid_denominators():
    countries = source_countries()
    html = ui.training_drilldown_html(countries)
    assert html.count('<details class="eoc-capacity-disclosure">') == 2 * len(TRAINING_LABELS)
    assert html.count('class="eoc-country-capacity-item"') == 2 * len(TRAINING_LABELS) * len(countries)
    for course in TRAINING_LABELS:
        for prefix in ("Completed: ", "Priority: "):
            valid = countries[prefix + course].dropna()
            n = int(valid.astype(bool).sum())
            d = len(valid)
            assert (f'{100*n/d:.0f}% ({n}/{d})' if d else "No valid responses") in html


def test_cooperation_and_infrastructure_bar_rows_are_expandable():
    countries = source_countries()
    for prefix, names in (("Skill: ", COOPERATION_SKILLS.values()),
                          ("Mode: ", COOPERATION_MODES.values()),
                          ("", RESOURCE_LABELS.values())):
        items=[]
        for name in names:
            col=prefix+name
            vals=countries[col].dropna()
            items.append({"capacity":name, "in_place":int(vals.astype(bool).sum()),
                          "denominator":len(vals), "status_col":col})
        html=ui.capacity_rows_html(pd.DataFrame(items),country=countries)
        assert html.count('<details class="eoc-capacity-disclosure">') == len(items)
        assert html.count('class="eoc-country-capacity-item"') == len(items)*len(countries)


def test_drilldown_html_and_css_are_accessible_and_preserve_native_bars():
    source = open(ui.__file__,encoding="utf-8").read()
    assert '<summary class="eoc-capacity-summary">' in source
    assert 'focus-visible' in source
    assert '.eoc-capacity-chevron' in source
    assert 'display:block;height:100%;background:#009BDA;' in source
    assert '.eoc-operations-card:has(.eoc-capacity-disclosure[open])' in source
    assert 'viz.country_hazards(' in source  # National ordinal-frequency bars remain unchanged.
