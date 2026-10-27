"""Clean Plotly charts for PAHO/WHO EOC-S regional monitoring."""
from __future__ import annotations
from pathlib import Path
from functools import lru_cache
import json
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from dashboard.data import HAZARD_LABELS,TRAINING_LABELS,NETWORK_NAMES,GPKG
from dashboard.i18n import tr

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


def horizontal_bars(data,x='in_place',y='capacity',height=350,divide=False,selected=None,lang='en'):
    """Percentages of valid responses, annotated with numerator and denominator."""
    v=data.sort_values(x,ascending=True)
    pct=[100*float(n)/float(d) if d else 0 for n,d in zip(v[x],v.denominator)]
    fig=go.Figure(go.Bar(y=[tr(q,lang) for q in v[y]],x=pct,orientation='h',marker_color=CYAN,
              text=[f'{z:.0f}% ({int(n)}/{int(d)})' if d else tr('No valid responses',lang)
                    for z,n,d in zip(pct,v[x],v.denominator)],
              textposition='outside',cliponaxis=False,
              hovertemplate='%{y}<br>%{text}<extra></extra>'))
    fig.update_xaxes(showgrid=True,gridcolor='#F0F4F7',zeroline=False,range=[0,128],
                     tickvals=[0,25,50,75,100],ticksuffix='%')
    fig.update_yaxes(showgrid=False,title=None,automargin=True)
    return style(fig,height=height,margin=dict(l=12,r=52,b=28,t=20))


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


