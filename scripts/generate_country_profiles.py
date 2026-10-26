#!/usr/bin/env python3
"""Reproducible PAHO EOC country fact sheets (one Letter page per country).

Source: first worksheet in data/Encuesta_OPS_2026_COEs.xlsx.
No external APIs, credentials or machine translation; controlled survey answers are
translated via deterministic rules. Respondent names, phone numbers and emails
are never printed. Non-standard free text is not published verbatim.
"""
from __future__ import annotations
import argparse, collections, datetime as dt, hashlib, html, re, unicodedata, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT

HERE = Path(__file__).resolve().parents[1]
BLUE = '#005A8B'          # PAHO-inspired institutional navy
BRIGHT = '#009BDA'        # PAHO cyan
ORANGE = '#F36B32'        # accent
INK = '#143A56'
MUTED = '#587185'
PALE = '#EDF5FA'
PALE2 = '#F5F9FB'
LINE = '#D8E5EE'
GREEN = '#279E84'
WHITE = '#FFFFFF'
UNKNOWN = 'Not reported'
PAGE_W, PAGE_H = letter

COUNTRIES = {
    'Panamá':'Panama','Paraguay':'Paraguay','Bolivia':'Bolivia','Ecuador':'Ecuador',
    'Perú':'Peru','Guatemala':'Guatemala','Belice':'Belize','Bahamas':'Bahamas',
    'Honduras':'Honduras','Colombia':'Colombia','El Salvador':'El Salvador',
    'Santa Lucía':'Saint Lucia','Dominica':'Dominica','Argentina':'Argentina','Brasil':'Brazil',
}

# Manually edited English paraphrases of current survey narrative, for readability;
# all new/modified records use safe data-derived statements instead of untranslated text.
CURATED = {
 'Argentina':(
  ['Multidisciplinary structure within the Ministry of Health', 'Monitoring coordinated with national emergency structures', 'Field-deployment capacity supporting provinces'],
  ['Formalize the health EOC through a resolution', 'Approve internal operating regulations', 'Increase activation and deployment exercises']),
 'Bahamas':(
  ['Rapid formal activation', 'Systematic risk assessment and event grading', 'Regular formal intersectoral coordination'],
  ['Identify and train response personnel', 'Establish a dedicated operations space', 'Develop in-country Emergency Medical Team capacity']),
 'Belize':(
  ['Formal links with the health cluster and national emergency agency', 'Timely situation reports', 'Established mechanisms for national activation'],
  ['Conduct simulation exercises for recurrent hazards', 'Train teams in incident management and simulation design', 'Strengthen EOC equipment']),
 'Bolivia':(
  ['Defined functions across emergency-management phases', 'Inter-institutional coordination and technical leadership', 'Regular cross-sector meetings'],
  ['Improve interoperability across information systems', 'Retain trained personnel at subnational level', 'Strengthen tools linking surveillance and response']),
 'Brazil':(
  ['Coordination across federal, state and municipal levels', 'Links with surveillance and situational monitoring', 'Experience managing epidemics and disasters'],
  ['Formalize activation and operational protocols', 'Maintain dedicated staff and an updated rapid-response roster', 'Strengthen dedicated infrastructure and technology']),
 'Colombia':(
  ['Trained multidisciplinary personnel', 'Established response and monitoring capabilities', 'Institutional commitment to emergency coordination'],
  ['Improve interoperable information systems', 'Strengthen rapid-response team readiness', 'Formalize procedures and communications capacity']),
 'Dominica':(
  ['Existing emergency infrastructure', 'Multisectoral surveillance and response arrangements', 'Documented operating guidance'],
  ['Improve resilient connectivity for major hurricanes and earthquakes']),
 'El Salvador':(
  ['Permanent personnel assigned', 'Established legal framework', 'Infrastructure and equipment available'],
  ['Strengthen information-management systems', 'Improve sustainable financing', 'Expand staffing capacity']),
 'Guatemala':(
  ['Officially established emergency coordination structure', 'Documented integration and functions', 'Dedicated physical space and personnel'],
  ['Update standard operating procedures', 'Strengthen radio communications', 'Develop real-time information systems']),
 'Honduras':(
  ['Formal intersectoral coordination mechanisms', 'Risk assessment used during events', 'Experience using an incident-management approach'],
  ['Advance the legal mandate and procedures', 'Establish sustainable financing and surge staffing', 'Build workforce and operating capacity']),
 'Panama':(
  ['Organization and functioning manual available', 'Supported by a ministerial resolution', 'Fixed structure with designated personnel'],
  ['Secure dedicated operating finance', 'Strengthen transportation and satellite communications', 'Expand physical operating space']),
 'Paraguay':(
  ['Standardized incident-management roles', 'Coordination across institutional partners', 'Experience integrating situation information'],
  ['Improve resilient emergency telecommunications', 'Strengthen decentralized team training', 'Develop real-time digital dashboards']),
 'Peru':(
  ['Personnel and infrastructure formally assigned', 'Countrywide monitoring network', 'Legal instruments defining responsibilities'],
  ['Modernize emergency reporting platforms', 'Address turnover among staff', 'Expand specialized training opportunities']),
 'Saint Lucia':(
  ['Established intra- and inter-agency coordination', 'Experience in emergency response', 'Integration with national disaster management'],
  ['Establish dedicated EOC staffing', 'Document procedures for activation and operation', 'Upgrade data and information-sharing technology']),
}

