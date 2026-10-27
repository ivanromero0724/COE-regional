#!/usr/bin/env python3
"""Reproducible PAHO EOC country fact sheets (one Letter page per survey record).

Source: first worksheet in data/Encuesta_OPS_2026_COEs.xlsx.
No external APIs, credentials or machine translation; controlled survey answers are
translated via deterministic rules. Respondent names, phone numbers and emails
are never printed. Non-standard free text is not published verbatim.
"""
from __future__ import annotations
import argparse, collections, datetime as dt, hashlib, html, re, unicodedata, zipfile
from io import BytesIO
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont
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

# ISO alpha-2 codes for reproducible national flag illustrations. The Noto Color
# Emoji glyph is rasterized and embedded in the PDF; no remote service needed.
ISO = {'Argentina':'AR','Bahamas':'BS','Belize':'BZ','Bolivia':'BO','Brazil':'BR',
       'Colombia':'CO','Dominica':'DM','Ecuador':'EC','El Salvador':'SV',
       'Guatemala':'GT','Honduras':'HN','Panama':'PA','Paraguay':'PY',
       'Peru':'PE','Saint Lucia':'LC'}

@lru_cache(maxsize=25)
def flag(country):
    code = ISO.get(country)
    if not code:
        raise ValueError(f'No flag ISO mapping for {country!r}; add it to ISO')
    candidates = ['/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf',
                  '/usr/share/fonts/noto/NotoColorEmoji.ttf']
    font_path = next((v for v in candidates if Path(v).is_file()), None)
    if not font_path:
        raise RuntimeError('Noto Color Emoji font is required for country flags; '
                           'install fonts-noto-color-emoji on the build machine.')
    emoji = ''.join(chr(0x1F1E6 + ord(ch) - ord('A')) for ch in code)
    font = ImageFont.truetype(font_path, 109)
    image = Image.new('RGBA',(165,155),(255,255,255,0))
    ImageDraw.Draw(image).text((8,0), emoji, font=font, embedded_color=True)
    box = image.getbbox()
    if not box: raise RuntimeError(f'Flag did not render for {country}')
    image = image.crop(box)
    # Composite on white so internal transparency cannot leave a dark backing.
    image.thumbnail((145,105),Image.Resampling.LANCZOS)
    dst = Image.new('RGBA',image.size,(255,255,255,0))
    dst.alpha_composite(image)
    return ImageReader(dst)

def institution_slug(row):
    s=normalize(val(row,8))
    if 'instituto nacional' in s:return 'national_institute_of_health'
    if 'ministerio' in s:return 'ministry_of_health'
    if 'secretaria' in s:return 'secretariat_of_health'
    if 'otro' in s:return 'other_institution'
    return 'reporting_institution'

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
    if 'grupo de gestion del riesgo' in n or ('centro operaciones de emergencia' in n and 'respuesta inmediata' in n):return 'Public Health EOC - National Institute of Health (INS)'
    if n=='coe salud':return 'Health EOC - Ministry of Health and Social Protection'
    if 'emergencias de salud publica' in n or 'emergencias en salud publica' in n:return 'Public Health Emergency Operations Centre'
    if n in ('heoc','health emergency operations center'):return 'Health Emergency Operations Centre (HEOC)'
    if 'mohw emergency operation center' in n:return 'MOHW Emergency Operations Centre'
    if not name and 'instituto nacional de salud' in normalize(fallback):return 'National Institute of Health'
    if not name and 'ministerio' in normalize(fallback):return 'Ministry of Health - reporting institution'
    if not name and 'secretaria' in normalize(fallback):return 'Secretariat of Health - reporting institution'
    if not name and normalize(fallback).startswith('5. otro'):return 'Other institution (as reported)'

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
    """Three aligned zones: editorial title, EOC-NET and PAHO original logos.

    Each logo uses an identical 140 pt-wide, non-overlapping zone, with the
    original proportions preserved. No graphic element can cover another.
    """
    rect(c, 0, 0, PAGE_W, 7, BLUE)
    rect(c, 455, 0, PAGE_W-455, 7, ORANGE)
    eoc = HERE/'logos'/'logo_EOC.png'
    paho = HERE/'logos'/'PAHO_eng.png'
    if not (eoc.exists() and paho.exists()):
        raise FileNotFoundError('Both tracked logos must exist in logos/')

    # Left: keep a strong title, but within its own 227 pt wide column.
    text(c, 'EOC-NET / THE AMERICAS', 40, 24, 14.3, BLUE, True)
    text(c, 'COUNTRY FACT SHEETS  ·  2026', 40, 51, 9.4, ORANGE, True)

    # Centre/right: equal-width original logo artwork, side by side.
    # Explicit image geometry avoids ReportLab anchor/preserveAspectRatio shifts.
    from PIL import Image
    from reportlab.lib.utils import ImageReader
    def logo_fit(img_path, left, top, width, height):
        with Image.open(img_path) as im:
            iw, ih = im.size
        scale = min(width / iw, height / ih)
        dw, dh = iw * scale, ih * scale
        x = left + (width - dw)/2
        y = PAGE_H - top - (height - dh)/2 - dh
        c.drawImage(ImageReader(str(img_path)), x, y, width=dw, height=dh,
                    mask='auto')

    logo_fit(eoc, 281, 16, 138, 57)
    logo_fit(paho, 436, 16, 138, 57)
    rule(c, 40, PAGE_W-40, 90, BLUE, 1.05)


