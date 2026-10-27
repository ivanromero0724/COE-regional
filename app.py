"""PAHO/WHO | EOC-NET Americas 2026 — regional-to-country survey dashboard.

Deploy in Streamlit Community Cloud: repository COE-regional, main file app.py.
Data is bundled in data/ and refreshed by a GitHub/Streamlit Cloud redeploy.
"""
from __future__ import annotations
import base64
import html
from io import BytesIO
from PIL import Image
from pathlib import Path
import pandas as pd
import numpy as np
import streamlit as st
from dashboard.data import (
  ROOT, XLSX, RESOURCE_LABELS, TRAINING_LABELS,
  HAZARD_LABELS, NETWORK_NAMES, COOPERATION_SKILLS, COOPERATION_MODES, CAPACITIES, load_data, country_aggregate,
  capacity_table, country_capacity
)
from dashboard import charts as viz
from dashboard.i18n import T, tr, chosen_language

st.set_page_config(page_title='EOC-NET Americas | PAHO 2026',page_icon='🌎',layout='wide',initial_sidebar_state='expanded')
BLUE='#005A8B';CYAN='#009BDA';ORANGE='#F36B32';TEXT='#17324D';MUTED='#607B8A'


@st.cache_data(show_spinner=False)
def img64(path):
    path=Path(path)
    if not path.is_file():return ''
    with Image.open(path) as source:
        source.thumbnail((700,220),Image.Resampling.LANCZOS)
        out=BytesIO();source.convert('RGBA').save(out,format='PNG',optimize=True)
    return base64.b64encode(out.getvalue()).decode('ascii')


def esc(v):return html.escape(str(v))


