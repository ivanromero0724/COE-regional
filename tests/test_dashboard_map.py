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
    # Mexico's northern edge must remain visible (including a small margin).
    assert 33 <= fig.layout.yaxis.range[1] <= 38
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
    # No aspect-ratio letterboxing: both axes occupy the whole plot area.
    assert fig.layout.xaxis.constrain=='domain'
    assert fig.layout.yaxis.constrain=='domain'
    assert fig.layout.yaxis.scaleanchor=='x'
    assert fig.layout.yaxis.scaleratio==1
    assert fig.layout.height==600
    assert fig.layout.margin.t==0 and fig.layout.margin.b==0
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


def test_guatemala_brazil_focus_still_includes_bahamas_argentina_chile():
    """Important northern, central and southern survey countries stay visible."""
    from dashboard.charts import responding_country_map_bounds
    records,_=load_data()
    countries=country_aggregate(records)
    geo=load_geojson()
    (xmin,xmax),(ymin,ymax)=responding_country_map_bounds(
        geo,set(countries.iso3)
    )
    for code in ('GTM','BRA','BHS','ARG','CHL','MEX'):
        hits=[f for f in geo['features']
              if f['properties'].get('ISO_CC')==code]
        assert hits, code
        coords=[]
        def visit(value):
            if not isinstance(value,(list,tuple)):
                return
            if len(value)>=2 and all(isinstance(x,(int,float)) for x in value[:2]):
                coords.append(value)
            else:
                for node in value:
                    visit(node)
        for feature in hits:
            visit(feature['geometry'].get('coordinates',[]))
        assert coords, code
        assert all(xmin < p[0] < xmax and ymin < p[1] < ymax for p in coords),code
    fig=countries_map(countries)
    assert fig.layout.yaxis.scaleanchor=='x'
    assert fig.layout.yaxis.scaleratio==1
    assert fig.layout.height==600


def test_mexico_is_entirely_inside_the_regional_map_viewport():
    """Context countries must not be cropped just because they did not respond."""
    from dashboard.charts import responding_country_map_bounds
    records,_=load_data()
    countries=country_aggregate(records)
    geo=load_geojson()
    mexican_features=[f for f in geo['features']
                      if f['properties'].get('ISO_CC')=='MEX']
    assert mexican_features, 'Mexico must be available in the map context'
    values=[]
    def visit(coord):
        if not isinstance(coord,(list,tuple)):
            return
        if len(coord)>=2 and all(isinstance(x,(int,float)) for x in coord[:2]):
            values.append((coord[0],coord[1]))
        else:
            for nested in coord:
                visit(nested)
    for feature in mexican_features:
        visit(feature['geometry']['coordinates'])
    assert values
    (xmin,xmax),(ymin,ymax)=responding_country_map_bounds(geo,set(countries.iso3))
    assert min(x for x,_ in values)>xmin
    assert max(x for x,_ in values)<xmax
    assert min(y for _,y in values)>ymin
    assert max(y for _,y in values)<ymax
    # It must not require selecting Mexico or counting it as a survey respondent.
    assert 'MEX' not in set(countries.iso3)
    fig=countries_map(countries)
    assert fig.layout.margin.t==0 and fig.layout.margin.b==0
    assert fig.layout.legend.orientation=='v'


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
    # Only the icon stroke turns orange; backgrounds, borders and KPI text stay blue.
    source=(Path(__file__).resolve().parents[1]/'app.py').read_text(encoding='utf-8')
    assert 'border-radius:10px;background:#FFF1E9;color:#F36B32;' in source
    assert '.kpi.accent{border-top-color:#005A8B;}' in source
    assert '.kpi.accent .kpi-icon{background:#FFF1E9;color:#F36B32;}' in source
    assert '.kpi{\n' in source


def test_coverage_map_card_has_no_white_frame_padding():
    source=(Path(__file__).resolve().parents[1]/'app.py').read_text(encoding='utf-8')
    css=source.split('.st-key-eoc_coverage_map_panel{',1)[1].split('}',1)[0]
    assert 'padding:0!important;' in css
    assert 'border:1px solid #DFE9F1!important;' in css
    assert '[data-testid="stPlotlyChart"]{' in source
    fig=countries_map(country_aggregate(load_data()[0]))
    assert fig.layout.margin.l==fig.layout.margin.r==0
    assert fig.layout.margin.t==fig.layout.margin.b==0


def test_southern_chile_and_argentina_clear_the_lower_map_edge():
    """Map framing must include the southern context with additional clearance."""
    from dashboard.charts import responding_country_map_bounds
    records,_=load_data()
    countries=country_aggregate(records)
    geo=load_geojson()
    points=[]
    def visit(coords):
        if not isinstance(coords,(list,tuple)):
            return
        if len(coords)>=2 and all(isinstance(v,(int,float)) for v in coords[:2]):
            points.append((coords[0],coords[1]))
        else:
            for child in coords:
                visit(child)
    for code in ('CHL','ARG'):
        matched=[feature for feature in geo['features']
                 if feature['properties'].get('ISO_CC')==code]
        assert matched, code
        for feature in matched:
            visit(feature['geometry']['coordinates'])
    assert points
    (xmin,xmax),(ymin,ymax)=responding_country_map_bounds(geo,set(countries.iso3))
    # The south tip is not pressed against or clipped by the frame.
    assert min(y for _,y in points)-ymin>=2.9
    assert ymax>=33  # Northern Mexico remains fully visible as well.
    fig=countries_map(countries)
    assert fig.layout.yaxis.scaleanchor=='x'
    assert tuple(fig.layout.yaxis.range)==(ymin,ymax)
