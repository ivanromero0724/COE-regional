"""Schema-aware transformations for the 2026 PAHO COE-S survey.

Never exports personal identifiers, contacts or submission metadata. Original
xlsx remains the sole source for survey-derived numbers; narrative PDFs provide
context, not a competing data source.
"""
from __future__ import annotations
from functools import lru_cache
from pathlib import Path
import re
import unicodedata
import math
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
XLSX = ROOT / 'data' / 'Encuesta_OPS_2026_COEs.xlsx'
GPKG = ROOT / 'data' / 'geografia' / 'paises_americas.gpkg'

COUNTRY_LOOKUP = {
 'Argentina':('Argentina','ARG','South America'), 'Bahamas':('Bahamas','BHS','Caribbean'),
 'Belice':('Belize','BLZ','Central America'), 'Bolivia':('Bolivia','BOL','South America'),
 'Brasil':('Brazil','BRA','South America'), 'Colombia':('Colombia','COL','South America'),
 'Dominica':('Dominica','DMA','Caribbean'), 'Ecuador':('Ecuador','ECU','South America'),
 'El Salvador':('El Salvador','SLV','Central America'), 'Guatemala':('Guatemala','GTM','Central America'),
 'Honduras':('Honduras','HND','Central America'), 'Panamá':('Panama','PAN','Central America'),
 'Paraguay':('Paraguay','PRY','South America'), 'Perú':('Peru','PER','South America'),
 'Santa Lucía':('Saint Lucia','LCA','Caribbean'),
}
RESOURCE_LABELS = {55:"Dedicated room",56:"Shared room",57:"Virtual coordination",58:"Communications equipment",
                   59:"Display screens",60:"Backup generator",61:"Redundant internet",62:"Furniture"}
TRAINING_LABELS = ["EOC activation", "Incident management system", "Information management",
                   "Coordination & decisions", "Damage & needs assessment", "Rapid situation analysis",
                   "Multidisciplinary response teams", "After-action review"]
HAZARD_LABELS={23:"Geological / weather",24:"Biological / epidemic",25:"Social / human-caused",26:"Technological"}
OPERATING={"a":"Not formally defined","b":"Response only","c":"Response + monitoring","d":"24/7 continuous"}
ACTIVATION={"a":"Under 2 hours","b":"2–6 hours","c":"Over 6 hours","d":"Not defined","e":"Not defined"}
STATUS_LABELS={"a":"Established", "b":"Not established", "c":"In implementation"}
NETWORK_NAMES={153:"EOC-NET",154:"EMT initiative",155:"GOARN"}
COOPERATION_SKILLS={
126:'Strategic leadership',127:'EOC strengthening',128:'Incident management & coordination',
129:'Surveillance & outbreak investigation',130:'Laboratory',131:'Emergency Medical Teams',
132:'Infection prevention & control',133:'Risk communication',134:'Information & geospatial analysis',
135:'Logistics & supplies',136:'Water, sanitation & hygiene',137:'Mental health & psychosocial support',
138:'Training & response evaluation'
}
COOPERATION_MODES={
144:'Exchange of experience',145:'Remote technical assistance',146:'Facilitators / instructors',
147:'National expert mobilization',148:'Deployments to other countries',149:'Mentoring',
150:'Availability requires assessment'
}



def norm(value):
    return ''.join(t for t in unicodedata.normalize('NFKD',str(value).lower()) if not unicodedata.combining(t))


def clean(value):
    if value is None or pd.isna(value): return ""
    return re.sub(r'\s+',' ',str(value)).strip()


def letter(value):
    v=norm(clean(value))
    m=re.match(r'^([a-z])\.\s',v)
    return m.group(1) if m else None


def binary(value):
    if pd.isna(value):return None
    v=clean(value).lower()
    if v in ('1','1.0','true','yes','sí','si'): return True
    if v in ('0','0.0','false','no'): return False
    return None


def public_narrative(value):
    txt=clean(value)[:1400]
    txt=re.sub(r'(?i)\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b','[email redacted]',txt)
    txt=re.sub(r'(?<!\d)(?:\+?\d[\d .()-]{8,}\d)(?!\d)','[number redacted]',txt)
    return txt


def institution(value, country):
    v=norm(clean(value))
    if 'instituto nacional' in v:
        return 'National Institute of Health (INS)' if country=='Colombia' else 'National institute of health'
    if 'secretaria de salud' in v: return 'Secretariat of Health'
    if 'ministerio' in v:
        return 'Ministry of Health and Social Protection' if country=='Colombia' else 'Ministry of Health'
    if 'otro' in v:return 'Other reporting institution'
    return 'Reporting institution'


def code(row,ix):
    return letter(row.iloc[ix])


def category_or_na(row,ix,labels):
    return labels.get(code(row,ix),'Not reported')