def ui_style():
    st.markdown('''<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');
    html,body,[class*="css"],.stApp {font-family:'DM Sans',Arial,sans-serif;}
    .stApp {background:#F7FAFC; color:#17324D;}
    /* The native Streamlit toolbar stays fixed and fully opaque on scroll. */
    [data-testid="stHeader"]{
        position:fixed!important;
        top:0!important;
        z-index:999990!important;
        background:#F7FAFC!important;
        background-image:none!important;
        opacity:1!important;
        backdrop-filter:none!important;
        -webkit-backdrop-filter:none!important;
        border-bottom:1px solid #E1EAF1;
        box-shadow:0 2px 8px rgba(0,65,115,.035);
    }
    [data-testid="stSidebar"] {background:#FFFFFF;border-right:1px solid #E1EAF1;}
    [data-testid="stSidebar"] [data-testid="stImage"] {margin-bottom:8px;}
    /* Breathing room below the fixed Streamlit toolbar keeps the PAHO banner fully visible. */
    [data-testid="stMainBlockContainer"], .block-container {width:min(100%,1280px)!important;max-width:1280px!important;margin-left:auto!important;margin-right:auto!important;padding:3.25rem 1.35rem 2.6rem;box-sizing:border-box;}
    h1,h2,h3,h4{color:#005A8B;font-weight:800;letter-spacing:-.025em;}
    h2{font-size:1.42rem!important;}h3{font-size:1.06rem!important;}
    /* Shared one-pixel PAHO border for Streamlit native and HTML chart surfaces. */
    [data-testid="stVerticalBlockBorderWrapper"],
    [data-testid="stVerticalBlockBorderWrapper"] > div{
        border-color:#DFE9F1!important;
        border-radius:12px!important;
        background:#FFFFFF!important;
    }
    /* One CSS frame around the map, identical to the other dashboard cards. */
    .st-key-eoc_coverage_map_panel{
        background:#FFFFFF!important;
        border:1px solid #DFE9F1!important;
        border-radius:12px!important;
        padding:16px!important;
        box-sizing:border-box;
        overflow:hidden;
    }
    .st-key-eoc_coverage_map_panel [data-testid="stVerticalBlock"],
    .st-key-eoc_coverage_map_panel [data-testid="stPlotlyChart"]{
        background:#FFFFFF!important;
    }
    [data-testid="stMetric"] {background:#FFF;border:1px solid #DFE9F1;border-radius:12px;padding:14px;min-height:112px;}
    [data-testid="stMetricValue"] {color:#005A8B;font-size:1.5rem!important;font-weight:800;overflow-wrap:anywhere;}
    [data-testid="stMetricLabel"] {font-size:.75rem!important;color:#597184;}
    .paho-strip{height:7px;background:linear-gradient(90deg,#005A8B 0%,#005A8B 75%,#F36B32 75%,#F36B32 100%);}
    .paho-header{background:#fff;border:1px solid #E1EAF1;border-radius:14px;margin-bottom:18px;overflow:hidden;box-shadow:0 4px 18px rgba(25,75,110,.04);}
    .paho-hero{padding:22px 26px;display:grid;grid-template-columns:minmax(0,1fr) minmax(290px,395px);align-items:center;column-gap:24px;}
    .paho-eyebrow{font-size:.71rem;letter-spacing:.15em;font-weight:800;color:#F36B32;}
    .paho-title{font-size:clamp(1.48rem,2.1vw,2.2rem);font-weight:800;line-height:1.16;letter-spacing:-.035em;color:#005A8B;margin:7px 0;}
    .paho-desc{font-size:.86rem;line-height:1.5;color:#62798C;max-width:650px;}
    .brand-set{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);align-items:center;gap:18px;min-width:0;}
    .brand-set img{display:block;width:100%;height:96px;object-fit:contain;object-position:center;min-width:0;}
     .section-eyebrow{font-size:.69rem;letter-spacing:.14em;font-weight:800;color:#008CBF;margin:7px 0 3px;}
     .section-title{font-size:1.22rem;font-weight:800;letter-spacing:-.02em;color:#005A8B;line-height:1.25;margin:0 0 4px;}
     .section-desc{font-size:.81rem;line-height:1.46;color:#657A8A;margin-bottom:8px;}
    .small-note{color:#667D8D;font-size:.75rem;line-height:1.55;}
    .eoc-note{background:#FFF8F2;border-left:3px solid #F36B32;padding:12px 14px;color:#6C5A4C;font-size:.78rem;border-radius:7px;line-height:1.55;}
    .bigcountry{font-size:2rem;line-height:1.12;color:#005A8B;font-weight:800;overflow-wrap:anywhere;}
    .subtle-label{font-size:.68rem;letter-spacing:.09em;text-transform:uppercase;font-weight:700;color:#678197;}
    .paho-footer{font-size:.72rem;color:#718594;margin-top:25px;border-top:1px solid #DCE8F0;padding:13px 2px;}
    /* Standalone Plotly charts receive the same frame as HTML capacity cards. */
    [data-testid="stPlotlyChart"]{
        background:#FFFFFF;border:1px solid #DFE9F1;
        border-radius:12px;overflow:hidden;box-sizing:border-box;
    }
    div.stButton>button[kind="primary"]{background:#005A8B!important;border-color:#005A8B!important;}
    .kpi-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px;margin:10px 0 20px;}
    .kpi-grid.four{grid-template-columns:repeat(4,minmax(0,1fr));margin-top:14px;}
    /* KPI labels, icons and values form one compact, consistent visual group. */
    .kpi{
        box-sizing:border-box;min-width:0;min-height:117px;background:#FFF;
        border:1px solid #DFE9F1;border-top:3px solid #005A8B;border-radius:13px;
        padding:15px 17px 14px;display:grid;
        grid-template-columns:minmax(0,1fr) 34px;
        grid-template-areas:"label icon" "value icon";
        grid-template-rows:auto auto;align-content:start;align-items:start;
        column-gap:8px;row-gap:9px;
        box-shadow:0 3px 12px rgba(0,75,120,.035);
    }
    .kpi.accent{border-top-color:#F36B32;}
    .kpi .kpi-label{
        grid-area:label;min-height:2.7em;color:#526F84;font-size:.70rem;
        font-weight:800;text-transform:uppercase;letter-spacing:.035em;line-height:1.35;
        overflow-wrap:anywhere;
    }
    .kpi .kpi-value{
        grid-area:value;color:#005A8B;font-size:1.95rem;font-weight:800;
        line-height:1.05;letter-spacing:-.035em;overflow-wrap:anywhere;word-break:normal;
    }
    .kpi .kpi-value.long{font-size:clamp(.95rem,1.15vw,1.16rem);line-height:1.22;letter-spacing:0;}
    .kpi-icon{
        grid-area:icon;display:flex;justify-content:center;align-items:center;
        width:34px;height:34px;border-radius:10px;background:#EAF4FA;color:#005A8B;
    }
    .kpi-icon svg{width:19px;height:19px;flex-shrink:0;}
    .kpi.accent .kpi-icon{background:#FFF1E9;color:#D95A28;}
    .country-identity{display:flex;gap:17px;align-items:center;padding:12px 0 14px;min-width:0;}
    .country-flag{font-size:3rem;line-height:1;flex-shrink:0;display:flex;align-items:center;justify-content:center;}
    .country-identity .institution{font-size:.85rem;color:#647D8D;margin-top:5px;line-height:1.4;overflow-wrap:anywhere;}
    .card-panel{background:#FFF;border:1px solid #DFE9F1;border-radius:12px;padding:17px 18px;margin:1px 0 12px;min-width:0;}
    /* Compact comparisons: align headings without stretching cards or bar spacing.
       Different-length datasets are allowed to finish at their natural height. */
    .eoc-pair-heading{min-height:0;margin:0 0 2px;box-sizing:border-box;}
    .card-panel.eoc-pair-overview,.card-panel.eoc-pair-capacities,.card-panel.eoc-pair-cooperation{
        min-height:0;display:block;box-sizing:border-box;
    }
    /* Match the seven-row capacity card and the five-row priority card in height,
       without stretching the bar rows or adding uneven gaps between them. */
    /* Compact capacity comparison: matched modest height, without oversized empty areas. */
    .card-panel.eoc-pair-capacities{min-height:305px;margin-bottom:0;padding:13px 16px;}
    .card-panel.eoc-pair-capacities .measure-row{padding:6px 0;min-height:35px;}
    /* Five priority rows use the available card height evenly, without changing
       the seven-row capacities card or creating a large empty area at the bottom. */
    .card-panel.eoc-pair-capacities.eoc-priority-card{
        display:grid;
        grid-template-columns:minmax(0,1fr);
        align-content:space-between;
    }
    .eoc-priority-card .measure-row{padding:9px 0;}
    /* One card, same outside height as the 450px map plus its frame padding.
       Keep rows at a consistent rhythm; never stretch the inner content. */
    .card-panel.eoc-pair-overview.eoc-operations-card{
        height:calc(450px + 2rem + 2px);
        min-height:0;
        margin:0;
        padding:16px 18px;
        border:1px solid #DFE9F1;
        border-radius:12px;
        box-sizing:border-box;
        background:#FFFFFF;
        overflow-y:auto;
        overflow-x:hidden;
    }
    .eoc-operations-card .dist-row{min-height:46px;padding:8px 0;}
    .eoc-operations-card .mini-title{margin:10px 0 7px;}
    /* The map is framed only once by its outer Streamlit container. */
    .st-key-eoc_coverage_map_panel [data-testid="stPlotlyChart"]{
        border:0!important;border-radius:0!important;
    }
    .status-tile-grid.eoc-pair-infrastructure{min-height:0;margin:0;grid-template-rows:auto;box-sizing:border-box;}
    .card-title{font-size:.85rem;font-weight:800;color:#005A8B;margin:0 0 12px;}
    .measure-row{display:grid;grid-template-columns:minmax(0,1.35fr) minmax(65px,1fr) 116px;align-items:center;gap:12px;padding:8px 0;border-bottom:1px solid #EDF2F6;min-height:38px;}
    .measure-row:last-child{border-bottom:0;}
    .measure-label{font-size:.80rem;font-weight:600;color:#29485F;line-height:1.35;overflow-wrap:anywhere;}
    .measure-bar{width:100%;height:9px;border-radius:999px;background:#E7F0F6;overflow:hidden;}
    .measure-fill{height:100%;background:#009BDA;border-radius:999px;}
    .measure-value{font-size:.77rem;font-weight:800;color:#005A8B;text-align:right;white-space:nowrap;}
    .mini-title{font-size:.85rem;font-weight:800;color:#005A8B;margin:14px 0 6px;}
    .dist-row{display:grid;grid-template-columns:minmax(0,1.5fr) minmax(70px,1fr) 115px;gap:10px;align-items:center;padding:6px 0;}
    .dist-label{font-size:.77rem;color:#29485F;overflow-wrap:anywhere;}
    .dist-count{white-space:nowrap;font-size:.78rem;color:#005A8B;font-weight:800;text-align:right;}
    .stat-table{width:100%;border-collapse:collapse;font-size:.80rem;}
    .stat-table th{text-align:left;font-size:.71rem;text-transform:uppercase;letter-spacing:.04em;color:#607B8A;background:#F0F6FA;padding:9px 11px;}
    .stat-table td{padding:10px 11px;border-bottom:1px solid #E8F0F5;vertical-align:middle;}
    .stat-table tr:last-child td{border-bottom:0;}
    .stat-table td:first-child{color:#29485F;font-weight:600;overflow-wrap:anywhere;}
    .stat-table-wrap{overflow:auto;max-height:460px;border:1px solid #DFE9F1;border-radius:10px;}
    .status-chip{display:inline-block;white-space:nowrap;border-radius:6px;font-size:.70rem;font-weight:800;padding:5px 9px;}
    .status-yes{background:#E6F5EF;color:#18795E;}
    .status-no{background:#FFF0E8;color:#A84C2F;}
    .status-unknown{background:#EFF3F6;color:#687C8B;}
    .status-tile-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin:8px 0 18px;}
    .status-tile{border:1px solid #DFE9F1;border-radius:10px;background:white;padding:12px;display:grid;grid-template-columns:24px minmax(0,1fr);gap:4px 8px;align-items:center;}
    .status-symbol{font-size:1.2rem;font-weight:900;grid-row:span 2;}
    .status-tile-name{font-size:.79rem;font-weight:700;color:#29485F;overflow-wrap:anywhere;}
    .status-tile-state{font-size:.72rem;color:#607B8A;}
    .network-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:14px 0;}
    .network-card{border:1px solid #DFE9F1;border-top:3px solid #009BDA;border-radius:12px;background:#fff;padding:15px;min-height:120px;}
    .network-name{font-size:.79rem;font-weight:800;color:#005A8B;}
    .network-count{font-size:1.55rem;color:#005A8B;font-weight:800;margin:7px 0;}
    .network-meta{font-size:.73rem;line-height:1.45;color:#61798A;}
    @media(max-width:1150px){.kpi-grid{grid-template-columns:repeat(3,minmax(0,1fr));}.kpi-grid.four{grid-template-columns:repeat(2,minmax(0,1fr));}}
    @media(max-width:900px){.eoc-pair-heading{margin-bottom:0;}
        .card-panel.eoc-pair-overview.eoc-operations-card{height:auto;overflow:visible;}
        .card-panel.eoc-pair-capacities{min-height:0;}}
    @media(max-width:760px){[data-testid="stMainBlockContainer"],.block-container{padding-top:2.75rem;}.measure-row{grid-template-columns:minmax(0,1fr) 115px;row-gap:6px;gap:7px;}.measure-label{grid-column:1 / -1;overflow-wrap:normal;font-size:.74rem;}.measure-bar{grid-column:1;}.measure-value{grid-column:2;}.dist-row{grid-template-columns:minmax(0,1fr) 80px 112px;gap:6px;}.block-container{padding-left:1rem;padding-right:1rem;}.paho-hero{grid-template-columns:1fr;padding:17px;row-gap:14px;}.brand-set{max-width:360px;}.kpi-grid,.kpi-grid.four{grid-template-columns:repeat(2,minmax(0,1fr));}.network-grid{grid-template-columns:1fr;}.status-tile-grid{grid-template-columns:1fr;}.card-panel{padding:13px;}}
    @media(max-width:460px){.kpi-grid,.kpi-grid.four{grid-template-columns:1fr 1fr;gap:8px;}.kpi{padding:11px;min-height:103px;}.kpi .kpi-value{font-size:1.5rem;}.kpi-grid:not(.four)>.kpi:last-child:nth-child(odd){grid-column:span 2;}.country-flag{font-size:2.4rem;}}
    </style>''',unsafe_allow_html=True)


