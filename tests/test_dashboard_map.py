"""Ensure the displayed map actually contains the bundled Americas polygons."""
from dashboard.data import load_data, country_aggregate
from dashboard.charts import load_geojson, countries_map


def test_americas_map_contains_country_polygons():
    records, _ = load_data()
    countries = country_aggregate(records)
    geo = load_geojson()
    assert geo is not None and len(geo["features"]) > 15
    geometry_codes = {f["properties"]["ISO_CC"] for f in geo["features"]}
    assert set(countries["iso3"]).issubset(geometry_codes)

    for lang in ("en", "es"):
        fig = countries_map(countries, set(countries["country"]), lang=lang)
        assert fig is not None
        fig_data = fig.to_plotly_json()
        assert fig_data["data"]
        assert all(trace["type"] == "choroplethmap" for trace in fig_data["data"])
        mapped = {str(code) for trace in fig_data["data"] for code in trace["locations"]}
        assert set(countries["iso3"]).issubset(mapped)
        assert fig_data["layout"]["map"]["style"] == "white-bg"


def test_regional_map_has_fixed_extent_without_pan_or_zoom():
    """The map stays fixed while Plotly country tooltips remain enabled."""
    from pathlib import Path
    records,_=load_data()
    fig=countries_map(country_aggregate(records))
    assert fig.layout.dragmode is False
    assert fig.layout.map.center.lat==-11
    assert fig.layout.map.center.lon==-79
    assert fig.layout.map.zoom==1.55
    source=(Path(__file__).resolve().parents[1]/'app.py').read_text(encoding='utf-8')
    scope=source.split('def coverage_map(country,selected):',1)[1].split('def regional_overview(',1)[0]
    assert "'scrollZoom':False" in scope
    assert "'doubleClick':False" in scope
    assert "'displayModeBar':False" in scope
    assert "'staticPlot':False" in scope
