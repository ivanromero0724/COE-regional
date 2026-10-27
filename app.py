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
  capacity_table, country_capacity, safe_csv
)
from dashboard import charts as viz

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
    [data-testid="stHeader"] {background:rgba(247,250,252,.93);}
    [data-testid="stSidebar"] {background:#FFFFFF;border-right:1px solid #E1EAF1;}
    [data-testid="stSidebar"] [data-testid="stImage"] {margin-bottom:8px;}
    .block-container {padding-top:1.2rem;padding-bottom:2.4rem; max-width:1600px;}
    h1,h2,h3,h4{color:#005A8B;font-weight:800;letter-spacing:-.035em;}
    h2{font-size:1.42rem!important;}
    h3{font-size:1.06rem!important;}
    [data-testid="stVerticalBlockBorderWrapper"] > div {border-color:#DFE9F1!important;
      background:#FFFFFF; border-radius:14px!important;}
    [data-testid="stMetric"] {background:#FFF;border:1px solid #E1EAF1;
      border-radius:13px;padding:15px 15px 13px;}
    [data-testid="stMetricLabel"]{font-size:.78rem!important;color:#597184;}
    [data-testid="stMetricValue"]{color:#005A8B;font-size:1.8rem!important;font-weight:800;}
    .paho-strip{height:7px;background:linear-gradient(90deg,#005A8B 0%,#005A8B 72%,#F36B32 72%,#F36B32 100%);border-radius:8px 8px 0 0}
    .paho-header{background:white;border:1px solid #E1EAF1;border-radius:13px;
      margin-bottom:22px;overflow:hidden;box-shadow:0 4px 20px rgba(25,75,110,.035);}
    .paho-hero{padding:20px 26px 22px;display:flex;align-items:center;justify-content:space-between;gap:24px;flex-wrap:wrap;}
    .paho-eyebrow{font-size:.72rem;letter-spacing:.15em;font-weight:800;color:#F36B32;}
    .paho-title{font-size:clamp(1.4rem,2.1vw,2.3rem);font-weight:800;line-height:1.13;letter-spacing:-.045em;color:#005A8B;margin:4px 0 6px;}
    .paho-desc{font-size:.87rem;color:#62798C;max-width:720px;}
    .brand-set{display:flex;align-items:center;gap:21px;flex-shrink:0;}
    .brand-set img{object-fit:contain;max-width:150px;max-height:58px;}
    .section-eyebrow{font-size:.72rem;letter-spacing:.14em;font-weight:800;color:#008CBF;margin:14px 0 6px;}
    .section-title{font-size:1.25rem;font-weight:800;letter-spacing:-.02em;color:#005A8B;margin:0 0 6px;}
    .section-desc{font-size:.8rem;color:#657A8A;margin-bottom:14px;}
    .small-note{color:#667D8D;font-size:.73rem;line-height:1.6;}
    .eoc-note{background:#FFF8F2;border-left:3px solid #F36B32;padding:12px 14px;
      color:#6C5A4C;font-size:.78rem;border-radius:6px;line-height:1.55;}
    .badge{display:inline-block;font-size:.71rem;font-weight:700;color:#005A8B;
      background:#E9F3FA;border:1px solid #CFE5F2;border-radius:999px;padding:5px 11px;margin:3px 4px 3px 0;}
    .bigcountry{font-size:2rem;line-height:1.1;color:#005A8B;font-weight:800;}
    .subtle-label{font-size:.69rem;letter-spacing:.1em;text-transform:uppercase;font-weight:700;color:#678197;}
    .priority-pill{display:flex;gap:10px;align-items:flex-start;padding:13px 15px;background:#FFF;
       border:1px solid #E3EAF0;border-top:3px solid #F36B32;border-radius:9px;margin:8px 0;}
    .priority-pill strong{color:#005A8B;font-size:.83rem;}
    .pill-num{font-size:1.3rem;color:#F36B32;font-weight:800;}
    .paho-footer{font-size:.73rem;color:#718594;margin-top:22px;border-top:1px solid #DCE8F0;padding:12px 2px;}
    [data-testid="stPlotlyChart"]{background:#FFF;border-radius:8px;}
    div.stButton>button[kind="primary"]{background:#005A8B!important;border-color:#005A8B!important;}
    </style>''',unsafe_allow_html=True)


def header():
    eoc=img64(ROOT/'logos/logo_EOC.png');paho=img64(ROOT/'logos/PAHO_eng.png')
    content=f'<img src="data:image/png;base64,{eoc}" alt="EOC-NET"/><img src="data:image/png;base64,{paho}" alt="PAHO/WHO"/>'
    st.markdown(f'''<div class="paho-header"><div class="paho-strip"></div><div class="paho-hero">
       <div><div class="paho-eyebrow">EOC-NET / THE AMERICAS · 2026</div>
       <div class="paho-title">Health Emergency Operations Centres</div>
       <div class="paho-desc">Regional survey dashboard · Institutional preparedness, operational capacities and cooperation</div></div>
       <div class="brand-set">{content}</div></div></div>''',unsafe_allow_html=True)


def section(title,subtitle='',eyebrow=None):
    if eyebrow:st.markdown(f'<div class="section-eyebrow">{esc(eyebrow)}</div>',unsafe_allow_html=True)
    st.markdown(f'<div class="section-title">{esc(title)}</div>',unsafe_allow_html=True)
    if subtitle:st.markdown(f'<div class="section-desc">{esc(subtitle)}</div>',unsafe_allow_html=True)


def note(msg):st.markdown(f'<div class="small-note">{esc(msg)}</div>',unsafe_allow_html=True)


def count_kpis(country):
    operational=int((country.eoc_status=='Established').sum())
    fast=int((country.activation=='Under 2 hours').sum())
    c1,c2,c3,c4,c5=st.columns(5,gap='small')
    c1.metric('Countries responding',len(country),help='Countries with at least one survey submission; not every country in the Americas responded.')
    c2.metric('Established EOC-S',operational,help='Country has at least one institutional response reporting an established EOC-S.')
    c3.metric('In implementation',int((country.eoc_status=='In implementation').sum()))
    c4.metric('24/7 operation',int((country.operating_mode=='24/7 continuous').sum()))
    c5.metric('Activation <2 hours',fast)


def country_metric_values(country):
    caps=capacity_table(country)
    return caps


def coverage_map(country,selected):
    try: fig=viz.countries_map(country,selected)
    except Exception as e:
        st.error('The geographic layer could not be read. Check data/geografia/paises_americas.gpkg.');return
    if fig is None:
        st.info('Map file not found. The Americas GeoPackage is expected in data/geografia/paises_americas.gpkg.')
    else:st.plotly_chart(fig,use_container_width=True,config={'displayModeBar':False})


def regional_overview(country,active):
    count_kpis(active)
    st.write('')
    col_map,col_summary=st.columns([1.35,1],gap='large')
    with col_map:
        section('Where have countries responded?',
                'Country-level survey coverage. Countries without a response remain visible in gray.',eyebrow='01 / REGIONAL COVERAGE')
        coverage_map(country,set(active.country))
    with col_summary:
        section('Operating arrangements','Country counted once. For multiple responses, the strongest reported arrangement is displayed.',eyebrow='02 / OPERATING MODE')
        st.plotly_chart(viz.operating_chart(active),use_container_width=True,config={'displayModeBar':False})
        st.markdown('**Activation time after formal decision**')
        st.plotly_chart(viz.activation_chart(active),use_container_width=True,config={'displayModeBar':False})
    st.divider()
    cols=st.columns([1.02,1],gap='large')
    with cols[0]:
        section('Most widely reported capacities',
                'Number of countries explicitly reporting each established or functional capacity.',
                eyebrow='03 / REPORTED CAPACITIES')
        ranked=capacity_table(active)
        ranked=ranked[ranked.component.isin(CAPACITIES)]
        ranked=ranked[ranked.denominator>0].sort_values(['in_place','capacity'],ascending=[False,True]).head(7)
        st.plotly_chart(viz.horizontal_bars(ranked,height=365),use_container_width=True,config={'displayModeBar':False})
    with cols[1]:
        section('Priority capacity gaps','Countries reporting these specific capacities as established / in place.',eyebrow='04 / COOPERATION PRIORITIES')
        priorities=[('Sustainable financing',36,('d','e')),
                    ('Formal surge staffing',77,('d','e')),
                    ('Updated surge roster',78,('a',)),
                    ('Integrated information tools',107,('d','e')),
                    ('Structured information exchange',105,('d',))]
        for label,col,yes in priorities:
            vals=[country_capacity(s,col,yes) for _,s in active.iterrows()]
            denominator=sum(v is not None for v in vals)
            number=sum(bool(v) for v in vals)
            x=round(100*number/denominator) if denominator else 0
            st.markdown(f'**{label}**  ·  {number}/{denominator} countries')
            st.progress(x/100 if denominator else 0)
        note('Only fully established / explicitly positive options count as “in place”. Partial, informal and developing responses do not.')
    st.markdown('<div class="eoc-note">PRELIMINARY · Self-reported capacities from responding countries only. Reported as “in place” means a positive or fully functional answer, not partial or developing. All measures use question-specific denominators.</div>',unsafe_allow_html=True)


def capacity_and_gaps(active):
    section('Core capacities reported as in place','Denominators reflect countries with a recognized answer to each survey item.',eyebrow='01 / CAPACITY PROFILES')
    caps=capacity_table(active)
    component=st.selectbox('Explore a component',list(caps.component.unique()),key='capacity_component')
    sliced=caps[caps.component==component]
    c1,c2=st.columns([1.05,1],gap='large')
    with c1:
        with st.container(border=True):
            st.markdown('#### Availability by capacity')
            st.plotly_chart(viz.horizontal_bars(sliced,height=max(335,len(sliced)*49+80)),use_container_width=True,config={'displayModeBar':False})
    with c2:
        with st.container(border=True):
            st.markdown('#### Countries reporting each capacity')
            grid=[]
            for _,c in active.iterrows():
                r={'Country':c.country}
                for _,item in sliced.iterrows():
                    if item['col']!=-1:
                        positive=next((codes for group,items in CAPACITIES.items() for lab,col,codes in items if lab==item['capacity'] and col==item['col']),())
                        value=country_capacity(c,int(item['col']),positive)
                    else:value=c.get(item['capacity'])
                    r[item['capacity']]='●' if pd.notna(value) and bool(value) else '—' if pd.notna(value) else '·'
                grid.append(r)
            st.dataframe(pd.DataFrame(grid).set_index('Country'),use_container_width=True,height=max(340,34*(len(grid)+1)),
                         column_config={x:st.column_config.TextColumn(width='small') for x in sliced.capacity},hide_index=False)
            note('● In place / reported; — not in place; · not reported. Matrix uses country-level OR for Colombia.')
    st.divider()
    section('Information technology and surge workforce','Two recurrent priorities for regional technical cooperation.')
    top=capacity_table(active)
    p=top[top.capacity.isin(['Integrated/interoperable platform','Formal SITREP process','Updated surge roster','Formal surge procedure','Redundant internet','Backup generator'])]
    st.plotly_chart(viz.horizontal_bars(p,height=330),use_container_width=True,config={'displayModeBar':False})


def operations_section(active):
    section('Hazards coordinated during the past two years',
            'Reported frequency bands: 0 / 1–2 / 3–5 / >5 events. Bands are ordinal; they are not exact event counts.',
            eyebrow='01 / TYPES OF EMERGENCIES')
    st.plotly_chart(viz.hazard_heatmap(active.sort_values('country')),use_container_width=True,config={'displayModeBar':False})
    st.divider()
    c1,c2=st.columns(2,gap='large')
    with c1:
        section('Physical infrastructure','Number of responding countries that report each physical resource.',eyebrow='02 / INFRASTRUCTURE')
        cards=[]
        for r in RESOURCE_LABELS.values():
            valid=active[r].dropna();cards.append({'capacity':r,'in_place':sum(bool(x) for x in valid),'denominator':len(valid)})
        st.plotly_chart(viz.horizontal_bars(pd.DataFrame(cards),height=420),use_container_width=True,config={'displayModeBar':False})
    with c2:
        section('Training completed versus prioritized','Each country counted once per course; countries may select several options.',eyebrow='03 / WORKFORCE DEVELOPMENT')
        courses=[]
        for course in TRAINING_LABELS:
            done=active['Completed: '+course].dropna()
            pri=active['Priority: '+course].dropna()
            courses.append({'Course':course,'Completed':sum(bool(x) for x in done),
                            'Priority':sum(bool(x) for x in pri),'Respondents':len(done)})
        import plotly.graph_objects as go
        fig=go.Figure()
        names=[x['Course'] for x in courses][::-1]
        fig.add_bar(y=names,x=[x['Completed'] for x in courses][::-1],orientation='h',name='Completed last year',marker_color=viz.NAVY)
        fig.add_bar(y=names,x=[x['Priority'] for x in courses][::-1],orientation='h',name='Priority next year',marker_color=viz.ORANGE)
        fig.update_layout(barmode='group',legend=dict(orientation='h',y=1.1),height=420,
                          plot_bgcolor='white',paper_bgcolor='rgba(0,0,0,0)',
                          margin=dict(l=15,r=15,t=30,b=15),font=dict(color=TEXT,size=11))
        fig.update_xaxes(dtick=1,gridcolor='#ECF2F6');fig.update_yaxes(automargin=True)
        st.plotly_chart(fig,use_container_width=True,config={'displayModeBar':False})


def cooperation_section(active):
    section('Regional and global networks','Network membership and willingness to join, among countries that answered these later questions.',eyebrow='01 / COOPERATION NETWORKS')
    ncols=st.columns(3)
    for widget,name in zip(ncols,NETWORK_NAMES.values()):
        valid=active[name]
        counts=valid.value_counts()
        with widget:
            st.metric(name,int((valid!='Not reported').sum()),help='Number of countries with a network participation answer.')
            st.markdown(f"<div class='small-note'><b>{int(counts.get('Participating',0))}</b> participating · <b>{int(counts.get('Interested',0))}</b> interested · <b>{int(counts.get('Not participating',0))}</b> not participating</div>",unsafe_allow_html=True)
    st.write('')
    section('Country network status','Only those with a reported network status are displayed.')
    cols=['country']+list(NETWORK_NAMES.values())
    st.dataframe(active[cols].rename(columns={'country':'Country'}),use_container_width=True,hide_index=True,height=min(530,42*len(active)+42))
    st.divider()
    a,b=st.columns(2,gap='large')
    with a:
        section('Expertise countries can share',
                'Country-reported technical expertise available for cooperation.',eyebrow='02 / CAPACITIES OFFERED')
        vals=[]
        for name in COOPERATION_SKILLS.values():
            series=active['Skill: '+name].dropna()
            vals.append({'capacity':name,'in_place':sum(bool(x) for x in series),'denominator':len(series)})
        shown=pd.DataFrame(vals).sort_values('in_place',ascending=False).head(9)
        st.plotly_chart(viz.horizontal_bars(shown,height=445),use_container_width=True,config={'displayModeBar':False})
    with b:
        section('How countries can cooperate',
                'Reported modalities of technical collaboration.',eyebrow='03 / MODALITIES')
        vals=[]
        for name in COOPERATION_MODES.values():
            series=active['Mode: '+name].dropna()
            vals.append({'capacity':name,'in_place':sum(bool(x) for x in series),'denominator':len(series)})
        shown=pd.DataFrame(vals).sort_values('in_place',ascending=False)
        st.plotly_chart(viz.horizontal_bars(shown,height=420),use_container_width=True,config={'displayModeBar':False})
    st.markdown('<div class="eoc-note">The later questions about mobilizable expertise, cooperation modalities and regional networks were answered by fewer countries. Never use the full 15-country denominator when a question was not asked or answered.</div>',unsafe_allow_html=True)


def flag_from_iso(iso):
    alpha={'ARG':'AR','BHS':'BS','BLZ':'BZ','BOL':'BO','BRA':'BR','COL':'CO','DMA':'DM','ECU':'EC','SLV':'SV',
           'GTM':'GT','HND':'HN','PAN':'PA','PRY':'PY','PER':'PE','LCA':'LC'}.get(iso,'')
    return ''.join(chr(ord(k)-ord('A')+0x1F1E6) for k in alpha)



def country_profile(records,countries):
    region=st.selectbox('Select a country',sorted(records.country.unique()),key='selected_country')
    options=records[records.country==region].sort_values('institution')
    rows={f'{x.institution} · Excel row {x.source_excel_row}':int(i) for i,x in options.iterrows()}
    selected_key=st.selectbox('Reporting institution',list(rows.keys()),key='selected_institution')
    r=records.loc[rows[selected_key]]
    st.markdown(f'''<div style="display:flex;gap:14px;align-items:center;padding:14px 0 18px">
        <div style="font-size:3.4rem;line-height:1">{flag_from_iso(r.iso3)}</div><div>
        <div class="bigcountry">{esc(r.country)}</div><div style="font-size:.86rem;color:#647D8D">{esc(r.institution)}</div></div></div>''',unsafe_allow_html=True)
    t1,t2,t3,t4=st.columns(4)
    t1.metric('EOC status',r.eoc_status)
    t2.metric('Operating mode',r.operating_mode)
    t3.metric('Activation',r.activation)
    t4.metric('24/7 duty staff',f'{int(r.staff_24_7)}' if pd.notna(r.staff_24_7) else 'Not reported')
    st.write('')
    section('Reported institutional capacities',
            'Answers from this institution, grouped by PHEOC core component.',
            eyebrow='01 / CAPACITIES REPORTED')
    groups=list(CAPACITIES.items())
    tabs=st.tabs([name for name,_ in groups])
    for tab,(group,items) in zip(tabs,groups):
        with tab:
            details=[]
            for label,col,positive in items:
                availability=country_capacity(r,col,positive)
                details.append({'Capacity':label,'Reported status':
                    'In place' if availability is True else 'Not in place / partial' if availability is False else 'Not reported'})
            st.dataframe(pd.DataFrame(details),use_container_width=True,hide_index=True,
                         height=min(525,38*(len(details)+1)+15))
    note('Only explicit qualifying answers are marked in place. “Not reported” is different from a negative answer.')
    st.divider()
    col1,col2=st.columns([1,1],gap='large')
    with col1:
        section('Hazards coordinated','Band reported by the selected institution.',eyebrow='02 / LAST TWO YEARS')
        desc={0:'No events',1:'1–2 events',2:'3–5 events',3:'More than 5 events'}
        for lab in HAZARD_LABELS.values():
            x=r[lab];level=int(x) if pd.notna(x) else -1
            st.markdown(f'**{lab}** · {desc.get(level,"Not reported")}')
            st.progress(max(0,(level+1)/4))
    with col2:
        section('Physical infrastructure','Resources reported as available at this institution.',eyebrow='03 / INFRASTRUCTURE')
        for i,(label,chunk) in enumerate([(k,r[k]) for k in RESOURCE_LABELS.values()]):
            if i%2==0:l,rcol=st.columns(2)
            with (l if i%2==0 else rcol):
                symbol='✓' if pd.notna(chunk) and bool(chunk) else '—' if pd.notna(chunk) else '·'
                clr=CYAN if pd.notna(chunk) and bool(chunk) else '#7B93A2'
                st.markdown(f'<div style="font-size:.86rem;padding:8px 0"><span style="color:{clr};font-weight:800">{symbol}</span> {esc(label)}</div>',unsafe_allow_html=True)
    st.divider()
    section('Training and preparedness','Completed activities during the last year versus identified priorities for the next period.',eyebrow='04 / PEOPLE AND TRAINING')
    df=pd.DataFrame([{'Training area':label,
                      'Completed in last year':'Yes' if pd.notna(r['Completed: '+label]) and bool(r['Completed: '+label]) else 'No' if pd.notna(r['Completed: '+label]) else 'Not reported',
                      'Future priority':'Yes' if pd.notna(r['Priority: '+label]) and bool(r['Priority: '+label]) else 'No' if pd.notna(r['Priority: '+label]) else 'Not reported'}
                     for label in TRAINING_LABELS])
    st.dataframe(df,use_container_width=True,hide_index=True,height=330)
    st.divider()
    section('Reported experience','Open-text fields as originally submitted. Spanish or Portuguese entries are not machine-translated.',eyebrow='05 / INSTITUTIONAL NOTES')
    a,b=st.columns(2,gap='large')
    for col,key,title in ((a,'Reported strengths (original language)','Reported strengths'),
                          (b,'Improvement areas (original language)','Areas for improvement')):
        with col:
            with st.container(border=True):
                st.markdown('**'+title+'**')
                st.write(r[key] or 'No narrative response provided.')
    if r['Recent activations (original language)']:
        with st.expander('Recent events / activations · original response'):
            st.write(r['Recent activations (original language)'])
    skills=[name for name in COOPERATION_SKILLS.values() if pd.notna(r['Skill: '+name]) and bool(r['Skill: '+name])]
    modes=[name for name in COOPERATION_MODES.values() if pd.notna(r['Mode: '+name]) and bool(r['Mode: '+name])]
    if skills or modes:
        with st.expander('Technical capabilities and contributions this institution can offer'):
            st.markdown('**Expertise:** '+(', '.join(skills) if skills else 'Not reported'))
            st.markdown('**Modalities:** '+(', '.join(modes) if modes else 'Not reported'))
    note('Record-specific profile: Colombia’s two institutions remain independent. Answers come from the survey, with no names, phone numbers or emails exposed.')


def methodology(records,country):
    section('Methods & limitations','How the dashboard interprets the self-reported survey.',eyebrow='DATA GOVERNANCE')
    with st.container(border=True):
        st.markdown('''**Unit of analysis.** The underlying dataset has one row per institutional response. Regional figures count each country once, so Colombia does not get additional weight because it has two submissions. Country capacities count as available if **at least one** institution reports them as fully in place. The institutional view keeps both submissions separate.

**Capacity counts.** Every indicator refers to a concrete questionnaire capacity and counts countries that report it as present, formally established or functional. Missing items reduce the denominator; developing/informal options are **not** treated as fully in place. These are item-level survey indicators rather than a combined rating.

**Hazards.** Frequencies are ordered categories (none, 1–2, 3–5, over 5), not continuous event counts. For the regional country view, multiple institutional frequencies show the highest reported category, not their sum.

**Coverage.** Results are preliminary and represent only responding countries. Some later network and cooperation items have smaller denominators. The Brazil pilot survey has mapped answers that may not be completely equivalent to the final questionnaire.

**Privacy.** This dashboard intentionally excludes respondent names, phone numbers, emails, submission IDs and raw contact exports.''')
    st.write('')
    st.markdown('#### Indicator coverage and question-specific denominators')
    m=capacity_table(country)[['component','capacity','in_place','denominator']].rename(
        columns={'component':'Component','capacity':'Reported capacity','in_place':'Countries with capacity','denominator':'Countries responding'})
    st.dataframe(m,hide_index=True,use_container_width=True,height=420)
    st.markdown('#### Download a non-personal country summary')
    st.download_button('Download safe country indicators (.csv)',data=safe_csv(country),
                       file_name='paho_eoc_country_indicators_2026.csv',mime='text/csv')
    st.markdown('**Methodological implementation in GitHub:** `dashboard/data.py` · `dashboard/charts.py`.')
    note('Data source: PAHO/WHO 2026 survey; preliminary self-reported information.')


def main():
    ui_style()
    try:
        records,raw=load_data()
    except Exception as ex:
        st.error(f'Unable to read the survey data: {ex}')
        st.stop()
    country=country_aggregate(records)
    with st.sidebar:
        st.markdown('<div class="section-eyebrow">REGIONAL MONITORING</div>',unsafe_allow_html=True)
        st.markdown('### EOC-S · Americas')
        st.caption('PAHO/WHO survey 2026')
        view=st.radio('Explore', ['Regional overview','Country profiles','Methods & data'],label_visibility='collapsed')
        if view=='Regional overview':
            st.divider()
            regions=st.multiselect('Geographic areas',sorted(country.subregion.unique()),default=sorted(country.subregion.unique()))
            all_countries=country[country.subregion.isin(regions)]
            selected=st.multiselect('Countries',all_countries.country.tolist(),default=all_countries.country.tolist())
            tabscope=st.radio('Regional section',['Overview','Capacities & gaps','Operations & hazards','Networks & cooperation'])
        st.divider()
        st.caption(f'2026 survey · {len(country)} countries · {len(records)} institutional responses')
        st.caption('Source: local Excel in `data/` · Updated with GitHub redeploy')
    header()
    if view=='Regional overview':
        active=country[country.country.isin(selected)]
        if active.empty:
            st.info('Select at least one country to display regional indicators.')
            st.stop()
        if tabscope=='Overview':regional_overview(country,active)
        elif tabscope=='Capacities & gaps':capacity_and_gaps(active)
        elif tabscope=='Operations & hazards':operations_section(active)
        else:cooperation_section(active)
    elif view=='Country profiles':country_profile(records,country)
    else:methodology(records,country)
    st.markdown('<div class="paho-footer">PAHO / WHO · EOC-NET Americas · 2026  |  Preliminary, self-reported information  |  Analytical dashboard for technical coordination</div>',unsafe_allow_html=True)

if __name__=='__main__':main()