def header():
    eoc=img64(ROOT/'logos/logo_EOC.png');paho=img64(ROOT/'logos/PAHO_eng.png')
    content=f'<img src="data:image/png;base64,{eoc}" alt="EOC-NET"/><img src="data:image/png;base64,{paho}" alt="PAHO/WHO"/>'
    st.markdown(f'''<div class="paho-header"><div class="paho-strip"></div><div class="paho-hero">
       <div><div class="paho-eyebrow">{esc(T("EOC-NET / THE AMERICAS · 2026"))}</div>
       <div class="paho-title">{esc(T("Health Emergency Operations Centres"))}</div>
       <div class="paho-desc">{esc(T("Regional survey dashboard · Institutional preparedness, operational capacities and cooperation"))}</div></div>
       <div class="brand-set">{content}</div></div></div>''',unsafe_allow_html=True)


def section(title,subtitle='',eyebrow=None,paired=False):
    """Shared heading baseline for desktop comparisons; natural height on mobile."""
    pieces=[]
    if eyebrow:pieces.append(f'<div class="section-eyebrow">{esc(T(eyebrow))}</div>')
    pieces.append(f'<div class="section-title">{esc(T(title))}</div>')
    if subtitle:pieces.append(f'<div class="section-desc">{esc(T(subtitle))}</div>')
    cls=' class="eoc-pair-heading"' if paired else ''
    st.markdown(f'<div{cls}>{"".join(pieces)}</div>',unsafe_allow_html=True)