def norm_network(v):
    x=norm(clean(v))
    if not x: return 'Not reported'
    if 'no participa' in x and 'interes' in x:return 'Interested'
    if 'participa' in x and 'no participa' not in x:return 'Participating'
    if 'no participa' in x:return 'Not participating'
    return 'Not reported'



def create_records(raw:pd.DataFrame)->tuple[pd.DataFrame,pd.DataFrame]:
    if raw.shape[1]<157:raise ValueError('Survey schema has fewer than 157 expected columns.')
    profiles=[]; survey_rows=[]
    for ix in range(len(raw)):
        r=raw.iloc[ix]
        native=clean(r.iloc[7]); mapping=COUNTRY_LOOKUP.get(native)
        if not mapping:continue
        country,iso,subregion=mapping
        inst=institution(r.iloc[8],country)
        eo=STATUS_LABELS.get(code(r,14),'Not reported')
        d={
         'record_id':f'{iso}-{ix+2:03d}', 'source_excel_row':ix+2,
         'country':country,'iso3':iso,'subregion':subregion,'institution':inst,
         'eoc_status':eo,'operating_mode':category_or_na(r,27,OPERATING),
         'activation':category_or_na(r,39,ACTIVATION),
         # Survey question 15: formal document describing the EOC-S mandate and procedures.
         'formal_document': (True if code(r,28)=='a' else False if code(r,28)=='b' else None),
         'established':clean(r.iloc[17]) or 'Not reported',
         'staff_24_7':pd.to_numeric(r.iloc[67],errors='coerce'),
         'mapped_workforce': (('actualiza periodicamente' in norm(clean(r.iloc[123]))) if clean(r.iloc[123]) else None),
        }
        for col,label in HAZARD_LABELS.items():
            c=code(r,col)
            d[label]=dict(a=0,b=1,c=2,d=3).get(c,np.nan)
        for col,label in RESOURCE_LABELS.items():d[label]=binary(r.iloc[col])
        for a,label in enumerate(TRAINING_LABELS):
            d['Completed: '+label]=binary(r.iloc[83+a]); d['Priority: '+label]=binary(r.iloc[94+a])
        for col,name in NETWORK_NAMES.items():d[name]=norm_network(r.iloc[col])
        for col,name in COOPERATION_SKILLS.items():d['Skill: '+name]=binary(r.iloc[col])
        for col,name in COOPERATION_MODES.items():d['Mode: '+name]=binary(r.iloc[col])
        for col in (29,32,33,36,37,40,41,42,43,46,47,49,50,51,66,68,77,78,80,81,105,107,108,109,110):
            d[f'Q_{col}']=code(r,col)
        # Only nonpersonal narrative fields; never names/telephone/email (9–12).
        for col,name in ((112,'Recent activations (original language)'),
                         (120,'Reported strengths (original language)'),
                         (121,'Improvement areas (original language)')):
            d[name]=public_narrative(r.iloc[col])
        profiles.append(d)
        survey_rows.append({'country':country,'iso3':iso,'record_id':d['record_id']})
    if not profiles: raise ValueError('No recognized country records in the first worksheet.')
    frame=pd.DataFrame(profiles)
    return frame,raw


@lru_cache(maxsize=3)
def load_data(path:str=str(XLSX)):
    raw=pd.read_excel(path,sheet_name=0,engine='openpyxl')
    return create_records(raw)


def country_aggregate(df:pd.DataFrame)->pd.DataFrame:
    """One country = one observation. Any institution may report an in-place capacity.

    Ordinal event bands are not summed; use the highest reported category.
    """
    out=[]
    for country,g in df.groupby('country',sort=True):
        row={'country':country,'iso3':g.iso3.iloc[0], 'subregion':g.subregion.iloc[0],
             'institutions':len(g),
             'staff_24_7':g.staff_24_7.max(skipna=True),
             'mapped_workforce': (any(bool(x) for x in g.mapped_workforce if x is not None)
                                  if g.mapped_workforce.notna().any() else None),
             'eoc_status':('Established' if (g.eoc_status=='Established').any()
                           else 'In implementation' if (g.eoc_status=='In implementation').any()
                           else 'Not established'),
             'operating_mode': next((v for v in ('24/7 continuous','Response + monitoring','Response only','Not formally defined') if v in set(g.operating_mode)), 'Not reported'),
             'activation':next((v for v in ('Under 2 hours','2–6 hours','Over 6 hours','Not defined') if v in set(g.activation)),'Not reported'),
             'formal_document': (any(v == True for v in g.formal_document) if g.formal_document.notna().any() else None)}
        for label in HAZARD_LABELS.values():
            row[label]=g[label].max(skipna=True)
        for label in RESOURCE_LABELS.values():
            a=g[label].dropna().tolist();row[label]=(any(bool(x) for x in a) if a else None)
        for label in TRAINING_LABELS:
            for t in ('Completed: ','Priority: '):
                a=g[t+label].dropna().tolist();row[t+label]=(any(bool(x) for x in a) if a else None)
        for name in list(COOPERATION_SKILLS.values())+list(COOPERATION_MODES.values()):
            prefix='Skill: ' if name in COOPERATION_SKILLS.values() else 'Mode: '
            col=prefix+name
            v=g[col].dropna().tolist()
            row[col]=(any(bool(q) for q in v) if v else None)
        for network in NETWORK_NAMES.values():
            x=g[network].tolist()
            row[network]='Participating' if 'Participating' in x else 'Interested' if 'Interested' in x else 'Not participating' if 'Not participating' in x else 'Not reported'
        for q in [29,32,33,36,37,40,41,42,43,46,47,49,50,51,66,68,77,78,80,81,105,107,108,109,110]:
            codes=[str(z) for z in g[f'Q_{q}'].dropna() if z]
            row[f'Q_{q}']=','.join(sorted(set(codes)))
        out.append(row)
    return pd.DataFrame(out)


