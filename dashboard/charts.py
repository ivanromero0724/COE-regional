"""Clean Plotly charts for PAHO/WHO EOC-S regional monitoring."""
from __future__ import annotations
from pathlib import Path
from functools import lru_cache
import json
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from dashboard.data import HAZARD_LABELS,GPKG

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
    """Four short, readable headers; contrasting text for dark and light cells."""
    cats=list(HAZARD_LABELS.values())
    if frame.empty:return go.Figure()
    vals=frame[cats].to_numpy(dtype=float)
    countries=list(frame['country'])
    short=['Geo / weather','Biological','Social','Technological']
    text=[['Not reported' if pd.isna(v) else ['None','1–2','3–5','>5'][int(v)] for v in row]
          for row in vals]
    z=np.where(np.isnan(vals),0,vals+1)
    cmap=[[0,'#F0F4F7'],[.249,'#F0F4F7'],[.25,'#E8F4FA'],[.499,'#E8F4FA'],
          [.5,'#91CAE8'],[.749,'#91CAE8'],[.75,CYAN],[.999,CYAN],[1,NAVY]]
    fig=go.Figure(go.Heatmap(z=z,x=short,y=countries,zmin=0,zmax=4,
                  colorscale=cmap,showscale=False,customdata=text,
                  hovertemplate='<b>%{y} · %{x}</b><br>Frequency: %{customdata}<extra></extra>',
                  xgap=4,ygap=4))
    for i,name in enumerate(countries):
        for j,label in enumerate(text[i]):
            color='white' if z[i,j]>=3 else TEXT
            fig.add_annotation(x=short[j],y=name,text=label,showarrow=False,
                               font=dict(family='Arial,sans-serif',size=10,color=color))
    fig.update_yaxes(autorange='reversed',title=None,automargin=True,
                     tickfont=dict(size=11,color=TEXT),showgrid=False)
    fig.update_xaxes(title=None,side='top',automargin=True,tickangle=0,
                     tickfont=dict(size=11,color=TEXT),showgrid=False)
    return style(fig,max(410,100+len(countries)*30),dict(l=12,r=12,t=54,b=30))


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