def note(msg):st.markdown(f'<div class="small-note">{esc(T(msg))}</div>',unsafe_allow_html=True)


KPI_ICON_PATHS={
    'Countries responding':'<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a16 16 0 0 1 0 18M12 3a16 16 0 0 0 0 18"/>',
    'Established EOC-S':'<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/><path d="m9 12 2 2 4-4"/>',
    'In implementation':'<rect x="3" y="3" width="18" height="18" rx="3"/><path d="M8 12h8M12 8v8"/>',
    '24/7 operation':'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    'Activation under 2 h':'<path d="m13 2-9 12h7l-1 8 10-12h-7z"/>',
    'EOC status':'<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/>',
    'Operating mode':'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    'Activation time':'<path d="M12 7v5l-4 2"/><circle cx="12" cy="12" r="9"/>',
    '24/7 duty staff':'<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>',
}


def kpi_grid(cards,columns=5):
    """Compact PAHO metric cards, with a stable label/value rhythm."""
    items=[]
    fallback='<path d="M4 18V6M4 18h16M8 14l4-4 3 3 5-6"/>'
    for label,value in cards:
        display=str(value)
        long=' long' if len(display)>12 else ''
        tone=' accent' if label.lower().startswith(('in implementation','activation')) else ''
        svg='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'+KPI_ICON_PATHS.get(label,fallback)+'</svg>'
        items.append(f'<div class="kpi{tone}"><div class="kpi-label">{esc(T(label))}</div>'
                     f'<div class="kpi-icon" aria-hidden="true">{svg}</div>'
                     f'<div class="kpi-value{long}">{esc(T(display))}</div></div>')
    style=' four' if columns==4 else ''
    st.markdown(f'<div class="kpi-grid{style}">{"".join(items)}</div>',unsafe_allow_html=True)


