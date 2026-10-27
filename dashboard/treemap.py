"""Lightweight PAHO-colored, regional-only treemaps for the Overview.

Tile areas represent shares among valid responses, NOT country populations
or absolute numbers of responses. No country detail or click drilldowns.
"""
from __future__ import annotations

from html import escape
import math

from dashboard.i18n import tr

BLUE_SHADES=('#005A8B','#0872A5','#0E8CBE','#159DD0')
ORANGE_SHADES=('#A43D20','#B94A26','#CC592B','#DC703A')


def _split_tiles(items,x=0.0,y=0.0,w=100.0,h=100.0):
    """Deterministic binary treemap; each rectangle has proportional area."""
    if not items:
        return []
    if len(items)==1:
        return [(items[0],(x,y,w,h))]
    total=sum(item['weight'] for item in items)
    running=0
    best=min(range(1,len(items)),
             key=lambda i: abs(sum(v['weight'] for v in items[:i])-total/2))
    first,second=items[:best],items[best:]
    part=sum(item['weight'] for item in first)/total
    if w>=h:
        a=w*part
        return (_split_tiles(first,x,y,a,h)
                +_split_tiles(second,x+a,y,w-a,h))
    a=h*part
    return (_split_tiles(first,x,y,w,a)
            +_split_tiles(second,x,y+a,w,h-a))


def layout_treemap(records):
    """Input records: {label, numerator, denominator}; return rectangle positions.

    Zero rates retain a tiny minimum visual footprint so every record remains
    accessible, although all currently selected priorities have nonzero rates.
    """
    prepared=[]
    for index,item in enumerate(records):
        n=int(item['numerator']);d=int(item['denominator'])
        if d<0 or n<0 or n>d:
            raise ValueError('Treemap numerator and denominator must be valid counts')
        pct=100*n/d if d else 0.0
        prepared.append({**item,'numerator':n,'denominator':d,'pct':pct,
                         'weight':max(pct,0.4),'order':index})
    if not prepared:
        return []
    ordered=sorted(prepared,key=lambda row:(-row['weight'],row['order']))
    tiles=_split_tiles(ordered)
    return [{**item,'rect':rect} for item,rect in tiles]


def _tile_color(pct,mode):
    if mode=='available':
        return (BLUE_SHADES[0] if pct>=95 else BLUE_SHADES[1] if pct>=90
                else BLUE_SHADES[2] if pct>=85 else BLUE_SHADES[3])
    return (ORANGE_SHADES[0] if pct>=85 else ORANGE_SHADES[1] if pct>=75
            else ORANGE_SHADES[2] if pct>=65 else ORANGE_SHADES[3])


def overview_treemap_html(frame,mode='available',lang='en'):
    """Two informational treemaps: availability and inverse (gap) shares."""
    if mode not in ('available','gap'):
        raise ValueError('Treemap mode must be available or gap')
    records=[]
    for _,row in frame.iterrows():
        total=int(row['denominator'])
        positive=int(row['in_place'])
        n=positive if mode=='available' else total-positive
        records.append({'label':row['capacity'],'numerator':n,'denominator':total})
    tiles=layout_treemap(records)
    kind=tr('Available among valid responses',lang) if mode=='available' else tr('Not fully in place among valid responses',lang)
    elements=[]
    for tile in tiles:
        x,y,w,h=tile['rect']
        label=tr(tile['label'],lang)
        n,d=tile['numerator'],tile['denominator']
        pct=f"{tile['pct']:.0f}%"
        rate=f"{n}/{d}"
        tooltip=escape(f'{label} · {kind}: {pct} ({rate})',quote=True)
        color=_tile_color(tile['pct'],mode)
        elements.append(
            '<div class="eoc-overview-treemap-tile" style="'
            f'left:{x:.5f}%;top:{y:.5f}%;width:{w:.5f}%;height:{h:.5f}%">'
            '<div class="eoc-overview-treemap-face" style="background:'+color+
            '" title="'+tooltip+'" role="img" aria-label="'+tooltip+'">'
            '<span class="eoc-overview-treemap-label">'+escape(str(label))+'</span>'
            '<span class="eoc-overview-treemap-metric">'
            +pct+' <small>('+rate+')</small></span></div></div>'
        )
    caption=('Tile area reflects the share of valid responses reporting a capacity in place.'
             if mode=='available'
             else 'Tile area reflects the share of valid responses without a fully established capacity.')
    return ('<div class="eoc-overview-treemap-card">'
            '<div class="eoc-overview-treemap-plot" role="group" aria-label="'
            +escape(kind,quote=True)+'">'+''.join(elements)+'</div>'
            '<div class="eoc-overview-treemap-caption">'+escape(tr(caption,lang))+
            '</div></div>')