def header(c, country, row, page_idx, total, response_number, responses_in_country):
    logo_header(c)
    # Draw the emoji national flag directly, with NO surrounding grey frame.
    c.drawImage(flag(country), 40, PAGE_H-99-32, width=55, height=32,
                mask='auto')
    text(c, country, 107, 95, 24.5, BLUE, True)
    if responses_in_country > 1:
        sub = f'INSTITUTIONAL RESPONSE {response_number} OF {responses_in_country}  ·  INDEPENDENT RECORD'
    else:
        sub = 'INSTITUTIONAL SURVEY RECORD'
    text(c, sub, 108, 124, 6.9, MUTED, True)
    if country == 'Brazil':
        text(c, 'PILOT RESPONSE · MAR 2026', 108, 135, 5.8, ORANGE, True)
    right(c, f'{page_idx:02d} / {total:02d}', 572, 100, 8.5, BLUE, True)
    right(c, 'REGIONAL SURVEY 2026', 572, 119, 6.8, MUTED)
    rect(c, 40, 145, 532, 2, ORANGE)


def metric(c, x, top, w, primary, label):
    """Restore the original understated top KPI cards preferred for the report."""
    rect(c, x, top, w, 45, PALE2, r=5)
    rect(c, x, top, 3, 45, BRIGHT, r=1)
    paragraph(c, primary, x+9, top+7, w-16,
              size=9.2 if len(primary)<22 else 7.1, bold=True, maxheight=21)
    paragraph(c, label, x+9, top+29, w-13,
              size=5.55, color=MUTED, leading=7, maxheight=13)


def section_panel(c, x, top, width, height, title):
    """Same border, padding and heading grid for all five capability panels."""
    rect(c, x, top, width, height, '#FBFDFE', r=8, stroke='#D4E4EE', lw=.8)
    heading(c, title, x+10, top+10, width-20)


def badge(c, s, x, top, width, active):
    rect(c, x, top, width, 16, PALE if active else '#F1F4F6', r=7)
    mark='●' if active else '○'
    text(c, mark, x+5, top+4, 5.5, BLUE if active else '#8C9DAC')
    paragraph(c,s,x+14,top+3,width-18,size=5.15,
              color=BLUE if active else '#8496A4',maxheight=10)


def cap_bars(c, row, x, top, width):
    section_panel(c, x, top, width, 141, 'Capability snapshot')
    yy=top+31
    for lab,v,n,total in scores(row):
        text(c,lab,x+10,yy+1,6.45,MUTED)
        track_x=x+176
        track_w=width-207
        rect(c,track_x,yy,track_w,9,'#E5EEF4',r=4.5)
        if v is not None:
            rect(c,track_x,yy,max(2,track_w*v/100),9,
                 BLUE if v>=70 else BRIGHT if v>=45 else ORANGE,r=4.5)
            right(c,str(v),x+width-10,yy,7.8,BLUE,True)
        else:
            right(c,'—',x+width-10,yy,7.8,MUTED)
        yy+=20
    text(c,'Mean of available scored responses · 0–100 · indicative',
         x+10,top+128,5.15,MUTED)
    return top+141


def attribute_table(c, row, x, top, width):
    section_panel(c, x, top, width, 213, 'Institutional & operational attributes')
    pairs=row_items(row)
    gap=12
    inner=width-20
    w=(inner-gap)/2
    y0=top+32
    # Dense 20-item grid: the attribute and its response occupy DIFFERENT
    # text lines so neither can collide, even for long response categories.
    for i,(label,value) in enumerate(pairs):
        column=i//10; line=i%10
        xx=x+10+column*(w+gap)
        yy=y0+line*17
        text(c,label,xx,yy,5.45,MUTED)
        if value in ('No','None','Not used','Health sector only'):
            color=ORANGE
        elif value in ('Yes','Formal','Systematic','Used','Integrated',
                       'Updated','Consolidated','Functional',
                       'Formal & regular','High','Interoperable'):
            color=BLUE
        else:
            color=MUTED
        text(c,value[:30],xx,yy+7,5.65,color,True)
        rule(c,xx,xx+w,yy+16,LINE,.45)
    return top+213