def capacity_rows_html(frame,title=None,pair=None,variant=None):
    """Small visual bars with explicit percentage AND numerator / denominator."""
    contents=[]
    for _,r in frame.iterrows():
        numerator=int(r['in_place']); denominator=int(r['denominator'])
        percent=100*numerator/denominator if denominator else 0
        visible=f'{percent:.0f}% ({numerator}/{denominator})' if denominator else T('No valid responses')
        contents.append(f'<div class="measure-row"><div class="measure-label">{esc(T(r["capacity"]))}</div>'
                        f'<div class="measure-bar"><div class="measure-fill" style="width:{percent:.1f}%"></div></div>'
                        f'<div class="measure-value">{esc(visible)}</div></div>')
    h=f'<div class="card-title">{esc(T(title))}</div>' if title else ''
    pair_class=f' eoc-pair-{pair}' if pair in ('capacities','cooperation') else ''
    variant_class=' eoc-priority-card' if pair=='capacities' and variant=='priority' else ''
    return f'<div class="card-panel{pair_class}{variant_class}">{h}{"".join(contents)}</div>'


def distribution_html(series,title,ordered,color):
    """Percentage uses all displayed response categories, including missing as its own group."""
    total=int(series.isin(ordered).sum())
    entries=[]
    for label in ordered:
        n=int((series==label).sum())
        if not n:continue
        pct=100*n/total if total else 0
        entries.append(f'<div class="dist-row"><div class="dist-label">{esc(T(label))}</div>'
                       f'<div class="measure-bar"><div class="measure-fill" style="width:{pct:.1f}%;background:{color}"></div></div>'
                       f'<div class="dist-count">{pct:.0f}% ({n}/{total})</div></div>')
    return f'<div class="mini-title">{esc(T(title))}</div>{"".join(entries)}'


def status_chip(value):
    if value is None or pd.isna(value):
        return f'<span class="status-chip status-unknown">{esc(T("Not reported"))}</span>'
    return (f'<span class="status-chip status-yes">{esc(T("In place"))}</span>' if bool(value)
            else f'<span class="status-chip status-no">{esc(T("Partial / absent"))}</span>')


def status_grid_html(items,paired_infrastructure=False):
    """Scannable multi-column chips, no wide tables on country pages."""
    cards=[]
    for label,value in items:
        if value is None or pd.isna(value):
            color='#8CA0AF';symbol='—';state=T('Not reported')
        elif bool(value):
            color='#1D947C';symbol='✓';state=T('In place')
        else:
            color='#F36B32';symbol='×';state=T('Partial / absent')
        cards.append(f'<div class="status-tile"><span class="status-symbol" style="color:{color}">{symbol}</span>'
                     f'<span class="status-tile-name">{esc(T(label))}</span><span class="status-tile-state">{esc(state)}</span></div>')
    css='status-tile-grid eoc-pair-infrastructure' if paired_infrastructure else 'status-tile-grid'
    return '<div class="'+css+'">'+''.join(cards)+'</div>'


def compact_table(headers,body,maxheight=None):
    head=''.join(f'<th>{esc(T(x))}</th>' for x in headers)
    rows=''.join('<tr>'+''.join(f'<td>{item}</td>' for item in row)+'</tr>' for row in body)
    height=f' style="max-height:{maxheight}px"' if maxheight else ''
    st.markdown(f'<div class="stat-table-wrap"{height}><table class="stat-table"><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>',unsafe_allow_html=True)


def count_kpis(country):
    operational=int((country.eoc_status=='Established').sum())
    fast=int((country.activation=='Under 2 hours').sum())
    kpi_grid([
        ('Countries responding',len(country)),
        ('Established EOC-S',operational),
        ('In implementation',int((country.eoc_status=='In implementation').sum())),
        ('24/7 operation',int((country.operating_mode=='24/7 continuous').sum())),
        ('Activation under 2 h',fast)])


def country_metric_values(country):
    caps=capacity_table(country)
    return caps


def coverage_map(country,selected):
    try: fig=viz.countries_map(country,selected,lang=chosen_language())
    except Exception as e:
        st.error(T('The geographic layer could not be read. Check data/geografia/paises_americas.gpkg.'));return
    if fig is None:
        st.info(T('Map file not found. The Americas GeoPackage is expected in data/geografia/paises_americas.gpkg.'))
    else:
        # The card's CSS controls its own outline (no extra Streamlit border).
        with st.container(border=False, key='eoc_coverage_map_panel'):
            st.plotly_chart(fig, width='stretch', config={'displayModeBar':False})