# XLSX reader implemented with standard-library XML for reliable GitHub Actions
# execution without a spreadsheet engine changing source cell types or labels.
def read_first_sheet(path: Path) -> list[list[object]]:
    ns = {'x':'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
          'r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
          'p':'http://schemas.openxmlformats.org/package/2006/relationships'}
    with zipfile.ZipFile(path) as z:
        ss = []
        if 'xl/sharedStrings.xml' in z.namelist():
            root = ET.fromstring(z.read('xl/sharedStrings.xml'))
            ss = [''.join(t.text or '' for t in si.findall('.//x:t',ns)) for si in root.findall('x:si',ns)]
        book = ET.fromstring(z.read('xl/workbook.xml'))
        first = book.find('x:sheets/x:sheet',ns)
        if first is None: raise ValueError('Excel workbook has no sheets')
        rel = first.attrib.get('{'+ns['r']+'}id')
        rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        target = next((el.attrib['Target'] for el in rels if el.attrib.get('Id')==rel), None)
        if not target: raise ValueError('Cannot resolve first worksheet')
        sheet_path = target.lstrip('/') if target.startswith('/') else 'xl/'+target
        sheet_path = sheet_path.replace('xl/xl/','xl/')
        root = ET.fromstring(z.read(sheet_path))
        rows = []
        for row in root.findall('.//x:sheetData/x:row',ns):
            cells = {}
            for cell in row.findall('x:c',ns):
                m = re.match(r'([A-Z]+)',cell.attrib.get('r',''))
                if not m: continue
                idx = 0
                for cc in m.group(1): idx = idx*26+ord(cc)-64
                idx -= 1
                t = cell.attrib.get('t')
                if t == 'inlineStr':
                    val = ''.join(x.text or '' for x in cell.findall('.//x:t',ns))
                else:
                    v = cell.find('x:v',ns)
                    val = v.text if v is not None else None
                    if t=='s' and val is not None: val = ss[int(val)]
                    elif t in ('n',None) and val is not None:
                        try: val = float(val) if '.' in val else int(val)
                        except ValueError: pass
                    elif t=='b' and val is not None: val = val=='1'
                cells[idx] = val
            width = max(cells, default=-1)+1
            rows.append([cells.get(i) for i in range(width)])
    if not rows: raise ValueError('No rows found in first sheet')
    cols = len(rows[0]); rows = [(r+[None]*cols)[:cols] for r in rows]
    return rows

def clean(v):
    if v is None: return ''
    return re.sub(r'\s+', ' ', str(v)).strip()

def val(row,idx):
    return clean(row[idx]) if idx<len(row) else ''

def number(row,idx):
    try: return int(float(val(row,idx)))
    except (ValueError,TypeError): return None

def yes(row, idx):
    v=val(row,idx)
    if not v: return None
    return v.lower().startswith('a. sí') or v.lower().startswith('a. si') or v.lower() in ('yes','1')

def selected(row,idx):
    v=val(row,idx).lower()
    if v in ('1','true','yes','sí','si'): return True
    if v in ('0','false','no'): return False
    return None

def normalize(s):
    return ''.join(c for c in unicodedata.normalize('NFKD',s.lower()) if not unicodedata.combining(c))

def choice(row,idx):
    s=normalize(val(row,idx)); return (s[:1] if re.match(r'^[a-z]\.\s',s) else '')

def date_str(row):
    raw=val(row,6)
    try:
        if re.match(r'^\d+(\.\d+)?$',raw):
            return (dt.datetime(1899,12,30)+dt.timedelta(days=float(raw))).strftime('%d %b %Y')
    except (ValueError,OverflowError): pass
    if raw:
        try: return dt.datetime.fromisoformat(raw.replace('Z','')).strftime('%d %b %Y')
        except ValueError: return raw[:20]
    return UNKNOWN