def hazard_heatmap(frame,lang='en'):
    """Four short, readable headers; contrasting text for dark and light cells."""
    cats=list(HAZARD_LABELS.values())
    if frame.empty:return go.Figure()
    vals=frame[cats].to_numpy(dtype=float)
    countries=[tr(q,lang) for q in frame['country']]
    short=([tr(q,lang) for q in ['Geological / weather','Biological / epidemic','Social / human-caused','Technological']]
           if lang=='es' else ['Geo / weather','Biological','Social','Technological'])
    text=[[tr('Not reported',lang) if pd.isna(v) else ['0','1–2','3–5','>5'][int(v)] for v in row]
          for row in vals]
    z=np.where(np.isnan(vals),0,vals+1)
    cmap=[[0,'#F0F4F7'],[.249,'#F0F4F7'],[.25,'#E8F4FA'],[.499,'#E8F4FA'],
          [.5,'#91CAE8'],[.749,'#91CAE8'],[.75,CYAN],[.999,CYAN],[1,NAVY]]
    fig=go.Figure(go.Heatmap(z=z,x=short,y=countries,zmin=0,zmax=4,
                  colorscale=cmap,showscale=False,customdata=text,
                  hovertemplate='<b>%{y} · %{x}</b><br>'+('Frecuencia: ' if lang=='es' else 'Frequency: ')+'%{customdata}<extra></extra>',
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



NETWORK_STATUS_CODES={'Not reported':0,'Not participating':1,'Interested':2,'Participating':3}
NETWORK_STATUS_COLORS={
    'Participating':NAVY,
    'Interested':CYAN,
    'Not participating':ORANGE,
    'Not reported':'#E7EDF2',
}


def network_participation_heatmap(frame,lang='en'):
    """Country x network status matrix; categorical (not a numerical score).

    Include every responding country, even when none of its network questions
    have a valid response. Cells show a symbol as well as a color and hover text.
    """
    names=list(NETWORK_NAMES.values())
    missing=[name for name in ['country']+names if name not in frame.columns]
    if missing:
        raise ValueError(f'Missing network matrix columns: {missing}')
    ordered=frame.sort_values('country').reset_index(drop=True)
    if ordered.empty:
        return go.Figure()
    countries=[tr(name,lang) for name in ordered.country]
    columns=[tr(name,lang) for name in names]
    raw=ordered[names].fillna('Not reported')
    statuses=raw.apply(lambda col: col.map(
        lambda x: x if x in NETWORK_STATUS_CODES else 'Not reported'))
    z=statuses.replace(NETWORK_STATUS_CODES).to_numpy(dtype=int)
    translated=statuses.apply(lambda col: col.map(lambda x: tr(x,lang)))
    customdata=translated.to_numpy()
    discrete=['#E7EDF2',ORANGE,CYAN,NAVY]
    scale=[]
    for index,color in enumerate(discrete):
        scale.extend([[index/4,color],[(index+1)/4,color]])
    fig=go.Figure(go.Heatmap(
        z=z,x=columns,y=countries,zmin=-0.5,zmax=3.5,
        colorscale=scale,showscale=False,xgap=7,ygap=5,
        customdata=customdata,
        hovertemplate='<b>%{y} · %{x}</b><br>%{customdata}<extra></extra>'
    ))
    glyphs={0:'—',1:'×',2:'◐',3:'✓'}
    for row,country in enumerate(countries):
        for col,network in enumerate(columns):
            status=int(z[row,col])
            fig.add_annotation(
                x=network,y=country,text=glyphs[status],showarrow=False,
                font=dict(family='Arial,sans-serif',size=15,
                          color=('#526A7B' if status==0 else '#FFFFFF'))
            )
    fig.update_yaxes(autorange='reversed',automargin=True,title=None,
                     showgrid=False,tickfont=dict(size=12,color=TEXT))
    fig.update_xaxes(side='top',automargin=True,title=None,showgrid=False,
                     tickfont=dict(size=12,color=NAVY))
    fig=style(fig,max(480,len(countries)*32+80),
              dict(l=8,r=18,t=48,b=24))
    fig.update_layout(paper_bgcolor='#FFFFFF',plot_bgcolor='#FFFFFF')
    return fig


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


def countries_map(countries, selection=None, lang='en'):
    """Render the bundled GeoPackage without Plotly Geo's external topojson fetch.

    Plotly's MapLibre-backed choroplethmap renders the GeoJSON polygons directly
    on a token-free white background. No remote base tiles or API key are needed.
    """
    geo=load_geojson()
    if geo is None:return None
    geo_codes={ft['properties']['ISO_CC'] for ft in geo['features']}
    stats=countries.set_index('iso3')
    listrows=[]
    for code in sorted(geo_codes):
        if code in stats.index:
            row=stats.loc[code]
            country=row['country'];status=row['eoc_status']
            if selection is not None and country not in selection:status='Outside filter'
        else:
            country='No survey response';status='No survey response'
        listrows.append({'iso3':code,'country':tr(country,lang),'status':tr(status,lang)})
    data=pd.DataFrame(listrows)
    status_order=['Established','In implementation','Not established','Outside filter','No survey response']
    palette=['#005A8B','#009BDA','#D75E52','#D5E0E9','#EFF2F4']
    fig=px.choropleth_map(
        data,geojson=geo,locations='iso3',featureidkey='properties.ISO_CC',
        color='status',hover_name='country',custom_data=['iso3'],
        category_orders={'status':[tr(x,lang) for x in status_order]},
        color_discrete_map={tr(s,lang):c for s,c in zip(status_order,palette)},
        map_style='white-bg',
        center={'lat':-11,'lon':-79},zoom=1.55,opacity=0.94,
    )
    fig.update_traces(
        marker_line_color='white',marker_line_width=0.65,
        hovertemplate='<b>%{hovertext}</b><br>ISO: %{customdata[0]}<br>'+
                      ('Estado' if lang=='es' else 'Status')+
                      ': %{fullData.name}<extra></extra>'
    )
    fig.update_layout(
        map=dict(style='white-bg',center=dict(lat=-11,lon=-79),zoom=1.55),
        legend=dict(title=None,orientation='h',y=-.08,x=0,font_size=10),
        dragmode=False,
    )
    # Opaque white plot canvas fills the complete gray-bordered dashboard card.
    fig=style(fig,450,dict(l=0,r=0,t=0,b=38))
    fig.update_layout(paper_bgcolor='#FFFFFF',plot_bgcolor='#FFFFFF')
    return fig


def training_comparison(frame,lang='en'):
    """Paired proportion bars; every bar uses its own non-missing denominator."""
    fig=go.Figure()
    labels=[tr(x,lang) for x in frame['area']]
    for name,ncol,dcol,color in [('Completed','done_n','done_d',NAVY),('Prioritized','priority_n','priority_d',CYAN)]:
        n=frame[ncol].astype(int).tolist();den=frame[dcol].astype(int).tolist()
        pct=[100*a/b if b else 0 for a,b in zip(n,den)]
        captions=[f'{v:.0f}% ({a}/{b})' if b else '—' for v,a,b in zip(pct,n,den)]
        fig.add_bar(name=tr(name,lang),x=pct,y=labels,orientation='h',marker_color=color,
                    text=captions,textposition='outside',cliponaxis=False,
                    hovertemplate='%{y}<br>'+tr(name,lang)+': %{text}<extra></extra>')
    fig.update_layout(barmode='group',legend=dict(orientation='h',y=1.08,x=0))
    fig.update_xaxes(title=None,range=[0,135],tickvals=[0,25,50,75,100],ticksuffix='%',
                     showgrid=True,gridcolor='#EAF0F4',zeroline=False)
    fig.update_yaxes(autorange='reversed',automargin=True,title=None,showgrid=False)
    return style(fig, max(460,len(labels)*66+95), dict(l=5,r=20,t=65,b=35))


def country_training(institution,lang='en'):
    """Binary training matrix, not a maturity score or artificial percentage."""
    labels=[tr(n,lang) for n in TRAINING_LABELS]
    fields=['Completed: ','Priority: ']
    z=[];text=[];custom=[]
    for name in TRAINING_LABELS:
        row=[];caption=[];hover=[]
        for field in fields:
            v=institution.get(field+name)
            if pd.isna(v):rank=0;label=tr('Not reported',lang);caption.append('—')
            elif bool(v):rank=2;label=tr('In place',lang);caption.append('✓')
            else:rank=1;label=tr('Partial / absent',lang);caption.append('×')
            row.append(rank);hover.append(label)
        z.append(row);text.append(caption);custom.append(hover)
    cols=[tr('Completed',lang),tr('Prioritized',lang)]
    fig=go.Figure(go.Heatmap(z=z,x=cols,y=labels,zmin=0,zmax=2,showscale=False,
       colorscale=[[0,'#EEF2F5'],[.249,'#EEF2F5'],[.25,'#FDEBDD'],[.749,'#FDEBDD'],[.75,'#CDEFE7'],[1,'#CDEFE7']],
       customdata=custom,hovertemplate='%{y} · %{x}<br>%{customdata}<extra></extra>',
       xgap=4,ygap=4))
    for i,label in enumerate(labels):
        for j,col in enumerate(cols):
            fig.add_annotation(x=col,y=label,text=text[i][j],showarrow=False,
                font=dict(size=16,color=(GREEN if z[i][j]==2 else RED if z[i][j]==1 else MUTED)))
    fig.update_yaxes(autorange='reversed',automargin=True,title=None,showgrid=False)
    fig.update_xaxes(side='top',title=None,showgrid=False)
    return style(fig,max(370,len(labels)*43+70),dict(l=8,r=12,t=45,b=15))


def country_hazards(institution,lang='en'):
    """Ordinal bands: a chart of reported frequency categories, never percent of events."""
    labels=[tr(v,lang) for v in HAZARD_LABELS.values()]
    vals=[institution.get(v) for v in HAZARD_LABELS.values()]
    scores=[int(v) if pd.notna(v) else 0 for v in vals]
    captions=([tr('No events',lang),tr('1–2 events',lang),tr('3–5 events',lang),tr('More than 5 events',lang)])
    notes=[captions[int(v)] if pd.notna(v) else tr('Not reported',lang) for v in vals]
    fig=go.Figure(go.Bar(y=labels,x=scores,orientation='h',marker_color=CYAN,
                         text=notes,textposition='outside',cliponaxis=False,
                         hovertemplate='%{y}: %{text}<extra></extra>'))
    fig.update_xaxes(range=[0,4.8],tickvals=[0,1,2,3],ticktext=['0','1–2','3–5','>5'],
                     showgrid=True,gridcolor='#EAF0F4',title=None,zeroline=False)
    fig.update_yaxes(autorange='reversed',automargin=True,showgrid=False,title=None)
    return style(fig,340,dict(l=8,r=15,t=14,b=30))