def regional_overview(country,active):
    count_kpis(active)
    left,right=st.columns([1.20,1],gap='large')
    with left:
        section('Which countries have EOC-S?',
                'Established or in implementation; countries without survey responses remain gray.',
                eyebrow='01 / EOC-S STATUS',paired=True)
        coverage_map(country,set(active.country))
    with right:
        section('How the EOC-S operate','One observation per responding country.',eyebrow='02 / OPERATIONS',paired=True)
        modes=['24/7 continuous','Response + monitoring','Response only','Not formally defined','Not reported']
        times=['Under 2 hours','2–6 hours','Over 6 hours','Not defined','Not reported']
        # Single bordered HTML card: no nested Streamlit frame/white overlay.
        st.markdown('<div class="card-panel eoc-pair-overview eoc-operations-card">'+
                    distribution_html(active.operating_mode,'Operating mode',modes,BLUE)+
                    distribution_html(active.activation,'Activation after formal decision',times,CYAN)+
                    '</div>',unsafe_allow_html=True)
    st.divider()
    left,right=st.columns(2,gap='large')
    with left:
        section('Most widely reported capacities',
                'Countries reporting an established or functional capacity.',eyebrow='03 / REPORTED CAPACITIES',paired=True)
        ranked=capacity_table(active)
        ranked=ranked[ranked.component.isin(CAPACITIES)]
        ranked=ranked[ranked.denominator>0].sort_values(['in_place','capacity'],ascending=[False,True]).head(7)
        st.markdown(capacity_rows_html(ranked,pair='capacities'),unsafe_allow_html=True)
    with right:
        section('Priority capacity gaps','Countries with the following capacities fully in place.',eyebrow='04 / COOPERATION PRIORITIES',paired=True)
        priorities=[('Sustainable financing',36,('d','e')),
                    ('Formal surge staffing',77,('d','e')),
                    ('Updated surge roster',78,('a',)),
                    ('Integrated information tools',107,('d','e')),
                    ('Structured information exchange',105,('d',))]
        figures=[]
        for label,col,positive in priorities:
            vals=[country_capacity(row,col,positive) for _,row in active.iterrows()]
            figures.append({'capacity':label,'in_place':sum(v is True for v in vals),
                            'denominator':sum(v is not None for v in vals)})
        st.markdown(capacity_rows_html(pd.DataFrame(figures),pair='capacities',variant='priority'),unsafe_allow_html=True)
 


def capacity_and_gaps(active):
    section('Core capacities reported as in place',
            'Country counts reflect only recognized answers to each survey item.',
            eyebrow='01 / CAPACITY PROFILES')
    caps=capacity_table(active)
    component=st.selectbox(T('Explore a component'),list(CAPACITIES.keys()),format_func=lambda value, _lang=chosen_language(): tr(value, _lang),key='capacity_component')
    sliced=caps[caps.component==component]
    a,b=st.columns([1.04,1],gap='large')
    with a:
        st.markdown(capacity_rows_html(sliced,'Capacity availability'),unsafe_allow_html=True)
    with b:
        st.markdown('<div class="mini-title">'+esc(T('Countries reporting each capacity'))+'</div>',unsafe_allow_html=True)
        chosen=st.selectbox(T('Choose capacity'),list(sliced.capacity),format_func=lambda value, _lang=chosen_language(): tr(value, _lang),key='capacity_country_view')
        item=sliced[sliced.capacity==chosen].iloc[0]
        positive=next((valid for lab,col,valid in CAPACITIES[component] if lab==chosen),())
        rows=[]
        for _,r in active.sort_values('country').iterrows():
            status=country_capacity(r,int(item['col']),positive)
            rows.append((esc(T(r.country)),status_chip(status)))
        compact_table(['Country','Reported capacity'],rows,maxheight=450)
        note('Colombia is counted once at regional level when at least one institution reports an in-place capacity.')
    st.divider()
    section('Information systems and surge workforce','Key capacities for technical cooperation.')
    focus=caps[caps.capacity.isin(['Integrated/interoperable platform','Formal SITREP process',
                       'Updated surge roster','Formal surge procedure','Redundant internet connection','Backup power generator'])]
    st.markdown(capacity_rows_html(focus),unsafe_allow_html=True)


def operations_section(active):
    section('Hazards coordinated during the past two years',
            'Categories reflect ordinal frequency bands, not exact event counts.',
            eyebrow='01 / TYPES OF EMERGENCIES')
    st.plotly_chart(viz.hazard_heatmap(active.sort_values('country'),lang=chosen_language()),
                    use_container_width=True,config={'displayModeBar':False})
    st.divider()
    section('Physical infrastructure','Countries reporting these resources.',eyebrow='02 / INFRASTRUCTURE')
    cards=[]
    for label in RESOURCE_LABELS.values():
        valid=active[label].dropna()
        cards.append({'capacity':label,'in_place':sum(bool(v) for v in valid),'denominator':len(valid)})
    st.markdown(capacity_rows_html(pd.DataFrame(cards)),unsafe_allow_html=True)
    st.divider()
    section('Training completed and prioritized','Each country counted once per course.',eyebrow='03 / WORKFORCE DEVELOPMENT')
    training=[]
    for course in TRAINING_LABELS:
        done=active['Completed: '+course].dropna()
        priority=active['Priority: '+course].dropna()
        training.append({'area':course, 'done_n':sum(bool(v) for v in done), 'done_d':len(done),
                         'priority_n':sum(bool(v) for v in priority), 'priority_d':len(priority)})
    st.plotly_chart(viz.training_comparison(pd.DataFrame(training),lang=chosen_language()),
                    use_container_width=True,config={'displayModeBar':False})



