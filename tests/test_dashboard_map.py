"""Validate respondent-focused, truly non-draggable map with hover popups."""
from pathlib import Path

from dashboard.data import load_data, country_aggregate
from dashboard.charts import load_geojson, countries_map


def test_americas_map_contains_country_polygons_and_tooltips():
    records, _ = load_data()
    countries = country_aggregate(records)
    geo = load_geojson()
    assert geo is not None and len(geo["features"]) > 15
    geometry_codes = {f["properties"]["ISO_CC"] for f in geo["features"]}
    assert set(countries["iso3"]).issubset(geometry_codes)

    for lang in ("en", "es"):
        fig = countries_map(countries, set(countries["country"]), lang=lang)
        assert fig is not None
        traces = fig.to_plotly_json()["data"]
        assert traces and all(t["type"] == "scatter" for t in traces)
        assert all(t["hoveron"] == "fills" for t in traces)
        assert all(t["hovertemplate"] for t in traces)
        assert all(t["fill"] == "toself" for t in traces)


def test_regional_map_viewport_cannot_pan_or_zoom():
    records, _ = load_data()
    fig = countries_map(country_aggregate(records))
    assert fig.layout.dragmode is False
    assert fig.layout.xaxis.fixedrange is True
    assert fig.layout.yaxis.fixedrange is True
    assert fig.layout.xaxis.range[0] <= -92
    assert fig.layout.xaxis.range[1] >= -35
    assert fig.layout.yaxis.range[1] <= 29
    source = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")
    scope = source.split("def coverage_map(country,selected):", 1)[1].split("def regional_overview(", 1)[0]
    assert "'scrollZoom':False" in scope
    assert "'doubleClick':False" in scope
    assert "'staticPlot':False" in scope
