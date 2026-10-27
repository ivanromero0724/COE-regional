"""PAHO/WHO | EOC-NET Americas 2026 — regional-to-country survey dashboard.

Deploy in Streamlit Community Cloud: repository COE-regional, main file app.py.
Data is bundled in data/ and refreshed by a GitHub/Streamlit Cloud redeploy.
"""
from __future__ import annotations
import base64
import html
import re
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
from dashboard.treemap import overview_treemap_html
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
    .kpi .kpi-count{display:inline-block;margin-left:12px;font-size:.82rem;font-weight:650;letter-spacing:0;color:#637D90;white-space:nowrap;vertical-align:baseline;}
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
    .eoc-capacity-section-title{font-size:.92rem;font-weight:800;color:#17324D;margin:17px 0 9px;}
    .eoc-capacity-chart-title{min-height:2.2em;max-height:2.8em;overflow:hidden;display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:2;line-height:1.35;font-size:.83rem;font-weight:800;color:#17324D;margin:1px 0 3px;}
    .eoc-capacity-chart-meta{font-size:.73rem;color:#607B8A;margin:-8px 0 3px;}
    /* The outer Streamlit chart card is the only frame in Capacities & gaps.
       Remove the generic Plotly frame nested inside each card. */
    /* Keep the Plotly chart frame; avoid stacking an outer card around it. */
    .st-key-capacity_visual_gallery [data-testid="stPlotlyChart"]{
        border:1px solid #DFE9F1!important;border-radius:12px!important;
        box-shadow:none!important;background:#FFFFFF!important;
    }


    /* Compact comparisons: align headings without stretching cards or bar spacing.
       Different-length datasets are allowed to finish at their natural height. */
    .eoc-pair-heading{min-height:0;margin:0 0 2px;box-sizing:border-box;}
    .card-panel.eoc-pair-overview,.card-panel.eoc-pair-cooperation{
        min-height:0;display:block;box-sizing:border-box;
    }
    /* Regional 03/04 are comparable treemaps: matching borders, equal
       heights, and a responsive natural wrap on narrow screens. */
    .eoc-overview-treemap-card{
        border:1px solid #DFE9F1;background:#FFF;border-radius:12px;
        padding:12px 13px 13px;margin:1px 0 8px;box-sizing:border-box;
        min-width:0;
    }
    .eoc-overview-treemap-plot{position:relative;width:100%;height:354px;}
    .eoc-overview-treemap-tile{position:absolute;padding:4px;box-sizing:border-box;min-width:0;}
    .eoc-overview-treemap-face{
        display:flex;flex-direction:column;justify-content:space-between;
        gap:10px;width:100%;height:100%;padding:13px;
        box-sizing:border-box;border-radius:7px;color:white;overflow:hidden;
    }
    .eoc-overview-treemap-label{
        color:white;font-size:.80rem;font-weight:760;line-height:1.25;
        overflow:hidden;overflow-wrap:anywhere;
        display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:4;
    }
    .eoc-overview-treemap-metric{
        color:white;font-size:1.35rem;line-height:1.05;font-weight:800;white-space:nowrap;
    }
    .eoc-overview-treemap-metric small{font-size:.73rem;line-height:1.2;font-weight:650;}
    @media(max-width:950px){
        .eoc-overview-treemap-plot{height:325px;}
        .eoc-overview-treemap-face{padding:8px;}
        .eoc-overview-treemap-label{font-size:.72rem;}
        .eoc-overview-treemap-metric{font-size:1.12rem;}
        .eoc-overview-treemap-metric small{font-size:.64rem;}
    }
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
    .measure-fill{display:block;height:100%;background:#009BDA;border-radius:999px;}
    .measure-value{font-size:.77rem;font-weight:800;color:#005A8B;text-align:right;white-space:nowrap;}
    /* The entire capacity bar is a keyboard-accessible native disclosure.
       Details open directly under the clicked row, without a sidebar or dropdown. */
    .eoc-capacity-disclosure{border-bottom:1px solid #EDF2F6;}
    .eoc-capacity-disclosure:last-child{border-bottom:0;}
    .eoc-capacity-summary{
        display:grid;
        grid-template-columns:minmax(0,1.35fr) minmax(65px,1fr) 116px 16px;
        gap:10px;min-height:42px;padding:8px 4px;
        align-items:center;cursor:pointer;list-style:none;border-radius:7px;
    }
    .eoc-capacity-full .eoc-capacity-summary{
        grid-template-columns:minmax(0,1fr) minmax(160px,1.9fr) 128px 20px;
        gap:16px;min-height:45px;padding:9px 5px;
    }
    .eoc-capacity-summary::-webkit-details-marker{display:none;}
    .eoc-capacity-summary:hover{background:#F0F7FB;}
    .eoc-capacity-summary:focus-visible{
        outline:2px solid #009BDA;outline-offset:2px;
    }
    .eoc-capacity-full .eoc-capacity-summary .measure-label{font-size:.82rem;}
    .eoc-capacity-chevron{
        display:inline-block;width:8px;height:8px;
        border-right:2px solid #005A8B;border-bottom:2px solid #005A8B;
        transform:rotate(45deg);transition:transform .15s ease;justify-self:center;
    }
    .eoc-capacity-disclosure[open] .eoc-capacity-chevron{transform:rotate(225deg);}
    .eoc-capacity-detail{
        background:#F8FBFD;border:1px solid #E2ECF3;border-radius:10px;
        padding:14px 15px;margin:2px 0 12px;
    }
    .eoc-capacity-detail-title{
        color:#005A8B;font-size:.79rem;font-weight:800;margin:0 0 12px;
    }
    /* Country status grid fits all responding countries without an inner scrollbar. */
    .eoc-country-capacity-panel{
        border:1px solid #DFE9F1;border-radius:12px;
        background:#FFF;padding:17px 18px;min-width:0;
    }
    .eoc-country-capacity-grid{
        display:grid;grid-template-columns:repeat(3,minmax(0,1fr));
        gap:10px 14px;
    }
    .eoc-country-capacity-item{
        display:flex;align-items:center;justify-content:space-between;
        flex-wrap:wrap;gap:8px 12px;min-width:0;
        background:#F7FAFC;border:1px solid #E8F0F5;
        border-radius:9px;padding:10px 12px;
    }
    .eoc-country-capacity-name{
        font-size:.81rem;font-weight:700;line-height:1.35;color:#29485F;
        overflow-wrap:anywhere;
    }
    .eoc-country-category-grid{
        display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px 12px;
    }
    .eoc-country-category-item{
        font-size:.81rem;font-weight:700;color:#29485F;
        background:#F7FAFC;border:1px solid #E8F0F5;
        border-radius:9px;padding:10px 12px;overflow-wrap:anywhere;
    }
    .eoc-operations-card:has(.eoc-capacity-disclosure[open]){
        height:auto;overflow:visible;
    }
    .eoc-training-group-title{
        font-size:.82rem;font-weight:800;color:#005A8B;margin:15px 0 3px;
        padding:6px 4px;background:#F1F7FA;border-radius:6px;
    }
    .eoc-training-group-title:first-of-type{margin-top:4px;}
    .network-grid{align-items:start;}
    /* Network summary cards stay static. The country-level breakdown is the
       separate categorical matrix below, not three accordion panels. */
    /* One matching legend and matrix vocabulary: colored symbols, no solid fills. */
    .eoc-network-legend{display:flex;gap:10px 23px;flex-wrap:wrap;
        align-items:center;margin:10px 0 11px;font-size:.80rem;color:#45667A;}
    .eoc-network-legend-item{display:inline-flex;gap:8px;align-items:center;}
    .eoc-network-legend-symbol,.eoc-network-heat-symbol{
        display:inline-block;font-family:Arial,sans-serif;font-weight:800;
        line-height:1;text-align:center;
    }
    .eoc-network-legend-symbol{font-size:1.08rem;min-width:19px;}
    .eoc-network-heat-symbol{font-size:1.38rem;}
    .eoc-network-legend-symbol[data-status="Participating"],
    .eoc-network-heat-symbol[data-status="Participating"]{color:#005A8B;}
    .eoc-network-legend-symbol[data-status="Interested"],
    .eoc-network-heat-symbol[data-status="Interested"]{color:#009BDA;}
    .eoc-network-legend-symbol[data-status="Not participating"],
    .eoc-network-heat-symbol[data-status="Not participating"]{color:#F36B32;}
    .eoc-network-legend-symbol[data-status="Not reported"],
    .eoc-network-heat-symbol[data-status="Not reported"]{color:#7B8D9B;}
    /* A quiet, border-matched HTML matrix rather than saturated badge tiles. */
    .eoc-network-matrix-wrap{
        border:1px solid #DFE9F1;border-radius:12px;background:#FFFFFF;
        padding:12px 18px;overflow-x:auto;box-sizing:border-box;
    }
    .eoc-network-matrix{width:100%;border-collapse:collapse;
        min-width:510px;table-layout:fixed;}
    .eoc-network-matrix th{
        padding:11px 10px;color:#005A8B;font-size:.80rem;
        text-align:center;font-weight:800;background:#F5F9FC;
        border-bottom:1px solid #DFE9F1;
    }
    .eoc-network-matrix th:first-child{text-align:left;width:28%;}
    .eoc-network-matrix td{padding:0;vertical-align:middle;
        border-bottom:1px solid #EBF0F4;}
    /* Keep the bottom separator on the final country (Saint Lucia),
       matching every other matrix row. */
    .eoc-network-matrix .eoc-network-country{
        font-size:.81rem;font-weight:700;color:#29485F;
        padding:8px 10px;background:#FFFFFF;text-align:left;
        border-bottom:1px solid #EBF0F4;
    }
    .eoc-network-heat-cell{
        display:flex;align-items:center;justify-content:center;
        min-height:31px;padding:4px 8px;background:transparent;
    }
    .eoc-network-heat-cell:focus-visible{
        outline:2px solid #009BDA;outline-offset:-2px;border-radius:5px;
    }
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
    .status-interest{background:#E5F5FD;color:#006C9A;}
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
    @media(max-width:1150px){.kpi-grid{grid-template-columns:repeat(3,minmax(0,1fr));}.kpi-grid.four{grid-template-columns:repeat(2,minmax(0,1fr));}.eoc-country-capacity-grid,.eoc-country-category-grid{grid-template-columns:repeat(2,minmax(0,1fr));}}
    @media(max-width:900px){.eoc-pair-heading{margin-bottom:0;}
        .card-panel.eoc-pair-overview.eoc-operations-card{height:auto;overflow:visible;}
        .card-panel.eoc-pair-capacities{min-height:0;}}
    @media(max-width:760px){.eoc-country-capacity-grid,.eoc-country-category-grid{grid-template-columns:1fr;}.eoc-capacity-summary{grid-template-columns:minmax(0,1fr) 105px 16px;gap:7px;}.eoc-capacity-summary .measure-label{grid-column:1/-1;}.eoc-capacity-summary .measure-bar{grid-column:1;}.eoc-capacity-summary .measure-value{grid-column:2;}.eoc-capacity-summary .eoc-capacity-chevron{grid-column:3;}.eoc-capacity-full .eoc-capacity-summary{grid-template-columns:minmax(0,1fr) 105px 16px;gap:7px;}.eoc-capacity-full .eoc-capacity-summary .measure-label{grid-column:1/-1;}.eoc-capacity-full .eoc-capacity-summary .measure-bar{grid-column:1;}.eoc-capacity-full .eoc-capacity-summary .measure-value{grid-column:2;}.eoc-capacity-full .eoc-capacity-summary .eoc-capacity-chevron{grid-column:3;}[data-testid="stMainBlockContainer"],.block-container{padding-top:2.75rem;}.measure-row{grid-template-columns:minmax(0,1fr) 115px;row-gap:6px;gap:7px;}.measure-label{grid-column:1 / -1;overflow-wrap:normal;font-size:.74rem;}.measure-bar{grid-column:1;}.measure-value{grid-column:2;}.dist-row{grid-template-columns:minmax(0,1fr) 80px 112px;gap:6px;}.block-container{padding-left:1rem;padding-right:1rem;}.paho-hero{grid-template-columns:1fr;padding:17px;row-gap:14px;}.brand-set{max-width:360px;}.kpi-grid,.kpi-grid.four{grid-template-columns:repeat(2,minmax(0,1fr));}.network-grid{grid-template-columns:1fr;}.status-tile-grid{grid-template-columns:1fr;}.card-panel{padding:13px;}}
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
    'Documented formal mandate':'<path d="M8 3h8l4 4v14H4V3h4z"/><path d="M16 3v5h4M8 13h8M8 17h8"/>',
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
        matched=re.fullmatch(r'(\d+(?:\.\d+)?%) \((\d+/\d+)\)', display)
        pretty=(f'{esc(matched.group(1))} <span class="kpi-count">({esc(matched.group(2))})</span>'
                if matched else esc(T(display)))
        long=' long' if len(display)>12 and not matched else ''
        tone=' accent' if label.lower().startswith(('in implementation','activation')) else ''
        svg='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'+KPI_ICON_PATHS.get(label,fallback)+'</svg>'
        items.append(f'<div class="kpi{tone}"><div class="kpi-label">{esc(T(label))}</div>'
                     f'<div class="kpi-icon" aria-hidden="true">{svg}</div>'
                     f'<div class="kpi-value{long}">{pretty}</div></div>')
    style=' four' if columns==4 else ''
    st.markdown(f'<div class="kpi-grid{style}">{"".join(items)}</div>',unsafe_allow_html=True)


def country_names_grid(names):
    """Only countries in the chosen response category; no misleading in-place labels."""
    return '<div class="eoc-country-category-grid">'+''.join(
        '<div class="eoc-country-category-item">'+esc(T(name))+'</div>'
        for name in sorted(names)
    )+'</div>'


def countries_capacity_grid(rows):
    """Responsive country-level status tiles including nonresponse."""
    return '<div class="eoc-country-capacity-grid">'+''.join(
        '<div class="eoc-country-capacity-item">'
        +'<span class="eoc-country-capacity-name">'+esc(T(name))+'</span>'
        +status_chip(value)+'</div>'
        for name,value in rows
    )+'</div>'


def disclosure_bar(label,numerator,denominator,rows=None,color=CYAN,category=False):
    """One keyboard-accessible clickable bar; expands correct country-level data."""
    n=int(numerator);d=int(denominator)
    pct=100*n/d if d else 0
    metric=f'{pct:.0f}% ({n}/{d})' if d else T('No valid responses')
    if rows is None:
        # No drilldown is offered when the underlying country field is unavailable.
        return (f'<div class="measure-row"><div class="measure-label">{esc(T(label))}</div>'
                f'<div class="measure-bar"><span class="measure-fill" style="width:{pct:.1f}%;background:{color}"></span></div>'
                f'<div class="measure-value">{esc(metric)}</div></div>')
    detail=(country_names_grid(rows) if category else countries_capacity_grid(rows))
    detail_title=T('Countries in this category') if category else T('Countries reporting each capacity')
    return (
        '<details class="eoc-capacity-disclosure">'
        '<summary class="eoc-capacity-summary">'
        '<span class="measure-label">'+esc(T(label))+'</span>'
        '<span class="measure-bar"><span class="measure-fill" style="width:'
        +f'{pct:.1f}%;background:{color}"></span></span>'
        '<span class="measure-value">'+esc(metric)+'</span>'
        '<span class="eoc-capacity-chevron" aria-hidden="true"></span>'
        '</summary><div class="eoc-capacity-detail">'
        '<div class="eoc-capacity-detail-title">'+esc(detail_title)+'</div>'
        +detail+'</div></details>'
    )


def regional_indicator_rows(active,item):
    """Resolve the exact country-level field used in each regional numerator."""
    field=item.get('status_col')
    if isinstance(field,str) and field in active.columns:
        return [(r.country,r[field] if pd.notna(r[field]) else None)
                for _,r in active.sort_values('country').iterrows()]
    col=item.get('col')
    if col is not None and pd.notna(col) and (int(col)>=0 or int(col)==-2):
        col=int(col)
        valid=item.get('positive')
        if valid is None or not isinstance(valid,tuple):
            valid=next((codes for items in CAPACITIES.values()
                        for name,ix,codes in items
                        if ix==col and name==item['capacity']),None)
        if valid is not None:
            return [(r.country,country_capacity(r,col,valid))
                    for _,r in active.sort_values('country').iterrows()]
    if item.get('component')=='Infrastructure':
        field=item['capacity']
    elif item.get('component')=='Training (completed)':
        field='Completed: '+item['capacity']
    else:
        return None
    if field not in active.columns:return None
    return [(r.country,r[field] if pd.notna(r[field]) else None)
            for _,r in active.sort_values('country').iterrows()]


def capacity_rows_html(frame,title=None,pair=None,variant=None,country=None):
    """Regional percentage bars: click for the source countries when available."""
    contents=[]
    for _,r in frame.iterrows():
        rows=regional_indicator_rows(country,r) if country is not None else None
        contents.append(disclosure_bar(r['capacity'],r['in_place'],r['denominator'],rows))
    h=f'<div class="card-title">{esc(T(title))}</div>' if title else ''
    pair_class=f' eoc-pair-{pair}' if pair=='cooperation' else ''
    variant_class=' eoc-capacity-full' if variant=='full' else ''
    return f'<div class="card-panel{pair_class}{variant_class}">{"".join([h]+contents)}</div>'


def capacity_response_distribution(active, indicator):
    """One country per answer; preserve original choice wording."""
    field=f"ANSWER_{int(indicator['col'])}"
    if field not in active.columns:
        return pd.Series(dtype=int)
    counts={}
    for response in active[field].dropna():
        label=re.sub(r'^[a-zA-Z]\.\s+', '', str(response).strip()).strip()
        if not label:
            continue
        # Preserve exact response text rather than collapsing intermediate states.
        counts[label]=counts.get(label,0)+1
    return pd.Series(counts,dtype=int).sort_values(ascending=False)


def capacity_chart(indicator, counts, chart_kind):
    """Compact PAHO-style charts; full questionnaire responses on hover."""
    import plotly.graph_objects as go
    colors=['#005A8B','#009BDA','#75B8D6','#F36B32','#8DA9B9','#D9E4EC']
    total=int(counts.sum())
    labels=list(counts.index)
    values=[int(v) for v in counts.values]
    pct=[100*v/total for v in values]
    def short_label(label,limit=27):
        label=str(label).strip()
        return label if len(label)<=limit else label[:limit-1].rstrip()+'…'
    shorter=[short_label(x) for x in labels]
    fig=go.Figure()
    if chart_kind=='donut':
        fig.add_trace(go.Pie(
            labels=shorter,values=values,customdata=labels,hole=.68,sort=False,
            marker=dict(colors=colors),
            textinfo='percent',textposition='inside',
            textfont=dict(size=11,color='white'),
            hovertemplate='<b>%{customdata}</b><br>%{percent} (%{value}/'+str(total)+')<extra></extra>'))
        fig.add_annotation(x=.5,y=.5,text='<b>'+str(total)+'</b>',
                           font=dict(size=23,color='#005A8B'),showarrow=False)
        fig.update_layout(showlegend=True,legend=dict(
            orientation='h',x=0,y=-.11,font=dict(size=10),itemsizing='constant'))
    elif chart_kind=='treemap':
        fig.add_trace(go.Treemap(
            labels=shorter,parents=['']*len(values),values=values,
            customdata=labels,
            marker=dict(colors=colors,line=dict(color='white',width=2)),
            texttemplate='%{label}<br>%{percentRoot:.0%}',
            textfont=dict(size=11),
            hovertemplate='<b>%{customdata}</b><br>%{percentRoot:.0%} (%{value}/'+str(total)+')<extra></extra>',
            tiling=dict(pad=3),
            branchvalues='total'))
        fig.update_layout(showlegend=False)
    else:
        order=list(reversed(range(len(values))))
        fig.add_trace(go.Bar(
            y=[short_label(labels[i],24) for i in order],
            x=[pct[i] for i in order],orientation='h',
            marker_color=[colors[i%len(colors)] for i in order],
            customdata=[[labels[i],values[i]] for i in order],
            text=[f'{pct[i]:.0f}%' for i in order],textposition='outside',
            hovertemplate='<b>%{customdata[0]}</b><br>%{x:.0f}% (%{customdata[1]}/'+str(total)+')<extra></extra>'))
        fig.update_xaxes(range=[0,115],visible=False,fixedrange=True)
        fig.update_yaxes(automargin=True,fixedrange=True,tickfont_size=10)
        fig.update_layout(showlegend=False)
    fig.update_layout(
        height=250,margin=dict(l=8,r=12,t=14,b=50 if chart_kind=='donut' else 12),
        paper_bgcolor='white',plot_bgcolor='white',
        font=dict(family='Arial, sans-serif',color='#17324D',size=11),
        hoverlabel=dict(bgcolor='white',font_size=11),
        dragmode=False)
    return fig


def capacity_visual_dashboard(frame, active):
    """Visual hierarchy consistent with the existing PAHO regional panels."""
    import plotly.graph_objects as go
    valid=frame[frame.denominator>0].copy()
    if not valid.empty:
        valid['percentage']=100*valid.in_place/valid.denominator
        labels=[T(x) for x in valid.capacity]
        concise=[x if len(x)<=33 else x[:32].rstrip()+'…' for x in labels]
        fig=go.Figure(go.Bar(
            y=concise[::-1],x=valid.percentage.to_list()[::-1],orientation='h',
            customdata=[[labels[i],int(valid.in_place.iloc[i]),int(valid.denominator.iloc[i])]
                        for i in range(len(valid))][::-1],
            marker_color='#009BDA',
            text=[f'{p:.0f}%' for p in valid.percentage][::-1],
            textposition='outside',cliponaxis=False,
            hovertemplate='<b>%{customdata[0]}</b><br>%{x:.0f}% (%{customdata[1]}/%{customdata[2]})<extra></extra>'))
        fig.update_layout(
            height=max(275,len(valid)*35+50),
            margin=dict(l=10,r=44,t=14,b=12),paper_bgcolor='white',
            plot_bgcolor='white',font=dict(family='Arial, sans-serif',size=11,color='#17324D'),
            hoverlabel=dict(bgcolor='white',font_size=11))
        fig.update_xaxes(range=[0,110],visible=False,fixedrange=True)
        fig.update_yaxes(automargin=True,fixedrange=True,tickfont_size=10)
        st.markdown('<div class="eoc-capacity-section-title">'+T('Capacity availability')+'</div>',unsafe_allow_html=True)
        st.plotly_chart(fig,use_container_width=True,config={'displayModeBar':False})
    st.markdown('<div class="eoc-capacity-section-title">'+
                ('Distribución de respuestas' if chosen_language()=='es' else 'Response distribution')+
                '</div>',unsafe_allow_html=True)
    columns=st.columns(2,gap='medium')
    for i,(_,indicator) in enumerate(frame.iterrows()):
        counts=capacity_response_distribution(active,indicator)
        with columns[i%2]:
            title=T(indicator['capacity'])
            st.markdown('<div class="eoc-capacity-chart-title" title="'+esc(title)+'">'+esc(title)+'</div>',
                        unsafe_allow_html=True)
            if counts.empty:
                st.caption(T('No valid responses'))
                continue
            kind=('donut','bar','treemap')[i%3]
            st.plotly_chart(capacity_chart(indicator,counts,kind),
                            use_container_width=True,config={'displayModeBar':False})
            st.markdown('<div class="eoc-capacity-chart-meta">'+str(int(counts.sum()))+' '+
                        ('respuestas válidas' if chosen_language()=='es' else 'valid responses')+
                        '</div>',unsafe_allow_html=True)


def distribution_html(series,title,ordered,color,active=None,field=None):
    """Categorical bars open only countries with that exact response category."""
    total=int(series.isin(ordered).sum())
    entries=[]
    for label in ordered:
        n=int((series==label).sum())
        if not n:continue
        rows=(active.loc[active[field]==label,'country'].tolist()
              if active is not None and field in active.columns else None)
        entries.append(disclosure_bar(label,n,total,rows,color=color,category=True))
    return f'<div class="mini-title">{esc(T(title))}</div>{"".join(entries)}'


def training_drilldown_html(active):
    """Two separately expandable percentages per course, with their own denominators."""
    items=[]
    for course in TRAINING_LABELS:
        items.append('<div class="eoc-training-group-title">'+esc(T(course))+'</div>')
        for state,prefix,color in [('Completed','Completed: ',BLUE),
                                    ('Prioritized','Priority: ',CYAN)]:
            valid=active[prefix+course].dropna()
            rows=[(r.country,r[prefix+course] if pd.notna(r[prefix+course]) else None)
                  for _,r in active.sort_values('country').iterrows()]
            items.append(disclosure_bar(state,sum(v is True or v==True for v in valid),
                                        len(valid),rows,color=color))
    return '<div class="card-panel eoc-training-bars">'+''.join(items)+'</div>'


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
    total=len(country)
    def share(n,denominator=total):
        return f'{100*n/denominator:.0f}% ({n}/{denominator})' if denominator else '— (0/0)'
    documented=country.formal_document.dropna()
    documented_yes=int((documented==True).sum())
    kpi_grid([
        ('Countries responding',total),
        ('Established EOC-S',share(int((country.eoc_status=='Established').sum()))),
        ('In implementation',share(int((country.eoc_status=='In implementation').sum()))),
        ('24/7 operation',share(int((country.operating_mode=='24/7 continuous').sum()))),
        ('Documented formal mandate',share(documented_yes,len(documented)))])


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
            # Keep the Americas at the designed extent: no drag, wheel zoom or
            # double-click zoom. Country hover labels remain available.
            st.plotly_chart(
                fig, width='stretch',
                config={'displayModeBar':False, 'scrollZoom':False,
                        'doubleClick':False, 'staticPlot':False},
            )


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
                    distribution_html(active.operating_mode,'Operating mode',modes,BLUE,active,'operating_mode')+
                    distribution_html(active.activation,'Activation after formal decision',times,CYAN,active,'activation')+
                    '</div>',unsafe_allow_html=True)
    st.divider()
    # Two compact, region-level treemaps. No country drilldowns in Overview;
    # all detailed capacity/status exploration remains in Capacities & gaps.
    strengths=capacity_table(active)
    strengths=strengths[strengths.component.isin(CAPACITIES)]
    strengths=(strengths[strengths.denominator>0]
               .sort_values(['in_place','capacity'],ascending=[False,True]).head(7))
    priorities=[('Sustainable financing',36,('d','e')),
                ('Formal surge staffing',77,('d','e')),
                ('Updated surge roster',78,('a',)),
                ('Integrated information tools',107,('d','e')),
                ('Structured information exchange',105,('d',))]
    gap_rows=[]
    for label,col,positive in priorities:
        valid=[country_capacity(row,col,positive) for _,row in active.iterrows()]
        gap_rows.append({
            'capacity':label,
            'in_place':sum(value is True for value in valid),
            'denominator':sum(value is not None for value in valid),
        })
    left,right=st.columns(2,gap='large')
    with left:
        section('Most widely reported capacities',
                'Countries reporting an established or functional capacity.',
                eyebrow='03 / REPORTED CAPACITIES',paired=True)
        st.markdown(overview_treemap_html(strengths,'available',lang=chosen_language()),
                    unsafe_allow_html=True)
    with right:
        section('Priority capacity gaps',
                'Countries where each capacity is not yet fully established.',
                eyebrow='04 / COOPERATION PRIORITIES',paired=True)
        st.markdown(overview_treemap_html(pd.DataFrame(gap_rows),'gap',lang=chosen_language()),
                    unsafe_allow_html=True)


def capacity_and_gaps(active):
    section('Core capacities reported as in place',
            'Country counts reflect only recognized answers to each survey item.',
            eyebrow='01 / CAPACITY PROFILES')
    caps=capacity_table(active)
    component=st.selectbox(T('Explore a component'),list(CAPACITIES.keys()),
                           format_func=lambda value, _lang=chosen_language(): tr(value, _lang),
                           key='capacity_component')
    sliced=caps[caps.component==component]
    # Full categorical distributions; click each answer category to see countries.
    with st.container(border=False,key="capacity_visual_gallery"):
        capacity_visual_dashboard(sliced,active)
    note('Each country is counted once; categories reproduce survey responses. Where several institutions answered, the country response is consolidated.')

def operations_section(active):
    section('Hazards coordinated during the past two years',
            'Categories reflect ordinal frequency bands, not exact event counts.',
            eyebrow='01 / TYPES OF EMERGENCIES')
    st.plotly_chart(viz.hazard_heatmap(active.sort_values('country'),lang=chosen_language()),
                    use_container_width=True,config={'displayModeBar':False})
    st.divider()
    section('Training completed and prioritized','Each country counted once per course.',eyebrow='02 / WORKFORCE DEVELOPMENT')
    st.markdown(training_drilldown_html(active),unsafe_allow_html=True)



NETWORK_STATUS_SYMBOLS={
    'Participating':'✓','Interested':'◐',
    'Not participating':'×','Not reported':'—',
}


def network_heatmap_html(active):
    """Compact, accessible network matrix with icon-only categorical cells.

    Each icon matches the legend and preserves the self-reported country response
    in its tooltip and screen-reader label.
    """
    allowed=NETWORK_STATUS_SYMBOLS
    names=list(NETWORK_NAMES.values())
    head='<thead><tr><th scope="col">'+esc(T('Country'))+'</th>'+''.join(
        '<th scope="col">'+esc(T(name))+'</th>' for name in names
    )+'</tr></thead>'
    rows=[]
    for _,record in active.sort_values('country').iterrows():
        name=str(record['country'])
        cells=[]
        for network in names:
            raw=record[network]
            status=raw if isinstance(raw,str) and raw in allowed else 'Not reported'
            tooltip=esc(T(name)+' · '+T(network)+': '+T(status))
            cells.append(
                '<td><span class="eoc-network-heat-cell" data-status="'
                +esc(status)+'" title="'+tooltip+'" tabindex="0" aria-label="'
                +tooltip+'"><span class="eoc-network-heat-symbol" data-status="'
                +esc(status)+'" aria-hidden="true">'
                +allowed[status]+'</span></span></td>'
            )
        rows.append('<tr><th scope="row" class="eoc-network-country">'
                    +esc(T(name))+'</th>'+''.join(cells)+'</tr>')
    return ('<div class="eoc-network-matrix-wrap">'
            '<table class="eoc-network-matrix">'+head+
            '<tbody>'+''.join(rows)+'</tbody></table></div>')


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
        cards.append(
            '<div class="network-card">'
            f'<div class="network-name">{esc(T(name))}</div>'
            f'<div class="network-count">{primary_pct:.0f}% '
            f'<span style="font-size:.82rem;color:#688193">({participating}/{answered})</span></div>'
            +bar+
            f'<div class="network-meta">{esc(T("Participating"))} {participating}/{answered} · '
            f'{esc(T("Interested"))} {interested}/{answered} · '
            f'{esc(T("Not participating"))} {inactive}/{answered}</div>'
            '</div>'
        )
    st.markdown('<div class="network-grid">'+''.join(cards)+'</div>',unsafe_allow_html=True)
    # One full-width categorical matrix for all three networks and all countries.
    st.markdown('<div class="mini-title">'+esc(T('Country participation by network'))+'</div>',
                unsafe_allow_html=True)
    legend=''.join(
        '<span class="eoc-network-legend-item">'
        '<span class="eoc-network-legend-symbol" data-status="'
        +esc(status)+'" aria-hidden="true">'
        +symbol+'</span>'+esc(T(status))+'</span>'
        for status,symbol in NETWORK_STATUS_SYMBOLS.items()
    )
    st.markdown('<div class="eoc-network-legend">'+legend+'</div>',
                unsafe_allow_html=True)
    st.markdown(network_heatmap_html(active),unsafe_allow_html=True)
    st.divider()
    a,b=st.columns(2,gap='large')
    with a:
        section('Expertise countries can share','Technical expertise reported for cooperation.',
                eyebrow='02 / CAPACITIES OFFERED',paired=True)
        entries=[]
        for name in COOPERATION_SKILLS.values():
            answered=active['Skill: '+name].dropna()
            entries.append({'capacity':name,'in_place':sum(bool(x) for x in answered),
                            'denominator':len(answered),'status_col':'Skill: '+name})
        ranked=pd.DataFrame(entries).sort_values('in_place',ascending=False).head(9)
        st.markdown(capacity_rows_html(ranked,pair='cooperation',country=active),unsafe_allow_html=True)
    with b:
        section('How countries can cooperate','Reported modalities of technical collaboration.',
                eyebrow='03 / MODALITIES',paired=True)
        entries=[]
        for name in COOPERATION_MODES.values():
            answered=active['Mode: '+name].dropna()
            entries.append({'capacity':name,'in_place':sum(bool(x) for x in answered),
                            'denominator':len(answered),'status_col':'Mode: '+name})
        ranked=pd.DataFrame(entries).sort_values('in_place',ascending=False)
        st.markdown(capacity_rows_html(ranked,pair='cooperation',country=active),unsafe_allow_html=True)
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