def submit_key(row):
    raw=val(row,160)
    try:return dt.datetime.fromisoformat(raw.replace('Z','+00:00')).timestamp()
    except (ValueError,TypeError):return 0

def status(row):
    c=choice(row,14)
    return True if c=='a' else False if c=='b' else None

def organization(row):
    name=val(row,15)
    fallback=val(row,8)
    # English display names for known 2026 centres; applied only when a source
    # term matches. Future new institutions retain the respondent's proper name.
    n=normalize(name)
    if n=='codes':return 'CODES - Health Emergency Operations Centre'
    if 'cove' in n:return 'COVE - Events Operations & Surveillance Centre'
    if 'mesa tecnica sectorial' in n:return 'Sectoral Technical Board for Health & Nutrition'
    if 'coes salud' in n:return 'COES - Health Sector Emergency Operations Centre'
    if 'operacoes de emergencias em saude publica' in n:return 'Public Health Emergency Operations Centre (COE)'
    if 'grupo de gestion del riesgo' in n:return 'Public Health EOC - National Institute of Health (INS)'
    if n=='coe salud':return 'Health EOC - Ministry of Health and Social Protection'
    if 'emergencias de salud publica' in n or 'emergencias en salud publica' in n:return 'Public Health Emergency Operations Centre'
    if n in ('heoc','health emergency operations center'):return 'Health Emergency Operations Centre (HEOC)'
    if 'mohw emergency operation center' in n:return 'MOHW Emergency Operations Centre'
    if not name and 'instituto nacional de salud' in normalize(fallback):return 'National Institute of Health'
    if not name and 'ministerio' in normalize(fallback):return 'Ministry of Health - reporting institution'
    if not name and 'secretaria' in normalize(fallback):return 'Secretariat of Health - reporting institution'

    if name and normalize(name) not in ('ninguno','no aplica'):
        # Only fixed, non-personal labels are translated; proper names preserved.
        name = re.sub(r'Centro de Operaciones (de |en )?(Emergencias|Emergencia)',
                      'Emergency Operations Centre',name,flags=re.I)
        name = re.sub(r'CENTRO DE OPERACIONES DE EMERGENCIAS EN SALUD','Health Emergency Operations Centre',name,flags=re.I)
        return name[:108]
    if fallback:
        n=normalize(fallback)
        if 'instituto nacional' in n:return 'National Institute of Health'
        if 'ministerio' in n:return 'Ministry of Health'
        if 'secretaria' in n:return 'Secretariat of Health'
    return 'Reporting institution'

def english_mode(row):
    t=normalize(val(row,27))
    if choice(row,27)=='d' or '24 horas' in t or '24/7' in t:return '24/7 continuous'
    if choice(row,27)=='c':return 'Emergencies + monitoring'
    if choice(row,27)=='b':return 'Emergencies only'
    return 'Not formally defined'

def english_activation(row):
    s=normalize(val(row,39))
    if 'menos de 2' in s:return '< 2 hours'
    if '2 a 6' in s or 'entre 2' in s:return '2-6 hours'
    if 'mas de 6' in s or '6 horas' in s or 'mayor a 6' in s:return '> 6 hours'
    return 'Not defined'

def english_mandate(row):
    s=normalize(val(row,40))
    if 'subnacional' in s or ('nacional' in s and 'local' in s):return 'National + subnational'
    if 'nacional' in s:return 'National'
    return 'Not defined'

def tiny_choice(row,idx, opts, fallback=UNKNOWN):
    ch=choice(row,idx)
    return opts.get(ch,fallback)