def side(c, row, x, top, width):
    # Three deliberately separate blocks on the right. The last card ends
    # exactly level with the two-column institutional attributes on the left.
    section_panel(c,x,top,width,106,'Hazards coordinated')
    yy=top+32
    for label,ans in hazards(row):
        text(c,label,x+10,yy,5.95,MUTED)
        right(c,ans,x+width-10,yy,5.75,
              BLUE if ans not in ('None','Not reported') else MUTED,True)
        yy+=16

    resource_top=top+116
    section_panel(c,x,resource_top,width,112,'Operational resources')
    resource_labels={
        'Virtual coordination':'Virtual platform',
        'Communications':'Comms equipment',
        'Redundant internet':'Backup internet',
        'Team workstations':'Workstations',
    }
    avail_width=width-20
    chip_gap=7
    chip_width=(avail_width-chip_gap)/2
    for j,(label,idx) in enumerate(RESOURCES):
        c0=j%2
        r0=j//2
        xx=x+10+c0*(chip_width+chip_gap)
        yy=resource_top+34+r0*19
        badge(c,resource_labels.get(label,label),xx,yy,chip_width,
              selected(row,idx) is True)

    training_top=top+238
    section_panel(c,x,training_top,width,124,'Training')
    text(c,'● completed    ★ priority for strengthening',
         x+10,training_top+28,5.4,MUTED)
    for j,(label,a,b) in enumerate(TRAININGS):
        yy=training_top+43+j*9.8
        done=selected(row,a)
        priority=selected(row,b)
        text(c,'●' if done else '○',x+11,yy,6.0,
             BLUE if done else '#9AADB9')
        if priority:
            text(c,'★',x+24,yy,5.9,ORANGE)
        text(c,label,x+38,yy,5.95,
             INK if done or priority else MUTED)
    return training_top+124


def draw_bullets(c,arr,x,top,width,color,max_h=76):
    y=top
    for a in arr[:3]:
        rect(c,x,y+4,4,4,color,r=2)
        h=paragraph(c,a,x+11,y,width-14,size=6.8,maxheight=35)
        y+=max(15,h+5)
        if y>top+max_h:break

def footer(c,country,source_row):
    rule(c,40,572,742,LINE)
    text(c,'SOURCE  PAHO/WHO Regional Survey on Health Emergency Operations Centres (2026)',40,752,6.1,BLUE,True)
    text(c,f'{country} · Source Excel row {source_row} · Self-reported information · Not independently verified',40,763,5.5,MUTED)
    text(c,'Indicative scores: arithmetic means of item-specific 0–100 rubrics; not an official PAHO assessment or ranking.',40,774,5.0,MUTED)
    right(c,'paho.org',572,753,7,BRIGHT,True)


def core_single(c,country,row):
    inst=organization(row)
    paragraph(c,inst,42,151,528,size=9.0,color=INK,bold=True,maxheight=27)
    metrics=[(val(row,17) if val(row,17) and val(row,17)!='1900' else '—','Established'),
         (english_mode(row),'Operating mode'),(english_activation(row),'Activation time'),
         (english_mandate(row),'Mandate'),
         (str(number(row,67)) if number(row,67) is not None else '—','24/7 duty staff')]
    xs=[40,148,256,364,472]
    for (k,v),x in zip(metrics,xs):metric(c,x,188,100,k,v)
    cap_bars(c,row,40,250,323)
    attribute_table(c,row,40,399,323)
    side(c,row,375,250,197)
    rect(c,40,626,260,102,PALE2,r=7)
    rect(c,312,626,260,102,'#FFF5F0',r=7)
    text(c,'REPORTED STRENGTHS',52,637,7,BLUE,True)
    text(c,'IMPROVEMENT PRIORITIES',324,637,7,ORANGE,True)
    a,b=narrative_for(country,row)
    draw_bullets(c,a,52,655,239,BLUE,65)
    draw_bullets(c,b,324,655,236,ORANGE,65)


