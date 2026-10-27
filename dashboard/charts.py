"""Clean Plotly charts for PAHO/WHO EOC-S regional monitoring."""
from __future__ import annotations
from pathlib import Path
from functools import lru_cache
import json
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from dashboard.data import DOMAINS,DOMAIN_SHORT,HAZARD_LABELS,GPKG

NAVY='#005A8B'; BLUE='#236192'; CYAN='#009BDA'; ORANGE='#F36B32'
TEXT='#17324D'; MUTED='#597083'; PALE='#EAF3F9'; GRAY='#E5EDF3'
GREEN='#1D947C'; RED='#D75E52'; GOLD='#E9A33B'
COLORS=[NAVY,CYAN,'#86BDD9',ORANGE,GOLD]


def style(fig,height=340,margin=None):
    fig.update_layout(height=height,plot_bgcolor='white',paper_bgcolor='rgba(0,0,0,0)',
         font=dict(family='Arial, sans-serif',size=12,color=TEXT),
         margin=margin or dict(l=12,r=12,b=28,t=26),
         hoverlabel=dict(bgcolor='white',font_size=12),
         legend=dict(orientation='h',yanchor='bottom',y=1.04,x=0,xanchor='left',font_size=11),
         hovermode='closest')
    return fig


def horizontal_bars(data,x='in_place',y='capacity',height=350,divide=False,selected=None):
    v=data.sort_values(x,ascending=True)
    fig=go.Figure()
    fig.add_trace(go.Bar(y=v[y],x=v[x],orientation='h',marker_color=CYAN,
              text=[f'{int(n)}/{int(d)}' if pd.notna(d) else str(n) for n,d in zip(v[x],v.get('denominator',[np.nan]*len(v)))],
              textposition='outside',cliponaxis=False,hovertemplate='%{y}: %{x}<extra></extra>'))
    fig.update_xaxes(showgrid=True,gridcolor='#F0F4F7',zeroline=False,range=[0,max(4,float(v[x].max())*1.18)])
    fig.update_yaxes(showgrid=False,title=None,automargin=True)
    return style(fig,height=height,margin=dict(l=10,r=65,b=28,t=24))


def score_chart(benchmark):
    v=benchmark.iloc[::-1]
    fig=go.Figure()
    fig.add_trace(go.Bar(x=v['mean'],y=v['domain'],orientation='h',marker_color=CYAN,
                         text=[f'{x:.1f} / 100' for x in v['mean']],textposition='outside',cliponaxis=False,
                         hovertemplate='%{y}: %{x:.1f}/100<extra></extra>'))
    fig.update_xaxes(range=[0,112],dtick=20,gridcolor='#EEF3F7',title=None)
    fig.update_yaxes(automargin=True,title=None)
    return style(fig,360,dict(l=10,r=28,b=25,t=18))


def operating_chart(frame):
    order=['24/7 continuous','Response + monitoring','Response only','Not formally defined','Not reported']
    colors=[NAVY,CYAN,'#80BDD8',ORANGE,'#CED7DE']
    vals=[int((frame.operating_mode==s).sum()) for s in order]
    fig=go.Figure(go.Pie(labels=order,values=vals,hole=.68,sort=False,
             marker=dict(colors=colors,line=dict(color='white',width=2)),
             textinfo='value',textposition='inside',hovertemplate='%{label}: %{value} countries<extra></extra>'))
    fig.update_layout(annotations=[dict(text=f'<b>{sum(vals)}</b><br><span style="font-size:10px">countries</span>',
                                       x=.5,y=.5,font=dict(size=23,color=NAVY),showarrow=False)],
        legend=dict(orientation='v',x=1.02,y=.8,yanchor='middle',font_size=11))
    return style(fig,320,dict(l=0,r=150,t=20,b=20))


def activation_chart(frame):
    order=['Under 2 hours','2–6 hours','Over 6 hours','Not defined','Not reported']
    colors=[GREEN,CYAN,ORANGE,'#A4B6C4','#CBD5DF']
    vs=[int((frame.activation==x).sum()) for x in order]
    fig=go.Figure()
    for s,v,color in zip(order,vs,colors):
        if v:
            fig.add_bar(x=[v],y=['Countries'],orientation='h',name=s,marker_color=color,text=[f'{v}'],
                        textposition='inside',hovertemplate=f'{s}: {v} countries<extra></extra>')
    fig.update_layout(barmode='stack',showlegend=True,legend=dict(orientation='h',y=-.5,font_size=10))
    fig.update_xaxes(showgrid=False,dtick=1,range=[0,max(15,sum(vs))]);fig.update_yaxes(visible=False)
    return style(fig,170,dict(l=8,r=12,t=12,b=50))