def country_capacity(c:pd.Series,col:int,positive:tuple[str,...])->bool|None:
    """Strict attainment: OR of qualifying institution choices, not score >= 60."""
    if col in RESOURCE_LABELS:
        v=c.get(RESOURCE_LABELS[col]);return None if pd.isna(v) else bool(v)
    if col==67:
        v=c.get('staff_24_7');return None if pd.isna(v) else float(v)>0
    if col==123:
        # The survey asked this later; countries that were not asked are missing,
        # not negative. Aggregator stores answered flag separately.
        return bool(c.get('mapped_workforce')) if pd.notna(c.get('mapped_workforce')) else None
    raw=clean(c.get('Q_'+str(col)))
    if not raw:return None
    return any(v in set(raw.split(',')) for v in positive)


# A capacity is in place only for explicitly positive / fully established answers.
# Partial and developing states do not count. Colombia is an OR of institutions.
CAPACITIES={
 'Legal authority & governance':[
   ('Formal legal framework',29,('d','e')),('Decision-making enabled',32,('d','e')),
   ('Strategic committee established',46,('a',)),('Formal intersectoral coordination',41,('c',)),
   ('High DRM integration',42,('d',)),('Institutionally allocated finance',36,('d','e')),
   ('National + subnational mandate',40,('b',)),
 ],
 'Policies, plans & procedures':[
   ('In national response plan',33,('a',)),('Manual or SOP available',37,('a',)),
   ('Incident management system used',47,('a',)),('Systematic risk assessment',49,('e',)),
   ('Incident action plan every activation',43,('a',)),('Documented roles',68,('a',)),
 ],
 'Information systems & standards':[
   ('Situation room integrated',109,('a',)),('Information management & monitoring',51,('a',)),
   ('Formal SITREP process',110,('d',)),('Structured exchange',105,('d',)),
   ('Integrated/interoperable platform',107,('d','e')),('Information gaps infrequent',108,('d',)),
 ],
 'Infrastructure & support':[
   ('Dedicated operations room',55,()),('Virtual coordination space',57,()),
   ('Backup power generator',60,()),('Redundant internet connection',61,()),
   ('Operational capacity to implement decisions',50,('d','e')),
 ],
 'Human resources & surge':[
   ('Coordinator formally designated',66,('a',)),('Permanent staff on 24/7 duty',67,()),
   ('Formal surge procedure',77,('d','e')),('Updated surge roster',78,('a',)),
   ('Coordinates rapid response deployment',80,('a',)),('Formally participates in GHEC',81,('a',)),
   ('Updated deployable workforce mapping',123,()),
 ],
}

def capacity_table(countries:pd.DataFrame)->pd.DataFrame:
    rows=[]
    for group,items in CAPACITIES.items():
        for label,col,valid in items:
            statuses=[country_capacity(r,col,valid) for _,r in countries.iterrows()]
            total=sum(s is not None for s in statuses)
            n=sum(s is True for s in statuses)
            rows.append({'component':group,'capacity':label,'in_place':n,'denominator':total,
                         'percent':(100*n/total if total else np.nan),'col':col})
    # Infrastructure and workforce directly use binary columns and separate indicators.
    for group,items in (('Infrastructure',RESOURCE_LABELS.values()),
                        ('Training (completed)',('Completed: '+n for n in TRAINING_LABELS))):
        for label in items:
            states=countries[label].tolist()
            vals=[v for v in states if pd.notna(v)]
            rows.append({'component':group,'capacity':label.replace('Completed: ',''),
                         'in_place':sum(bool(v) for v in vals),'denominator':len(vals),
                         'percent':(100*sum(bool(v) for v in vals)/len(vals) if vals else np.nan), 'col':-1})
    return pd.DataFrame(rows)



def safe_csv(df):
    # Never include source row narrative or personal fields in downloadable tables.
    base=['country','iso3','subregion','eoc_status','operating_mode','activation','institutions','staff_24_7']
    return df.loc[:,[c for c in base if c in df.columns]].to_csv(index=False).encode('utf-8-sig')