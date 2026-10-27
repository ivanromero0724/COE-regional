"""Regional Overview treemaps: correct percentages, gap direction and layout."""
from html import escape
from html.parser import HTMLParser
import math

import pandas as pd
import pytest

from dashboard.data import CAPACITIES, capacity_table, country_aggregate, country_capacity, load_data
from dashboard.i18n import tr
from dashboard.treemap import (
    layout_treemap, overview_treemap_html, cooperation_treemap_html,
)
from dashboard.visual_style import TREEMAP_COLORS, treemap_text_color


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


def test_full_shared_paho_palette_on_overview_and_cooperation_treemaps():
    strengths,gaps=_data()
    strengths_html=overview_treemap_html(strengths,'available')
    gaps_html=overview_treemap_html(gaps,'gap')
    assert len(TREEMAP_COLORS)==7
    assert len(set(TREEMAP_COLORS))==7
    # All seven distinctive colors occur when there are seven or more tiles.
    assert all('background:'+color in strengths_html for color in TREEMAP_COLORS)
    assert all('background:'+color in gaps_html for color in TREEMAP_COLORS[:5])
    assert 'color:'+treemap_text_color(TREEMAP_COLORS[0]) in strengths_html
    assert 'color:'+treemap_text_color(TREEMAP_COLORS[2]) in strengths_html
    from dashboard.data import COOPERATION_SKILLS, COOPERATION_MODES
    responses,_=load_data()
    countries=country_aggregate(responses)
    for kind,items,prefix in [
        ('expertise',COOPERATION_SKILLS,'Skill: '),
        ('modalities',COOPERATION_MODES,'Mode: '),
    ]:
        frame=pd.DataFrame([
            {'capacity':name,
             'in_place':int((countries[prefix+name].dropna()==True).sum()),
             'denominator':len(countries[prefix+name].dropna())}
            for name in items.values()
        ])
        html=cooperation_treemap_html(frame,kind=kind)
        for color in TREEMAP_COLORS[:min(len(frame),len(TREEMAP_COLORS))]:
            assert 'background:'+color in html


def test_capacity_plotly_treemap_uses_same_palette_and_contrasting_text():
    from dashboard.data import country_aggregate, load_data, capacity_table
    from app import capacity_response_distribution, capacity_chart
    data,_=load_data()
    countries=country_aggregate(data)
    for _,item in capacity_table(countries).iterrows():
        counts=capacity_response_distribution(countries,item)
        if counts.empty:
            continue
        fig=capacity_chart(item,counts,'treemap')
        colors=list(fig.data[0].marker.colors)
        assert colors==[TREEMAP_COLORS[i%len(TREEMAP_COLORS)] for i in range(len(colors))]
        assert list(fig.data[0].textfont.color)==[
            treemap_text_color(color) for color in colors
        ]


def test_cooperation_title_is_a_natural_question_in_both_languages():
    from pathlib import Path
    app=(Path(__file__).resolve().parents[1]/'app.py').read_text(encoding='utf-8')
    assert "section('How can countries cooperate?'," in app
    assert tr('How can countries cooperate?','es') == '¿Cómo pueden cooperar los países?'
    assert 'Modalidades de cooperación entre países' not in tr('How can countries cooperate?','es')


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


def test_cooperation_treemaps_rank_actual_country_offers_bilingually():
    from dashboard.data import COOPERATION_SKILLS, COOPERATION_MODES
    from dashboard.treemap import cooperation_treemap_html
    responses,_=load_data()
    countries=country_aggregate(responses)
    for kind,items,prefix,limit in [
        ('expertise',COOPERATION_SKILLS,'Skill: ',9),
        ('modalities',COOPERATION_MODES,'Mode: ',7),
    ]:
        data=[]
        for name in items.values():
            valid=countries[prefix+name].dropna()
            data.append({'capacity':name,'in_place':int((valid==True).sum()),
                         'denominator':len(valid)})
        frame=(pd.DataFrame(data).sort_values(['in_place','capacity'],
                  ascending=[False,True]).head(limit))
        assert frame.in_place.le(frame.denominator).all()
        for lang in ('en','es'):
            html=cooperation_treemap_html(frame,lang=lang,kind=kind)
            assert html.count('class="eoc-overview-treemap-tile eoc-cooperation-tile"')==limit
            assert '<details' not in html
            assert 'eoc-country-capacity-item' not in html
            for _,row in frame.iterrows():
                n,d=int(row.in_place),int(row.denominator)
                assert escape(tr(row.capacity,lang)) in html
                assert f'{100*n/d:.0f}%' in html if d else '0%' in html
                assert f'({n}/{d})' in html
    with pytest.raises(ValueError):
        cooperation_treemap_html(frame,kind='unrecognized')


def test_all_treemap_tile_faces_have_square_corners():
    """All shared HTML treemaps use the same squared-off block style."""
    from pathlib import Path
    app=(Path(__file__).resolve().parents[1]/'app.py').read_text(encoding='utf-8')
    rule=app.split('.eoc-overview-treemap-face{',1)[1].split('}',1)[0]
    assert 'border-radius:0;' in rule
    assert 'border-radius:7px' not in rule
    # Overview and cooperation both render that exact shared face class.
    overview=overview_treemap_html(_data()[0],'available')
    assert 'class="eoc-overview-treemap-face"' in overview
    from dashboard.data import COOPERATION_MODES
    frame=pd.DataFrame([{'capacity':v,'in_place':3,'denominator':5}
                        for v in COOPERATION_MODES.values()])
    coop=cooperation_treemap_html(frame,kind='modalities')
    assert 'class="eoc-overview-treemap-face eoc-cooperation-tile-face"' in coop