def row_items(row):
    # English and short strings; true survey data converted to reproducible labels.
    return [
      ('Legal framework',tiny_choice(row,29,{'a':'None','b':'Initial','c':'Developing','d':'Functional','e':'Consolidated'})),
      ('National plan', 'Yes' if yes(row,33) else 'No' if yes(row,33) is False else UNKNOWN),
      ('Formal SOP',tiny_choice(row,37,{'a':'Yes','b':'No','c':'In development'})),
      ('Operating finance',tiny_choice(row,36,{'a':'None','b':'Ad hoc','c':'Developing','d':'Functional','e':'Consolidated'})),
      ('Incident management',tiny_choice(row,47,{'a':'Used','b':'Not used'})),
      ('Incident action plan',tiny_choice(row,43,{'a':'Systematic','b':'Sometimes','c':'No'})),
      ('Risk assessment',tiny_choice(row,49,{'a':'None','b':'Informal','c':'Occasional','d':'Event graded','e':'Systematic'})),
      ('Strategic committee',tiny_choice(row,46,{'a':'Formal','b':'Developing','c':'No','d':'Unknown'})),
      ('EOC coordinator',tiny_choice(row,66,{'a':'Formal','b':'Informal','c':'No'})),
      ('Documented roles',tiny_choice(row,68,{'a':'Formal','b':'Partial','c':'No'})),
      ('Surge staffing',tiny_choice(row,77,{'a':'None','b':'Ad hoc','c':'Developing','d':'Functional','e':'Consolidated'})),
      ('Trained roster',tiny_choice(row,78,{'a':'Updated','b':'Outdated','c':'In progress','d':'No','e':'Unknown'})),
      ('Team deployment',tiny_choice(row,80,{'a':'Leads','b':'Supports','c':'No'})),
      ('Intersectoral links',tiny_choice(row,41,{'a':'Health sector only','b':'Occasional','c':'Formal & regular'})),
      ('Disaster-risk integration',tiny_choice(row,42,{'a':'None','b':'Limited','c':'Moderate','d':'High'})),
      ('International cooperation',tiny_choice(row,44,{'a':'Direct','b':'Via mechanism','c':'Inter-agency','d':'Limited','e':'None'})),
      ('Information tools',tiny_choice(row,107,{'a':'None','b':'Basic','c':'Institutional','d':'Integrated','e':'Interoperable'})),
      ('SITREP process',tiny_choice(row,110,{'a':'No','b':'Informal','c':'Irregular','d':'Formal & regular'})),
      ('Situation room',tiny_choice(row,109,{'a':'Integrated','b':'Not integrated'})),
      ('Logistics readiness',tiny_choice(row,50,{'a':'None','b':'Initial','c':'Developing','d':'Functional','e':'Consolidated'})),
    ]

def score_by_index(row,idx):
    # 0-100 descriptive survey item completion/maturity rubric; missing excluded.
    scales={
       29: {'a':0,'b':25,'c':50,'d':75,'e':100},
       33: {'a':100,'b':0}, 37:{'a':100,'b':0,'c':45},
       36:{'a':0,'b':25,'c':50,'d':75,'e':100},
       47:{'a':100,'b':0},43:{'a':100,'b':50,'c':0},
       49:{'a':0,'b':25,'c':50,'d':75,'e':100},
       46:{'a':100,'b':50,'c':0},
       66:{'a':100,'b':50,'c':0},68:{'a':100,'b':50,'c':0},
       77:{'a':0,'b':25,'c':50,'d':75,'e':100},
       78:{'a':100,'b':40,'c':35,'d':0},80:{'a':100,'b':50,'c':0},
       41:{'a':0,'b':50,'c':100},42:{'a':0,'b':35,'c':65,'d':100},
       44:{'a':100,'b':85,'c':75,'d':30,'e':0},
       107:{'a':0,'b':25,'c':50,'d':75,'e':100},
       110:{'a':0,'b':30,'c':60,'d':100},109:{'a':100,'b':0},
       50:{'a':0,'b':25,'c':50,'d':75,'e':100},
    }
    code=choice(row,idx)
    return scales.get(idx,{}).get(code)

DOMAINS=[('Governance & legal',[29,33,37,36]),
         ('Operations & decisions',[47,43,49,46,50]),
         ('Human resources',[66,68,77,78,80]),
         ('Information management',[107,110,109]),
         ('Coordination',[41,42,44])]

def scores(row):
    out=[]
    for label,cols in DOMAINS:
        values=[score_by_index(row,j) for j in cols]
        vals=[v for v in values if v is not None]
        out.append((label,round(sum(vals)/len(vals)) if vals else None,len(vals),len(cols)))
    return out

def hazards(row):
    labels={'a':'None','b':'1-2 events','c':'3-5 events','d':'> 5 events'}
    return [(name,labels.get(choice(row,j),UNKNOWN)) for name,j in [('Geological / weather',23),('Biological / epidemics',24),('Social / human-caused',25),('Technological',26)]]

RESOURCES=[('Dedicated room',55),('Shared room',56),('Virtual coordination',57),('Communications',58),('Situation displays',59),('Backup power',60),('Redundant internet',61),('Team workstations',62)]
TRAININGS=[('EOC activation',83,94),('Incident management',84,95),('Information management',85,96),
  ('Coordination',86,97),('Damage / needs assessment',87,98),('Rapid situation analysis',88,99),
  ('Rapid response teams',89,100),('After-action reviews',90,101)]

