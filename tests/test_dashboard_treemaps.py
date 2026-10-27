"""Regional Overview treemaps: correct percentages, gap direction and layout."""
from html import escape
from html.parser import HTMLParser
import math

import pandas as pd
import pytest

from dashboard.data import CAPACITIES, capacity_table, country_aggregate, country_capacity, load_data
from dashboard.i18n import tr
from dashboard.treemap import (
    BLUE_SHADES, ORANGE_SHADES, layout_treemap, overview_treemap_html,
)


def _data():
    records,_=load_data()
    countries=country_aggregate(records)
    caps=capacity_table(countries)
    caps=caps[caps.component.isin(CAPACITIES)]
    strengths=caps[caps.denominator>0].sort_values(
        ['in_place','capacity'],ascending=[False,True]).head(7)
    priorities=[
        ('Sustainable financing',36,('d','e')),
        ('Formal surge staffing',77,('d','e')),
        ('Updated surge roster',78,('a',)),
        ('Integrated information tools',107,('d','e')),
        ('Structured information exchange',105,('d',)),
    ]
    items=[]
    for label,col,positive in priorities:
        valid=[country_capacity(country,col,positive)
               for _,country in countries.iterrows()]
        items.append({'capacity':label,'in_place':sum(x is True for x in valid),
                      'denominator':sum(x is not None for x in valid)})
    return strengths,pd.DataFrame(items)


class TileParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tiles=[]
        self.labels=[]
    def handle_starttag(self,tag,attrs):
        props=dict(attrs)
        if tag=='div' and props.get('class')=='eoc-overview-treemap-tile':
            self.tiles.append(props)
        if tag=='div' and props.get('class')=='eoc-overview-treemap-face':
            self.labels.append(props)


def test_regional_treemaps_show_all_seven_strengths_and_five_gaps_bilingually():
    strengths,gaps=_data()
    for mode,data in [('available',strengths),('gap',gaps)]:
        for lang in ['en','es']:
            html=overview_treemap_html(data,mode,lang)
            parsed=TileParser()
            parsed.feed(html)
            assert len(parsed.tiles)==len(data)
            assert len(parsed.labels)==len(data)
            assert '<details' not in html
            assert 'eoc-country-capacity-item' not in html
            assert 'eoc-overview-treemap-card' in html
            for _,row in data.iterrows():
                n=int(row.in_place) if mode=='available' else int(row.denominator-row.in_place)
                d=int(row.denominator)
                expected=f'{100*n/d:.0f}% ({n}/{d})'
                assert expected in html
                assert escape(tr(row.capacity,lang)) in html
            assert 'eoc-overview-treemap-caption' not in html
            assert 'Tile area reflects' not in html
            assert 'El área de cada bloque' not in html


def test_gap_percentage_is_inverse_of_implementation_percentage():
    _,gaps=_data()
    for _,r in gaps.iterrows():
        n=int(r.denominator-r.in_place)
        assert 0<=n<=r.denominator
        report=overview_treemap_html(gaps,'gap')
        assert f'{100*n/r.denominator:.0f}% ({n}/{int(r.denominator)})' in report
    assert 'Not fully in place among valid responses' in report


def test_layout_tiles_cover_complete_chart_without_overlap_or_extra_space():
    strengths,gaps=_data()
    for data,mode in [(strengths,'available'),(gaps,'gap')]:
        rows=[
            {'label':r.capacity,
             'numerator':int(r.in_place if mode=='available' else r.denominator-r.in_place),
             'denominator':int(r.denominator)}
            for _,r in data.iterrows()
        ]
        tiles=layout_treemap(rows)
        assert len(tiles)==len(data)
        total_area=0
        for v in tiles:
            x,y,w,h=v['rect']
            assert 0<=x<=100 and 0<=y<=100
            assert w>0 and h>0
            assert x+w<=100.0001 and y+h<=100.0001
            total_area+=w*h
        assert math.isclose(total_area,10000,abs_tol=0.001)
        for i,a in enumerate(tiles):
            ax,ay,aw,ah=a['rect']
            for b in tiles[i+1:]:
                bx,by,bw,bh=b['rect']
                overlap=max(0,min(ax+aw,bx+bw)-max(ax,bx))*max(0,min(ay+ah,by+bh)-max(ay,by))
                assert overlap<1e-5


def test_colors_are_paho_blue_for_strengths_or_orange_for_gaps():
    strengths,gaps=_data()
    strengths_html=overview_treemap_html(strengths,'available')
    gaps_html=overview_treemap_html(gaps,'gap')
    assert any(color in strengths_html for color in BLUE_SHADES)
    assert any(color in gaps_html for color in ORANGE_SHADES)
    assert not any(color in gaps_html for color in BLUE_SHADES)
    assert not any(color in strengths_html for color in ORANGE_SHADES)


def test_invalid_counts_are_rejected_instead_of_misrepresented():
    with pytest.raises(ValueError):
        layout_treemap([{'label':'Invalid','numerator':7,'denominator':4}])
    with pytest.raises(ValueError):
        overview_treemap_html(pd.DataFrame([{'capacity':'A','in_place':1,'denominator':2}]),'other')


def test_regional_gap_description_is_clear_in_both_languages():
    from pathlib import Path
    app=(Path(__file__).resolve().parents[1]/'app.py').read_text(encoding='utf-8')
    assert "'Countries where each capacity is not yet fully established.'" in app
    assert "Share without each fully established capacity, among valid responses." not in app
    assert tr('Countries where each capacity is not yet fully established.','es') == (
        'Países donde cada capacidad aún no está plenamente establecida.'
    )
    assert '.eoc-overview-treemap-caption{' not in app