def core_no_eoc(c,country,row):
    rect(c,40,157,532,84,'#FFF5F0',r=7,stroke='#F5C8B4')
    text(c,'NO HEALTH EOC REPORTED BY THIS RESPONDENT',53,172,10,ORANGE,True)
    paragraph(c,'The response indicates that the reporting institution does not have a health emergency '
              'operations centre (or equivalent mechanism). It is retained as an independent survey '
              'record, not combined with other responses from this country.',53,193,504,size=8.2,maxheight=43)
    heading(c,'Reporting context',40,271,532)
    institution=organization(row)
    paragraph(c,'Responding organization: '+institution,43,295,526,size=9.0,bold=True,maxheight=38)
    paragraph(c,'Institution type: '+ ('Other (as reported)' if 'otro' in normalize(val(row,8)) else val(row,8)),43,344,520,size=8.1,color=MUTED,maxheight=32)
    paragraph(c,'Survey submitted: '+date_str(row),43,384,518,size=8.1,color=MUTED,maxheight=25)
    rect(c,40,448,532,121,PALE2,r=8)
    text(c,'INTERPRETATION NOTE',53,463,7.5,BLUE,True)
    paragraph(c,'Because this respondent answered "No" to the existence of a health EOC, '
              'the EOC-specific capability charts, operational resources and maturity indicators '
              'are intentionally not calculated on this page. This does not contradict or replace '
              'information supplied by another organization from the same country.',
              53,485,503,size=8.4,maxheight=74)
    rect(c,40,608,532,94,PALE,r=8)
    text(c,'SURVEY SOURCE',53,625,7.5,BLUE,True)
    paragraph(c,'PAHO/WHO Regional Survey on Health Emergency Operations Centres, 2026. '
              'Consult the source workbook for all responses and any institutional follow-up.',
              53,645,502,size=8.0,maxheight=48)


def do_page(c,country,row,page_idx,total,response_number,responses_in_country,source_row):
    header(c,country,row,page_idx,total,response_number,responses_in_country)
    if status(row) is False:
        core_no_eoc(c,country,row)
    else:
        core_single(c,country,row)
    footer(c,country,source_row)
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
    for source_row,r in enumerate(rows[1:],start=2):
        country=COUNTRIES.get(val(r,7),val(r,7))
        if not country:continue
        reports[country].append((source_row,r))
    # Keep response order stable, and assign unique, non-overwriting names.
    for country in reports:
        reports[country].sort(key=lambda item: (-submit_key(item[1]), item[0]))
    pages=[]
    for country in sorted(reports):
        submissions=reports[country]
        n=len(submissions)
        for i,(source_row,row) in enumerate(submissions,1):
            slug=re.sub(r'[^a-z0-9]+','_',normalize(country)).strip('_')
            if n>1:
                group_slug=institution_slug(row)
                group_count=sum(institution_slug(x[1])==group_slug for x in submissions)
                index=sum(institution_slug(x[1])==group_slug for x in submissions[:i])
                slug += '_'+group_slug
                if group_count>1:slug+=f'_{index:02d}'
            pages.append((country,row,i,n,source_row,slug))
    if not pages:raise ValueError('No country responses in first Excel worksheet')
    args.output.mkdir(parents=True,exist_ok=True)
    out_country=args.output/'countries'
    out_country.mkdir(parents=True,exist_ok=True)
    expected_filenames={record[-1]+'.pdf' for record in pages}
    if len(expected_filenames)!=len(pages):raise AssertionError('Generated filenames must be unique per record')
    # Important: remove old country-level files when changing from 15 to 18.
    for existing in out_country.glob('*.pdf'):
        if existing.name not in expected_filenames:existing.unlink()
    combined=args.output/'PAHO_EOC_Country_Fact_Sheets_2026.pdf'
    c=canvas.Canvas(str(combined),pagesize=letter,pageCompression=1)
    c.setTitle('PAHO | EOC Survey Fact Sheets 2026 | One per response')
    c.setAuthor('PAHO/WHO - Regional EOC survey (automatically generated; indicative)')
    for page_idx,(country,row,response_number,n,source_row,slug) in enumerate(pages,1):
        do_page(c,country,row,page_idx,len(pages),response_number,n,source_row)
    c.save()
    for page_idx,(country,row,response_number,n,source_row,slug) in enumerate(pages,1):
        dest=out_country/f'{slug}.pdf'
        single=canvas.Canvas(str(dest),pagesize=letter,pageCompression=1)
        single.setTitle(f'{country} · Response {response_number}/{n} | PAHO EOC 2026')
        do_page(single,country,row,page_idx,len(pages),response_number,n,source_row)
        single.save()
    print(f'Generated {len(pages)} pages from {len(pages)} survey responses, '
          f'{len(reports)} distinct countries: {combined}')
    print('Individual pages:', ', '.join(p.name for p in sorted(out_country.glob('*.pdf'))))

if __name__=='__main__':main()