CURATED_SIGNATURES = {'Panama': 'bd7da43e7b44fb87', 'Paraguay': 'ee315e6adb390bb3', 'Bolivia': '862df08aadd730f8', 'Peru': '198a04eda7ed8882', 'Guatemala': 'f0f313fa8bf22d6e', 'Belize': 'cbdb58f0117ed3f4', 'Bahamas': 'e9800d5ae850df9f', 'Honduras': 'cbe5cfdf7c2118a9', 'Colombia': '06f79df4eb783766', 'El Salvador': 'b55bf8c57996674d', 'Saint Lucia': 'ff82285413a2ede0', 'Dominica': '18cf663007b377a6', 'Argentina': '0f99c85787690491', 'Brazil': '393c393d08c0d1b9'}  # 2026 source narrative fingerprints

def narrative_for(country,row):
    digest=hashlib.sha256((val(row,120)+'|'+val(row,121)).encode('utf-8')).hexdigest()[:16]
    if country in CURATED and CURATED_SIGNATURES.get(country)==digest:
        return CURATED[country]
    return themes(row,'strength'), themes(row,'improve')

def themes(row, kind):
    # Human-readable insights synthesized from closed questions, never from personal fields.
    v={k:z for k,z in row_items(row)}
    if kind=='strength':
        candidates=[('Institutional SOPs are in place',v['Formal SOP']=='Yes'),
          ('Incident management is used in response',v['Incident management']=='Used'),
          ('Risk assessment supports activation decisions',v['Risk assessment'] in ('Systematic','Event graded')),
          ('Roles are documented',v['Documented roles']=='Formal'),
          ('Structured SITREPs support response',v['SITREP process']=='Formal & regular'),
          ('Intersectoral coordination is established',v['Intersectoral links']=='Formal & regular'),
          ('An integrated situation room is available',v['Situation room']=='Integrated'),
          ('Staffing and surge arrangements are functional',v['Surge staffing'] in ('Functional','Consolidated'))]
    else:
        candidates=[('Formalize operating procedures',v['Formal SOP'] in ('No','In development')),
           ('Strengthen institutional mandate',v['Legal framework'] in ('None','Initial','Developing')),
           ('Establish or update trained personnel rosters',v['Trained roster'] in ('No','Outdated')),
           ('Improve financing predictability',v['Operating finance'] in ('None','Ad hoc','Developing')),
           ('Improve incident-action planning',v['Incident action plan'] in ('No','Sometimes')),
           ('Strengthen interoperable information tools',v['Information tools'] in ('None','Basic','Institutional')),
           ('Formalize intersectoral coordination',v['Intersectoral links'] in ('Health sector only','Occasional')),
           ('Strengthen surge staffing procedures',v['Surge staffing'] in ('None','Ad hoc','Developing'))]
    found=[s for s,flag in candidates if flag]
    return (found or ['No specific areas identified from closed-question responses'])[:3]