def cooperation_section(active):
    section('Regional and global networks',
            'Membership and interest among countries that answered these later survey questions.',
            eyebrow='01 / COOPERATION NETWORKS')
    cards=[]
    for name in NETWORK_NAMES.values():
        valid=active[name]
        counts=valid.value_counts()
        answered=int((valid!='Not reported').sum())
        participating=int(counts.get('Participating',0))
        interested=int(counts.get('Interested',0))
        inactive=int(counts.get('Not participating',0))
        def part_html(n, color, caption):
            pct=(100*n/answered if answered else 0)
            return (f'<div style="width:{pct:.2f}%;background:{color};height:100%" '
                    f'title="{esc(T(caption))}: {pct:.0f}% ({n}/{answered})"></div>')
        bar=('<div style="display:flex;height:12px;width:100%;border-radius:99px;overflow:hidden;background:#EAF1F5">'
              +part_html(participating,'#005A8B','Participating')
              +part_html(interested,'#009BDA','Interested')
              +part_html(inactive,'#CFDDE6','Not participating')+'</div>')
        primary_pct=100*participating/answered if answered else 0
        cards.append(f'<div class="network-card"><div class="network-name">{esc(T(name))}</div>'
                     f'<div class="network-count">{primary_pct:.0f}% '
                     f'<span style="font-size:.82rem;color:#688193">({participating}/{answered})</span></div>'
                     +bar+
                     f'<div class="network-meta">{esc(T("Participating"))} {participating}/{answered} · '
                     f'{esc(T("Interested"))} {interested}/{answered} · '
                     f'{esc(T("Not participating"))} {inactive}/{answered}</div></div>')
    st.markdown('<div class="network-grid">'+''.join(cards)+'</div>',unsafe_allow_html=True)
    with st.expander(T('See country-level network participation')):
        rows=[]
        for _,r in active.sort_values('country').iterrows():
            rows.append(tuple([esc(T(r.country))]+[esc(T(r[name])) for name in NETWORK_NAMES.values()]))
        compact_table(['Country']+list(NETWORK_NAMES.values()),rows,maxheight=450)
    st.divider()
    a,b=st.columns(2,gap='large')
    with a:
        section('Expertise countries can share','Technical expertise reported for cooperation.',
                eyebrow='02 / CAPACITIES OFFERED',paired=True)
        entries=[]
        for name in COOPERATION_SKILLS.values():
            answered=active['Skill: '+name].dropna()
            entries.append({'capacity':name,'in_place':sum(bool(x) for x in answered),'denominator':len(answered)})
        ranked=pd.DataFrame(entries).sort_values('in_place',ascending=False).head(9)
        st.markdown(capacity_rows_html(ranked,pair='cooperation'),unsafe_allow_html=True)
    with b:
        section('How countries can cooperate','Reported modalities of technical collaboration.',
                eyebrow='03 / MODALITIES',paired=True)
        entries=[]
        for name in COOPERATION_MODES.values():
            answered=active['Mode: '+name].dropna()
            entries.append({'capacity':name,'in_place':sum(bool(x) for x in answered),'denominator':len(answered)})
        ranked=pd.DataFrame(entries).sort_values('in_place',ascending=False)
        st.markdown(capacity_rows_html(ranked,pair='cooperation'),unsafe_allow_html=True)
    st.markdown('<div class="eoc-note">'+esc(T('The cooperation and network questions were completed by fewer countries. Each indicator uses the number of valid responses to that specific question.'))+'</div>',unsafe_allow_html=True)


def flag_from_iso(iso):
    alpha={'ARG':'AR','BHS':'BS','BLZ':'BZ','BOL':'BO','BRA':'BR','COL':'CO','DMA':'DM','ECU':'EC','SLV':'SV',
           'GTM':'GT','HND':'HN','PAN':'PA','PRY':'PY','PER':'PE','LCA':'LC'}.get(iso,'')
    return ''.join(chr(ord(k)-ord('A')+0x1F1E6) for k in alpha)