def hazard_heatmap(frame):
    cats=list(HAZARD_LABELS.values())
    if frame.empty:return go.Figure()
    vals=frame[cats].fillna(-1).to_numpy(dtype=float)
    countries=list(frame['country'])
    # Ordinal frequencies must never be presented as exact event counts.
    cmap=[[0,'#EFF3F6'],[.001,'#EFF3F6'],[.249,'#EAF3F9'],[.25,'#97CCEA'],
          [.499,'#97CCEA'],[.5,CYAN],[.749,CYAN],[.75,NAVY],[1,NAVY]]
    z=np.where(vals==-1,0,vals+1)
    fig=go.Figure(go.Heatmap(z=z,x=cats,y=countries,zmin=0,zmax=4,colorscale=cmap,
                      showscale=False,text=[['Not reported' if p<0 else ['None','1–2','3–5','>5'][int(p)] for p in row] for row in vals],
                      texttemplate='%{text}',textfont=dict(size=10),
                      hovertemplate='%{y} · %{x}<br>Reported events: %{text}<extra></extra>',
                      xgap=4,ygap=4))
    fig.update_yaxes(autorange='reversed',title=None,automargin=True)
    fig.update_xaxes(title=None,side='top',tickangle=0,automargin=True)
    return style(fig,max(380,60+len(countries)*28),dict(l=20,r=8,t=15,b=32))


def maturity_radar(country_row,reference):
    a=[float(country_row.get(n,np.nan)) for n in DOMAINS]
    b=[float(reference.loc[reference.domain==n,'mean'].iloc[0]) for n in DOMAINS]
    lab=DOMAIN_SHORT+[DOMAIN_SHORT[0]]
    fig=go.Figure()
    fig.add_trace(go.Scatterpolar(r=b+[b[0]],theta=lab,fill='toself',name='Responding-country mean',
       line=dict(color=ORANGE,width=2,dash='dot'),fillcolor='rgba(243,107,50,.05)'))
    fig.add_trace(go.Scatterpolar(r=a+[a[0]],theta=lab,fill='toself',name='Selected institution',
       line=dict(color=NAVY,width=3),fillcolor='rgba(0,90,139,.14)'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True,range=[0,100],tickvals=[20,40,60,80,100],
                                  gridcolor='#E6EDF2',color=MUTED),
                        angularaxis=dict(gridcolor='#E6EDF2',tickfont=dict(size=11))),
                      showlegend=True,legend=dict(orientation='h',x=.05,y=-.1))
    return style(fig,430,dict(l=40,r=40,t=30,b=35))


def maturity_country_bars(institution,reference):
    fig=go.Figure()
    for name,short in zip(DOMAINS,DOMAIN_SHORT):
        val=institution.get(name,np.nan)
        region=float(reference.loc[reference.domain==name,'mean'].iloc[0])
        if pd.notna(val):
            fig.add_trace(go.Bar(x=[val],y=[short],orientation='h',marker_color=NAVY,
                                 width=.55,showlegend=False,hovertemplate=f'{name}: {val:.0f}/100<extra></extra>'))
        fig.add_trace(go.Scatter(x=[region],y=[short],mode='markers',marker=dict(color=ORANGE,size=12,symbol='line-ns-open',line=dict(width=3)),
                                 showlegend=False,hovertemplate=f'Responding-country mean: {region:.1f}<extra></extra>'))
    fig.update_xaxes(range=[0,103],dtick=20,gridcolor='#EFF3F7')
    fig.update_yaxes(autorange='reversed',automargin=True,title=None)
    return style(fig,275,dict(l=16,r=20,t=10,b=23))


@lru_cache(maxsize=1)
def load_geojson():
    import geopandas as gpd
    from shapely.geometry import box
    if not GPKG.is_file():return None
    geodf=gpd.read_file(str(GPKG)).to_crs(4326)
    if not {'ISO_CC','COUNTRY'}.issubset(geodf.columns):
        raise ValueError('Geopackage must provide ISO_CC and COUNTRY columns')
    geodf=geodf[geodf['ISO_CC'].notna()].copy()
    geodf.geometry=geodf.geometry.intersection(box(-132,-57,-30,34))
    geodf=geodf[~geodf.geometry.is_empty]
    geodf.geometry=geodf.geometry.simplify(0.045,preserve_topology=True)
    return json.loads(geodf[['ISO_CC','COUNTRY','geometry']].to_json())


def countries_map(countries,selection=None):
    geo=load_geojson()
    if geo is None:return None
    geo_codes={ft['properties']['ISO_CC'] for ft in geo['features']}
    stats=countries.set_index('iso3')
    listrows=[]
    for code in sorted(geo_codes):
        if code in stats.index:
            row=stats.loc[code]
            country=row['country'];status=row['eoc_status']
            if selection is not None and country not in selection: status='Outside filter'
        else:country='No survey response';status='No survey response'
        listrows.append({'iso3':code,'country':country,'status':status})
    data=pd.DataFrame(listrows)
    order=['Established','In implementation','Not established','Outside filter','No survey response']
    colors=['#005A8B','#009BDA','#D75E52','#D5E0E9','#EFF2F4']
    fig=px.choropleth(data,geojson=geo,locations='iso3',featureidkey='properties.ISO_CC',
                      color='status',hover_name='country',
                      custom_data=['iso3'],category_orders={'status':order},
                      color_discrete_map=dict(zip(order,colors)))
    fig.update_traces(marker_line_color='white',marker_line_width=.55,
                      hovertemplate='<b>%{hovertext}</b><br>ISO: %{customdata[0]}<br>Status: %{fullData.name}<extra></extra>')
    fig.update_geos(projection_type='mercator',visible=False,
                    lataxis_range=[-57,34],lonaxis_range=[-117,-32],
                    showocean=False,showcoastlines=False,showland=False)
    fig.update_layout(legend=dict(title=None,orientation='h',y=-.04,x=0,font_size=10),dragmode=False)
    return style(fig,495,dict(l=0,r=0,t=0,b=36))