# Font files are distributed with the GitHub-hosted Ubuntu runner.
def init_fonts():
    files=[('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','DejaVu'),
           ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf','DejaVuBold')]
    for path,name in files:
        if not Path(path).exists():raise RuntimeError(f'Font missing: {path}')
        pdfmetrics.registerFont(TTFont(name,path))

FONT='DejaVu'; BOLD='DejaVuBold'
def col(h):return HexColor(h)
def text(c,s,x,top,size=8,color=INK,bold=False):
    c.setFont(BOLD if bold else FONT,size);c.setFillColor(col(color));c.drawString(x,PAGE_H-top-size,s)
def right(c,s,right_x,top,size=8,color=INK,bold=False):
    c.setFont(BOLD if bold else FONT,size);c.setFillColor(col(color));c.drawRightString(right_x,PAGE_H-top-size,s)
def rect(c,x,top,w,h,fill=WHITE,r=0,stroke=None,lw=.7):
    c.setLineWidth(lw)
    c.setStrokeColor(col(stroke or fill));c.setFillColor(col(fill))
    c.roundRect(x,PAGE_H-top-h,w,h,r,fill=1,stroke=bool(stroke))
def rule(c,x1,x2,top,color=LINE,lw=.7):
    c.setStrokeColor(col(color));c.setLineWidth(lw);c.line(x1,PAGE_H-top,x2,PAGE_H-top)
def paragraph(c,s,x,top,width,size=7.0,color=INK,leading=None,maxheight=None,bold=False):
    st=ParagraphStyle('p',fontName=BOLD if bold else FONT,fontSize=size,leading=leading or (size*1.33),textColor=col(color),spaceAfter=0,allowWidows=0,allowOrphans=0)
    p=Paragraph(html.escape(str(s)).replace('\n','<br/>'),st)
    _,h=p.wrap(width,maxheight or 999)
    if maxheight is not None and h>maxheight:
        # Preserve layout and avoid clipping by fitting smaller font; long free text excluded.
        for k in [size-.4,size-.8,size-1.2]:
            st.fontSize=max(5,k);st.leading=st.fontSize*1.26;p=Paragraph(html.escape(str(s)),st);_,h=p.wrap(width,maxheight)
            if h<=maxheight:break
    p.drawOn(c,x,PAGE_H-top-h)
    return h

def heading(c,s,x,top,width):
    text(c,s.upper(),x,top,7.1,BLUE,True)
    rule(c,x,x+width,top+15)

def logo_header(c):
    # Refers to tracked original repo paths at runtime (no external requests).
    rect(c,0,0,PAGE_W,7,BLUE)
    rect(c,455,0,PAGE_W-455,7,ORANGE)
    p1=HERE/'logos'/'logo_EOC.png'; p2=HERE/'logos'/'PAHO_eng.png'
    if not (p1.exists() and p2.exists()):raise FileNotFoundError('Both tracked logos must exist in logos/')
    c.drawImage(ImageReader(str(p1)),40,PAGE_H-65,width=143,height=48,mask='auto',preserveAspectRatio=True,anchor='sw')
    c.drawImage(ImageReader(str(p2)),330,PAGE_H-66,width=238,height=47,mask='auto',preserveAspectRatio=True,anchor='sw')
    text(c,'EOC-NET  /  THE AMERICAS',188,29,7.0,BLUE,True)
    text(c,'COUNTRY FACT SHEETS · 2026',188,43,6.5,ORANGE,True)
    rule(c,40,PAGE_W-40,78,BLUE,1.0)

def header(c,country,rows,page_idx,total):
    logo_header(c)
    rect(c,40,95,36,39,PALE,r=7)
    text(c,'EOC',46,107,11,BLUE,True)
    text(c,country,88,93,22,BLUE,True)
    text(c,('ONE REPORTING INSTITUTION' if len(rows)==1 else f'{len(rows)} SURVEY RESPONSES  /  INSTITUTIONAL RESULTS'),89,120,7.1,MUTED,True)
    if country=='Brazil':text(c,'PILOT RESPONSE · MAR 2026',88,133,6.1,ORANGE,True)
    right(c,f'{page_idx:02d} / {total:02d}',572,101,8,BLUE,True)
    right(c,'REGIONAL SURVEY 2026',572,117,7,MUTED)
    rect(c,40,143,532,2,ORANGE)

def metric(c,x,top,w,primary,label):
    rect(c,x,top,w,45,PALE2,r=5)
    rect(c,x,top,3,45,BRIGHT,r=1)
    # Avoid overflow of long multi-line labels
    paragraph(c,primary,x+9,top+7,w-16,size=9.2 if len(primary)<22 else 7.1,bold=True,maxheight=21)
    paragraph(c,label,x+9,top+29,w-13,size=5.55,color=MUTED,leading=7,maxheight=13)

def badge(c,s,x,top,width,active):
    rect(c,x,top,width,17,PALE if active else '#F3F5F6',r=7)
    label=('● ' if active else '○ ')+s
    paragraph(c,label,x+6,top+4,width-11,size=6.0,color=BLUE if active else '#8297A7',maxheight=10)

def cap_bars(c,row,x,top,width):
    heading(c,'Capability snapshot',x,top,width)
    right(c,'0–100  ·  SURVEY-DERIVED',x+width,top,5.2,MUTED)
    yy=top+22
    for lab,v,n,total in scores(row):
        text(c,lab,x,yy+2,7,MUTED)
        trackx=x+171;trackw=width-198
        rect(c,trackx,yy,trackw,10,'#E5EEF4',r=5)
        if v is not None:
            rect(c,trackx,yy,max(2,trackw*v/100),10,BLUE if v>=70 else BRIGHT if v>=45 else ORANGE,r=5)
            right(c,str(v),x+width,yy,7.6,BLUE,True)
        else:right(c,'—',x+width,yy,7.6,MUTED)
        yy+=23
    return yy

def attribute_table(c,row,x,top,width):
    heading(c,'Institutional & operational attributes',x,top,width)
    pairs=row_items(row)
    gap=11; w=(width-gap)/2; y0=top+21
    # Two columns x 10 rows with one consistent 17px row height.
    for i,(label,value) in enumerate(pairs):
        column=i//10; line=i%10
        xx=x+column*(w+gap);yy=y0+line*17
        rule(c,xx,xx+w,yy+15)
        if value in ('No','None','Not used','Health sector only'):
            color=ORANGE
        elif value in ('Yes','Formal','Systematic','Used','Integrated','Updated','Consolidated','Functional','Formal & regular','High','Interoperable'):
            color=BLUE
        else:color=MUTED
        text(c,label,xx,yy+1,5.45,MUTED)
        right(c,value[:26],xx+w,yy+1,5.35,color,True)
    return y0+10*17

def side(c,row,x,top,width):
    heading(c,'Hazards coordinated',x,top,width)
    yy=top+21
    for label,ans in hazards(row):
        text(c,label,x,yy,6.25,MUTED)
        right(c,ans,x+width,yy,6.2,BLUE if ans not in ('None','Not reported') else MUTED,True)
        yy+=16
    yy+=5
    heading(c,'Operational resources',x,yy,width)
    yy+=22
    for j,(label,idx) in enumerate(RESOURCES):
        c0=j%2; r0=j//2;w=(width-7)/2
        badge(c,label,x+(w+7)*c0,yy+r0*21,w,selected(row,idx) is True)
    yy+=93
    heading(c,'Training',x,yy,width)
    yy+=22
    text(c,'Completed  /  priority marked *',x,yy,6,MUTED)
    yy+=13
    for label,a,b in TRAININGS:
        done=selected(row,a);pri=selected(row,b)
        marker=('●' if done else '○')+('  ★' if pri else '')
        text(c,marker,x,yy,6.4,ORANGE if pri else BLUE if done else MUTED)
        text(c,label,x+28,yy,6.25,INK if done or pri else MUTED)
        yy+=15
    return yy

def draw_bullets(c,arr,x,top,width,color,max_h=76):
    y=top
    for a in arr[:3]:
        rect(c,x,y+4,4,4,color,r=2)
        h=paragraph(c,a,x+11,y,width-14,size=6.8,maxheight=35)
        y+=max(15,h+5)
        if y>top+max_h:break

def footer(c,country,count,notices=None):
    notices=notices or []
    rule(c,40,572,742,LINE)
    text(c,'SOURCE  PAHO/WHO Regional Survey on Health Emergency Operations Centres (2026)',40,752,6.1,BLUE,True)
    text(c,f'{count} submitted record(s) for {country}  ·  Self-reported information  ·  Not independently verified',40,763,5.5,MUTED)
    text(c,'Indicative scores summarize selected closed-question responses; not an official PAHO assessment or country ranking.',40,774,5.0,MUTED)
    right(c,'paho.org',572,753,7,BRIGHT,True)

def core_single(c,country,row):
    inst=organization(row)
    paragraph(c,inst,42,151,528,size=9.0,color=INK,bold=True,maxheight=27)
    metrics=[(val(row,17) if val(row,17) and val(row,17)!='1900' else '—','Established'),
         (english_mode(row),'Operating mode'),(english_activation(row),'Activation time'),
         (english_mandate(row),'Mandate'),
         (str(number(row,67)) if number(row,67) is not None else '—','24/7 duty staff')]
    xs=[40,148,256,364,472]
    for (k,v),x in zip(metrics,xs):metric(c,x,184,100,k,v)
    cap_bars(c,row,40,245,323)
    attribute_table(c,row,40,405,323)
    side(c,row,383,245,189)
    rect(c,40,626,260,102,PALE2,r=7)
    rect(c,312,626,260,102,'#FFF5F0',r=7)
    text(c,'REPORTED STRENGTHS',52,637,7,BLUE,True)
    text(c,'IMPROVEMENT PRIORITIES',324,637,7,ORANGE,True)
    a,b=narrative_for(country,row)
    draw_bullets(c,a,52,655,239,BLUE,65)
    draw_bullets(c,b,324,655,236,ORANGE,65)


def compact_card(c,row,x,top,width,index,total,country):
    height=264
    rect(c,x,top,width,height,PALE2 if index%2==0 else WHITE,r=9,stroke=LINE)
    text(c,f'RESPONSE {index+1} OF {total}  ·  '+('EOC REPORTED' if status(row) else 'NO EOC REPORTED' if status(row) is False else 'UNDER IMPLEMENTATION'),x+13,top+10,7.0,BRIGHT if status(row) else ORANGE,True)
    right(c,date_str(row),x+width-12,top+11,6.5,MUTED)
    paragraph(c,organization(row),x+13,top+28,width-26,size=9.4,color=BLUE,bold=True,maxheight=35)
    rect(c,x+13,top+69,width-26,1,LINE)
    fields=[('Established',val(row,17) if val(row,17)!='1900' else 'N/A'),
      ('Operating mode',english_mode(row)),('Activation',english_activation(row)),
      ('Staff 24/7',str(number(row,67)) if number(row,67) is not None else 'N/A')]
    for i,(k,v) in enumerate(fields):
        xx=x+13+(i%2)*(width/2-5); yy=top+79+(i//2)*34
        text(c,k.upper(),xx,yy,5.3,MUTED,True)
        paragraph(c,v,xx,yy+10,width/2-23,size=7.1,color=INK,bold=True,maxheight=17)
    yy=top+154
    text(c,'CAPABILITY DOMAINS',x+13,yy,6.4,BLUE,True)
    yy+=18
    for lab,value,n,totaln in scores(row):
        text(c,lab,x+13,yy,5.8,MUTED)
        bx=x+143;bw=width-184
        rect(c,bx,yy,bw,7,'#E5EEF4',r=3)
        if value is not None:
            rect(c,bx,yy,max(2,bw*value/100),7,BLUE if value>=65 else BRIGHT if value>=40 else ORANGE,r=3)
            right(c,str(value),x+width-12,yy-1,6.3,BLUE,True)
        else:right(c,'N/A',x+width-12,yy-1,6.0,MUTED)
        yy+=14

def multi_page(c,country,rows):
    text(c,'MULTIPLE SURVEY RECORDS  •  INSTITUTIONAL RESULTS SHOWN SEPARATELY',40,151,8,BLUE,True)
    paragraph(c,'These submissions are not combined into a single national score. Different institutions may report different capacities.',40,169,529,7.3,MUTED,maxheight=32)
    # Two records stacked vertically; 15 countries from 18 responses.
    for i,row in enumerate(rows[:2]):
        compact_card(c,row,40,207+i*270,532,i,len(rows),country)
    if len(rows)>2:paragraph(c,f'An additional {len(rows)-2} response(s) are retained in the source workbook.',42,733,521,size=6.1,color=MUTED,maxheight=8)
    if all(status(r) is False for r in rows):
        rect(c,40,185,532,18,'#FFF5F0',r=4)
        text(c,'NO HEALTH EOC REPORTED BY THESE RESPONDENTS',50,189,7,ORANGE,True)


def do_page(c,country,rows,i,total):
    header(c,country,rows,i,total)
    if len(rows)==1 and status(rows[0]) is not False:
        core_single(c,country,rows[0])
    elif len(rows)==1:  # uncommon; no centre reported
        r=rows[0]
        text(c,'No health emergency operations centre reported',40,170,12,ORANGE,True)
        paragraph(c,'The responding institution reported that it does not have a health EOC or equivalent mechanism. No capacity index is calculated.',40,202,532,9,MUTED)
    else:multi_page(c,country,rows)
    footer(c,country,len(rows))
    c.showPage()


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--input',type=Path,default=HERE/'data'/'Encuesta_OPS_2026_COEs.xlsx')
    p.add_argument('--output',type=Path,default=HERE/'output')
    args=p.parse_args()
    init_fonts()
    rows=read_first_sheet(args.input)
    assert len(rows[0])>=150, f'Expected >=150 columns, got {len(rows[0])}'
    reports=collections.defaultdict(list)
    for r in rows[1:]:
        k=val(r,7)
        if not k:continue
        reports[COUNTRIES.get(k,k)].append(r)
    for k in reports:reports[k].sort(key=submit_key,reverse=True)
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'countries').mkdir(parents=True,exist_ok=True)
    names=sorted(reports)
    combined=args.output/'PAHO_EOC_Country_Fact_Sheets_2026.pdf'
    c=canvas.Canvas(str(combined),pagesize=letter,pageCompression=1)
    c.setTitle('PAHO | EOC Country Fact Sheets 2026')
    c.setAuthor('PAHO/WHO - Regional EOC survey (automatically generated; indicative)')
    for i, name in enumerate(names,1):do_page(c,name,reports[name],i,len(names))
    c.save()
    # Export independent one-page files as well; very useful for country distribution.
    for i,name in enumerate(names,1):
        slug=re.sub(r'[^a-z0-9]+','_',normalize(name)).strip('_')
        dest=args.output/'countries'/f'{slug}.pdf'
        single=canvas.Canvas(str(dest),pagesize=letter,pageCompression=1)
        single.setTitle(f'{name} | PAHO EOC Fact Sheet 2026')
        do_page(single,name,reports[name],i,len(names))
        single.save()
    print(f'Generated {len(names)} country pages from {sum(len(v) for v in reports.values())} survey responses: {combined}')
    print('Countries:',', '.join(names))

if __name__=='__main__':main()