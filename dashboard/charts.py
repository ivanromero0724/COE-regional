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

from dashboard.visual_style import (
    FONT_FAMILY, NAVY, CYAN, ORANGE, LIGHT_BLUE, GREEN, SLATE, PURPLE,
    TEXT, MUTED, BORDER, GRID, AXIS, WHITE, CAPACITY_COLORS, HAZARD_COLORS,
)
BLUE=NAVY
PALE='#EAF3F9'
GRAY=SLATE
RED=ORANGE
GOLD=ORANGE
COLORS=list(CAPACITY_COLORS)


def style(fig,height=340,margin=None):
    """Plotly base treatment from Capacities: white, PAHO palette and compact type."""
    fig.update_layout(
        height=height,plot_bgcolor=WHITE,paper_bgcolor=WHITE,
        font=dict(family=FONT_FAMILY,size=11,color=TEXT),
        margin=margin or dict(l=12,r=12,b=36,t=26),
        hoverlabel=dict(bgcolor=WHITE,font_color=TEXT,font_size=11),
        legend=dict(orientation='h',yanchor='top',y=-.08,x=0,xanchor='left',
                    font=dict(size=10,color=TEXT),itemsizing='constant'),
        hovermode='closest',dragmode=False,
    )
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
    colors=[NAVY,CYAN,LIGHT_BLUE,ORANGE,SLATE]
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
    colors=[GREEN,CYAN,ORANGE,SLATE,LIGHT_BLUE]
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
    # Discrete colors, exactly matching the four hazard donuts.
    # z=0 means missing, while 1..4 are the real 0/1-2/3-5/>5 bands.
    swatches=('#F0F4F7',)+HAZARD_COLORS
    cmap=[]
    for index,color in enumerate(swatches):
        cmap.extend([[index/5,color],[(index+1)/5,color]])
    fig=go.Figure(go.Heatmap(z=z,x=short,y=countries,
                  colorscale=cmap,showscale=False,customdata=text,zmin=0,zmax=5,
                  hovertemplate='<b>%{y} · %{x}</b><br>'+('Frecuencia: ' if lang=='es' else 'Frequency: ')+'%{customdata}<extra></extra>',
                  xgap=4,ygap=4))
    for i,name in enumerate(countries):
        for j,label in enumerate(text[i]):
            # White on PAHO navy; dark text on orange, cyan and the neutral band.
            color='white' if z[i,j]==3 else TEXT
            fig.add_annotation(x=short[j],y=name,text=label,showarrow=False,
                               font=dict(family=FONT_FAMILY,size=10,color=color))
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
                font=dict(family=FONT_FAMILY,size=15,
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


def responding_country_map_center(geo, country_codes):
    """Center the locked map on the geographic extent of survey respondents."""
    points=[]
    def visit(coords):
        if not isinstance(coords, (list,tuple)):
            return
        if len(coords)>=2 and all(isinstance(v,(int,float)) for v in coords[:2]):
            lon,lat=coords[:2]
            if -180<=lon<=180 and -90<=lat<=90:
                points.append((lon,lat))
        else:
            for child in coords:
                visit(child)
    for feature in geo['features']:
        if feature['properties'].get('ISO_CC') in country_codes:
            visit(feature.get('geometry',{}).get('coordinates',[]))
    if not points:
        return {'lat':-11,'lon':-79}
    lons=[p[0] for p in points]
    lats=[p[1] for p in points]
    return {'lat':(min(lats)+max(lats))/2, 'lon':(min(lons)+max(lons))/2}


def responding_country_map_bounds(geo, country_codes):
    """Tight, stable geographic extent across regional filters.

    Include all responding country polygons (not only currently selected
    countries) so the map never jumps as filters change. Preserve geographic
    proportions and leave just a small breathing room around the region.
    """
    points=[]
    def visit(coords):
        if not isinstance(coords,(list,tuple)):
            return
        if (len(coords)>=2
                and isinstance(coords[0],(int,float))
                and isinstance(coords[1],(int,float))):
            points.append((coords[0],coords[1]))
        else:
            for part in coords:
                visit(part)
    for feature in geo['features']:
        if feature.get('properties',{}).get('ISO_CC') in country_codes:
            visit(feature.get('geometry',{}).get('coordinates',[]))
    if not points:
        return (-94,-31),(-57,28)
    lons=[point[0] for point in points]
    lats=[point[1] for point in points]
    # Keep the map close to the occupied region, without clipping islands
    # or southern-country polygons at the edges.
    xpad=max(1.1,(max(lons)-min(lons))*.018)
    ypad=max(1.1,(max(lats)-min(lats))*.018)
    return ((min(lons)-xpad,max(lons)+xpad),
            (min(lats)-ypad,max(lats)+ypad))


def countries_map(countries, selection=None, lang='en'):
    """Fixed geographic viewport, with country hover but no pan/zoom.

    Cartesian polygon traces deliberately replace MapLibre: Plotly's map
    engine can still pan even with layout.dragmode=False. Fixed-range
    Cartesian axes reliably prevent dragging while preserving hover.
    """
    geo=load_geojson()
    if geo is None:
        return None
    stats=countries.set_index('iso3')
    statuses=['Established','In implementation','Not established',
              'Outside filter','No survey response']
    palette=['#005A8B','#009BDA','#D75E52','#D5E0E9','#EFF2F4']
    colors=dict(zip(statuses,palette))
    fig=go.Figure()
    shown=set()

    def rings(geometry):
        typ=geometry.get('type')
        coords=geometry.get('coordinates',[])
        if typ=='Polygon':
            return [coords]
        if typ=='MultiPolygon':
            return coords
        return []

    # Fit the respondent countries, not a generous continent-wide rectangle.
    # The viewport is independent of the active filter.
    (xmin,xmax),(ymin,ymax)=responding_country_map_bounds(
        geo,set(stats.index)
    )

    for feature in geo['features']:
        iso=feature.get('properties',{}).get('ISO_CC')
        if iso in stats.index:
            record=stats.loc[iso]
            name=tr(record['country'],lang)
            status=record['eoc_status']
            if selection is not None and record['country'] not in selection:
                status='Outside filter'
        else:
            name=tr('No survey response',lang)
            status='No survey response'
        xs,ys=[],[]
        for polygon in rings(feature.get('geometry',{})):
            # Exterior only; holes are rare and have negligible visual effect
            # at this scale. Break disconnected polygons with None.
            if polygon:
                for xy in polygon[0]:
                    xs.append(xy[0]);ys.append(xy[1])
                xs.append(None);ys.append(None)
        if not xs:
            continue
        fig.add_trace(go.Scatter(
            x=xs,y=ys,mode='lines',fill='toself',
            fillcolor=colors[status],
            line=dict(color='white',width=.65),
            name=tr(status,lang),
            legendgroup=status,showlegend=status not in shown,
            legendrank=statuses.index(status),
            hoveron='fills',
            hoverinfo='text',
            text=('<b>'+name+'</b><br>ISO: '+str(iso)+'<br>'+
                  ('Estado' if lang=='es' else 'Status')+': '+tr(status,lang)),
            hovertemplate='%{text}<extra></extra>',
        ))
        shown.add(status)

    fig.update_layout(
        dragmode=False,hovermode='closest',
        paper_bgcolor='#FFFFFF',plot_bgcolor='#FFFFFF',
    )
    fig.update_xaxes(range=[xmin,xmax],fixedrange=True,visible=False,
                     showgrid=False,zeroline=False,
                     constrain='domain')
    fig.update_yaxes(range=[ymin,ymax],fixedrange=True,visible=False,
                     showgrid=False,zeroline=False,scaleanchor='x',
                     scaleratio=1,constrain='domain')
    # The map itself fills the frame vertically; the legend overlays it.
    fig=style(fig,480,dict(l=4,r=4,t=5,b=5))
    # Apply this AFTER style(), otherwise the shared chart style
    # overwrites the map-specific vertical overlay legend.
    fig.update_layout(
        paper_bgcolor='#FFFFFF',plot_bgcolor='#FFFFFF',
        legend=dict(
            title=None,orientation='v',x=.018,y=.025,
            xanchor='left',yanchor='bottom',
            bgcolor='rgba(255,255,255,0.94)',
            bordercolor='#DFE9F1',borderwidth=1,
            font=dict(size=11,color=TEXT),
            itemsizing='constant',traceorder='normal',
        ),
    )
    return fig


def training_comparison(frame,lang='en'):
    """Single grouped comparison; percentages use each question's valid countries."""
    fig=go.Figure()
    labels=[tr(x,lang) for x in frame['area']]
    for name,ncol,dcol,color in [
        ('Completed','done_n','done_d',NAVY),
        ('Prioritized','priority_n','priority_d',CYAN),
    ]:
        n=frame[ncol].astype(int).tolist()
        den=frame[dcol].astype(int).tolist()
        percentages=[100*count/valid if valid else 0 for count,valid in zip(n,den)]
        captions=[f'{pct:.0f}%' if valid else '—'
                  for pct,valid in zip(percentages,den)]
        fig.add_bar(
            name=tr(name,lang),x=percentages,y=labels,orientation='h',
            marker_color=color,marker_line_width=0,
            text=captions,textposition='outside',cliponaxis=False,
            customdata=[[count,valid] for count,valid in zip(n,den)],
            hovertemplate=('<b>%{y}</b><br>'+tr(name,lang)+
                           ': %{x:.0f}% (%{customdata[0]}/%{customdata[1]})<extra></extra>'),
        )
    fig.update_layout(
        barmode='group',bargap=.32,bargroupgap=.10,
        legend=dict(orientation='h',x=0,y=1.085,
                    xanchor='left',yanchor='bottom',font=dict(size=11)),
    )
    fig.update_xaxes(
        range=[0,112],tickmode='array',tickvals=[0,25,50,75,100],
        ticktext=['0%','25%','50%','75%','100%'],
        showgrid=False,zeroline=False,showline=True,
        linecolor='#91A5B4',linewidth=1.3,
        ticks='outside',ticklen=5,tickcolor='#91A5B4',
        tickfont=dict(size=10,color=MUTED),fixedrange=True,
    )
    fig.update_yaxes(
        autorange='reversed',automargin=True,title=None,
        showgrid=True,gridcolor='#EBF1F5',gridwidth=1,
        showline=True,linecolor='#91A5B4',linewidth=1.3,
        tickfont=dict(size=11,color=TEXT),fixedrange=True,
    )
    fig=style(fig,max(590,len(labels)*75+120),
              dict(l=14,r=52,t=76,b=50))
    fig.update_layout(
        legend=dict(orientation='h',x=0,y=1.075,
                    xanchor='left',yanchor='bottom',font=dict(size=11)),
        paper_bgcolor='#FFFFFF',plot_bgcolor='#FFFFFF',
        hoverlabel=dict(bgcolor='white',font_size=11),
        dragmode=False,
    )
    return fig


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
       colorscale=[[0,'#F0F4F7'],[.249,'#F0F4F7'],[.25,'#FFF1E9'],[.749,'#FFF1E9'],[.75,'#E8F4FA'],[1,'#E8F4FA']],
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
                     showgrid=False,showline=True,linecolor=AXIS,title=None,zeroline=False)
    fig.update_yaxes(autorange='reversed',automargin=True,showgrid=True,gridcolor=GRID,showline=True,linecolor=AXIS,title=None)
    return style(fig,340,dict(l=8,r=15,t=14,b=30))