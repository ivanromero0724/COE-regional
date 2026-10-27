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


def test_map_uses_tight_stable_extent_and_vertical_overlay_legend():
    from dashboard.charts import responding_country_map_bounds
    records,_=load_data()
    countries=country_aggregate(records)
    geo=load_geojson()
    expected_x,expected_y=responding_country_map_bounds(geo,set(countries.iso3))
    fig=countries_map(countries,selection={countries.iloc[0]['country']},lang='es')
    assert tuple(fig.layout.xaxis.range)==expected_x
    assert tuple(fig.layout.yaxis.range)==expected_y
    assert fig.layout.xaxis.constrain=='domain'
    assert fig.layout.yaxis.constrain=='domain'
    assert fig.layout.yaxis.scaleanchor=='x'
    assert fig.layout.height==480
    assert fig.layout.margin.t<=6 and fig.layout.margin.b<=6
    assert fig.layout.legend.orientation=='v'
    assert fig.layout.legend.xanchor=='left'
    assert fig.layout.legend.yanchor=='bottom'
    assert fig.layout.legend.x<0.05
    assert fig.layout.legend.y<0.05
    assert fig.layout.legend.bgcolor.startswith('rgba(255,255,255')
    # The map retains the same extent when switching active country filters.
    other=countries.iloc[-1]['country']
    second=countries_map(countries,selection={other})
    assert tuple(second.layout.xaxis.range)==expected_x
    assert tuple(second.layout.yaxis.range)==expected_y


def test_five_overview_kpis_share_one_navy_treatment():
    from unittest.mock import patch
    from app import kpi_grid
    cards=[('Countries responding',15),('Established EOC-S','67% (10/15)'),
           ('In implementation','33% (5/15)'),('24/7 operation','40% (6/15)'),
           ('Documented formal mandate','50% (7/14)')]
    with patch('app.st.markdown') as markdown:
        kpi_grid(cards,columns=5)
    rendered=markdown.call_args.args[0]
    assert rendered.count('class="kpi"')==5
    assert 'class="kpi accent"' not in rendered
