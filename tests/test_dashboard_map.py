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