def country_profile(records,countries):
    region=st.selectbox(T('Select a country'),sorted(records.country.unique()),format_func=lambda value, _lang=chosen_language(): tr(value, _lang),key='selected_country')
    options=records[records.country==region].sort_values('institution')
    rows={f'{T(x.institution)} · {T("Excel row")} {x.source_excel_row}':int(i) for i,x in options.iterrows()}
    selected=st.selectbox(T('Reporting institution'),list(rows.keys()),key='selected_institution')
    r=records.loc[rows[selected]]
    st.markdown(f'<div class="country-identity"><div class="country-flag">{flag_from_iso(r.iso3)}</div>'
                f'<div><div class="bigcountry">{esc(T(r.country))}</div>'
                f'<div class="institution">{esc(T(r.institution))}</div></div></div>',unsafe_allow_html=True)
    staff=f'{int(r.staff_24_7)}' if pd.notna(r.staff_24_7) else 'Not reported'
    kpi_grid([('EOC status',r.eoc_status),('Operating mode',r.operating_mode),
              ('Activation time',r.activation),('24/7 duty staff',staff)],columns=4)
    section('Reported institutional capacities','Answers from this institution grouped by PHEOC core component.',
            eyebrow='01 / REPORTED CAPACITIES')
    component=st.selectbox(T('Explore a component'),list(CAPACITIES.keys()),format_func=lambda value, _lang=chosen_language(): tr(value, _lang),key='country_component')
    st.markdown(status_grid_html([(label,country_capacity(r,col,positive)) for label,col,positive in CAPACITIES[component]]),unsafe_allow_html=True)
    note('Only fully qualifying responses are classified as in place. Missing answers remain separate.')
    st.divider()
    a,b=st.columns(2,gap='large')
    with a:
        section('Hazards coordinated','Frequency band for the selected institution.',eyebrow='02 / LAST TWO YEARS',paired=True)
        st.plotly_chart(viz.country_hazards(r,lang=chosen_language()),
                        use_container_width=True,config={'displayModeBar':False})
    with b:
        section('Physical infrastructure','Resources the institution reports as available.',eyebrow='03 / INFRASTRUCTURE',paired=True)
        st.markdown(status_grid_html([(label,r[label] if pd.notna(r[label]) else None) for label in RESOURCE_LABELS.values()],paired_infrastructure=True),unsafe_allow_html=True)
    st.divider()
    section('Training and preparedness','Activities completed in the last year and priorities for the next period.',
            eyebrow='04 / PEOPLE AND TRAINING')
    st.plotly_chart(viz.country_training(r,lang=chosen_language()),
                    use_container_width=True,config={'displayModeBar':False})
    st.divider()
    section('Reported experience','Original-language responses, without machine translation.',eyebrow='05 / INSTITUTIONAL NOTES')
    a,b=st.columns(2,gap='large')
    for col,key,title in ((a,'Reported strengths (original language)','Reported strengths'),
                          (b,'Improvement areas (original language)','Areas for improvement')):
        with col:
            with st.container(border=True):
                st.markdown('**'+T(title)+'**')
                st.write(r[key] or T('No narrative response provided.'))
    if r['Recent activations (original language)']:
        with st.expander(T('Recent events / activations · original response')):
            st.write(r['Recent activations (original language)'])
    skills=[name for name in COOPERATION_SKILLS.values() if pd.notna(r['Skill: '+name]) and bool(r['Skill: '+name])]
    modes=[name for name in COOPERATION_MODES.values() if pd.notna(r['Mode: '+name]) and bool(r['Mode: '+name])]
    if skills or modes:
        with st.expander(T('Technical capabilities and contributions this institution can offer')):
            st.markdown('**'+T('Expertise:')+'** '+(', '.join(map(T,skills)) if skills else T('Not reported')))
            st.markdown('**'+T('Modalities:')+'** '+(', '.join(map(T,modes)) if modes else T('Not reported')))
    note('Each institution has its own response. Colombia’s two institutions remain separate.')





def main():
    ui_style()
    try:
        records,raw=load_data()
    except Exception as ex:
        st.error(f'Unable to read the survey data: {ex}')
        st.stop()
    country=country_aggregate(records)
    with st.sidebar:
        st.radio('Language / Idioma',['en','es'],format_func=lambda v: 'English' if v=='en' else 'Español',
                 horizontal=True,key='coe_language')
        st.markdown(f'<div class="section-eyebrow">{esc(T("REGIONAL MONITORING"))}</div>',unsafe_allow_html=True)
        st.markdown('### '+T('EOC-S · Americas'))
        st.caption(T('PAHO/WHO survey 2026'))
        view=st.radio(T('Explore'), ['Regional overview','Country profiles'],format_func=lambda value, _lang=chosen_language(): tr(value, _lang),label_visibility='collapsed',key='main_view')
        st.divider()
        st.caption(f'2026 · {len(country)} {T("countries")} · {len(records)} {T("institutional responses")}')
    header()
    if view=='Regional overview':
        # As in the Cluster Salud VZLA v2 dashboard: main-content horizontal section navigation.
        # Keep stable English values in session state while showing labels in the selected language.
        tabscope=st.segmented_control(
            T('Regional section'),
            ['Overview','Capacities & gaps','Operations & hazards','Networks & cooperation'],
            default='Overview',
            selection_mode='single',
            format_func=lambda value, _lang=chosen_language(): tr(value, _lang),
            key='regional_section',
        ) or 'Overview'
        # Regional indicators always summarize all responding countries.
        active=country
        if tabscope=='Overview':regional_overview(country,active)
        elif tabscope=='Capacities & gaps':capacity_and_gaps(active)
        elif tabscope=='Operations & hazards':operations_section(active)
        else:cooperation_section(active)
    elif view=='Country profiles':country_profile(records,country)
    st.markdown('<div class="paho-footer">'+esc(T('PAHO / WHO · EOC-NET Americas · 2026  |  Self-reported information  |  Analytical dashboard for technical coordination'))+'</div>',unsafe_allow_html=True)

if __name__=='__main__':main()