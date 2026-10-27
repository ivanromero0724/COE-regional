#!/usr/bin/env python3
"""Reproducible PAHO EOC country fact sheets (one Letter page per survey record).

Source: first worksheet in data/Encuesta_OPS_2026_COEs.xlsx.
No external APIs, credentials or machine translation; controlled survey answers are
translated via deterministic rules. Respondent names, phone numbers and emails
are never printed. Non-standard free text is not published verbatim.
"""
from __future__ import annotations
import argparse, collections, datetime as dt, hashlib, html, re, statistics, unicodedata, zipfile
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

# The approved reference fact-sheet calculation recodes 24 questionnaire items
# to five ordered maturity points (1=weakest, 5=strongest). Indices are zero-based
# columns in the first worksheet; see docs/capability_scoring.md for provenance.
# IMPORTANT: Code values are not always in strength order (e.g. Q21).
ITEM_RATINGS = {
    # Governance & legal (Q10, Q12, Q13, Q14, Q15)
    29: {'a':1,'b':2,'c':3,'d':4,'e':5},  # legal framework
    32: {'a':1,'b':2,'c':3,'d':4,'e':5},  # legal support to decisions
    33: {'a':5,'b':1},                  # inclusion in national plan
    36: {'a':1,'b':2,'c':3,'d':4,'e':5},  # sustainable finance
    37: {'a':5,'b':1,'c':3},            # formal SOP
    # Operations & decisions (Q16, Q20, Q22, Q23, Q24, Q25)
    39: {'a':5,'b':4,'c':2,'d':1,'e':1},  # activation time: <2h / 2-6h / >6h / undefined
    43: {'a':5,'b':3,'c':1,'d':1},       # incident action plan
    46: {'a':5,'b':3,'c':1,'d':1},       # strategic committee
    47: {'a':5,'b':1},                  # incident management system
    49: {'a':1,'b':2,'c':3,'d':4,'e':5},  # risk assessment and grading
    50: {'a':1,'b':2,'c':3,'d':4,'e':5},  # operational/logistic capacity
    # Human resources & surge (Q28, Q30, Q32, Q33, Q34)
    66: {'a':5,'b':3,'c':1},             # coordinator
    68: {'a':5,'b':3,'c':1},             # defined roles
    77: {'a':1,'b':2,'c':3,'d':4,'e':5},   # surge procedures
    78: {'a':5,'b':3,'c':2,'d':1,'e':1},   # response roster
    80: {'a':5,'b':3,'c':1,'d':1},        # rapid-team deployment
    # Information management (Q38, Q39, Q40, Q41, Q42)
    105: {'a':1,'b':2,'c':4,'d':5},      # intra-institutional information exchange
    107: {'a':1,'b':2,'c':3,'d':4,'e':5}, # information systems
    108: {'a':1,'b':2,'c':3,'d':5},      # frequent information gaps (reverse severity)
    109: {'a':5,'b':1,'c':1},            # integrated situation room
    110: {'a':1,'b':2,'c':3,'d':5,'e':1}, # SITREP procedures
    # Coordination & integration (Q18, Q19, Q21)
    41: {'a':1,'b':3,'c':5,'d':1},       # intersectoral collaboration
    42: {'a':1,'b':2,'c':4,'d':5},       # disaster-risk integration
    44: {'a':5,'b':4,'c':4,'d':1,'e':1}, # international cooperation
}

DOMAINS = [
    ('Governance & legal', [29,32,33,36,37]),
    ('Operations & decisions', [39,43,46,47,49,50]),
    ('Human resources', [66,68,77,78,80]),
    ('Information management', [105,107,108,109,110]),
    ('Coordination', [41,42,44]),
]

# Catch accidental omission, duplication or edits to the 24-item specification.
_DOMAIN_INDICES = [index for _, indices in DOMAINS for index in indices]
assert len(DOMAINS) == 5 and len(_DOMAIN_INDICES) == 24
assert len(set(_DOMAIN_INDICES)) == 24 and set(_DOMAIN_INDICES) == set(ITEM_RATINGS)
assert all(1 <= score <= 5 for ratings in ITEM_RATINGS.values() for score in ratings.values())


def score_by_index(row, idx):
    """Return the 1–5 ordinal item rating, or None for a genuinely blank cell.

    Explicit 'don't know', 'not defined' and 'not applicable' survey choices
    receive 1 where specified by the *reference 2026 infographic rubric*.
    This reproduces the provided baseline, but measures both uncertainty and
    declared immaturity; the methodological caveat is documented separately.
    """
    code = choice(row, idx)
    return ITEM_RATINGS.get(idx, {}).get(code)


def maturity_level(score):
    if score is None: return 'Not scored'
    if score < 40: return 'Initial'
    if score < 60: return 'Developing'
    if score < 80: return 'Functional'
    return 'Advanced'


def scores(row):
    """Five 0–100 pillar scores from equally weighted 1–5 question ratings.

    This is (mean(ratings) - 1) * 25, rounded only for display. Empty cells
    are excluded; 'don't know' options explicitly listed above are scored 1.
    """
    result = []
    for label, cols in DOMAINS:
        vals = [score_by_index(row, j) for j in cols]
        scored = [v for v in vals if v is not None]
        value = round((sum(scored)/len(scored) - 1)*25) if scored else None
        result.append((label, value, len(scored), len(cols)))
    return result

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


def responding_country_means(reports):
    """Country-weighted benchmark, NOT a full-Americas regional estimate.

    Each country has a single vote in the benchmark: if multiple institutions
    submitted a valid EOC response, average their reported domain scores first.
    Respondents reporting no EOC are excluded from EOC-specific capability scores.
    Any missing domain is omitted from that domain's benchmark denominator.
    """
    means = []
    for i, (label, columns) in enumerate(DOMAINS):
        by_country = []
        for country, submissions in reports.items():
            institution_scores = []
            for source_row, row in submissions:
                if status(row) is False:
                    continue
                value = scores(row)[i][1]
                if value is not None:
                    institution_scores.append(value)
            if institution_scores:
                by_country.append(statistics.mean(institution_scores))
        means.append((label, statistics.mean(by_country) if by_country else None,
                      len(by_country)))
    return means


def maturity_color(score):
    # The four maturity bands from the 24-item reference rubric.
    if score is None: return MUTED
    if score < 40: return '#EA8B62'   # Initial
    if score < 60: return '#85BFDE'   # Developing
    if score < 80: return '#397FA9'   # Functional
    return BLUE                       # Advanced


def cap_bars(c, row, x, top, width, region_means):
    section_panel(c, x, top, width, 141, 'Capability snapshot')
    # Five rows use the 24-item ordinal-derived 0–100 pillar scale. The orange marker is the
    # unweighted mean of responding countries, not an Americas-wide baseline.
    track_x = x + 173
    track_w = width - 207
    for i, (lab, value, scored, total) in enumerate(scores(row)):
        yy = top + 31 + 20*i
        text(c, lab, x+10, yy+1, 6.20, MUTED)
        rect(c, track_x, yy+1, track_w, 8, '#E8F0F5', r=4)
        if value is not None:
            rect(c, track_x, yy+1, max(2, track_w*value/100), 8, maturity_color(value), r=4)
            right(c, str(value), x+width-10, yy, 7.65, BLUE, True)
        else:
            right(c, '—', x+width-10, yy, 7.65, MUTED)
        benchmark = region_means[i][1]
        if benchmark is not None:
            px = track_x + track_w*benchmark/100
            c.setStrokeColor(col(ORANGE)); c.setLineWidth(1.7)
            c.line(px, PAGE_H-(yy-2), px, PAGE_H-(yy+12))
    # Legend contains a transparent limitation; benchmarks update from the data.
    rect(c, x+10, top+127.3, 8, 4.3, BLUE, r=2)
    text(c, 'Response', x+22, top+125.9, 4.9, MUTED)
    rect(c, x+83, top+125.7, 2.2, 9, ORANGE, r=0.9)
    n = min((r[2] for r in region_means if r[2]), default=0)
    text(c, f'Responding-country mean (n={n}; countries equally weighted)',
         x+90, top+125.9, 4.55, MUTED)
    return top+141


def fit_text_size(s, max_width, preferred=5.8, minimum=4.6, bold=False):
    font = BOLD if bold else FONT
    k = preferred
    while k > minimum and pdfmetrics.stringWidth(str(s), font, k) > max_width:
        k -= .15
    return max(minimum, k)


def attribute_table(c, row, x, top, width):
    """Clean 20-item capability matrix; no redundant two-line response rows."""
    section_panel(c, x, top, width, 213, 'Institutional & operational attributes')
    pairs = row_items(row)
    abbreviations = {
        'Disaster-risk integration':'DRM integration',
        'International cooperation':'Intl. cooperation',
        'Incident management':'Incident management',
        'Incident action plan':'Incident action plan',
        'Information tools':'Information tools',
        'Logistics readiness':'Logistics readiness',
    }
    gap = 12
    inner = width-20
    w = (inner-gap)/2
    y0 = top+31
    for i,(label,value) in enumerate(pairs):
        column, line = divmod(i, 10)
        xx = x+10 + column*(w+gap)
        yy = y0 + line*17.45
        if line % 2 == 0:
            rect(c, xx, yy, w, 15.1, '#EEF5FA', r=3)
        label = abbreviations.get(label, label)
        if value in ('No','None','Not used','Health sector only'):
            fg, bg = ORANGE, '#FFF0EA'
        elif value in ('Yes','Formal','Systematic','Used','Integrated','Updated',
                       'Consolidated','Functional','Formal & regular','High',
                       'Interoperable','Leads'):
            fg, bg = BLUE, '#DDEDF7'
        else:
            fg, bg = MUTED, '#E8EEF1'
        p_width = min(w*.48, pdfmetrics.stringWidth(value, BOLD, 5.4)+12)
        p_width = max(29, p_width)
        px = xx+w-3-p_width
        rect(c, px, yy+2, p_width, 11, bg, r=5.5)
        labelsize = fit_text_size(label, px-(xx+4)-3, 5.9, 4.5)
        text(c, label, xx+4, yy+3.6, labelsize, INK)
        valuesize = fit_text_size(value,p_width-6, 5.2, 4.3, True)
        c.setFont(BOLD,valuesize);c.setFillColor(col(fg))
        c.drawCentredString(px+p_width/2,PAGE_H-(yy+3.45)-valuesize,value)
    return top+213


def side(c, row, x, top, width):
    """Three compact visual summaries with fewer competing text styles."""
    section_panel(c, x, top, width, 106, 'Hazards coordinated')
    # Event counts are ordinal survey categories: the three lit mini-bars
    # represent ordered *ranges*, not proportional numbers of emergencies.
    hazard_labels = {
        'Geological / weather':'Geological / weather',
        'Biological / epidemics':'Biological / epidemic',
        'Social / human-caused':'Social / human-caused',
        'Technological':'Technological',
    }
    for i,(label,answer) in enumerate(hazards(row)):
        yy=top+30+i*17
        text(c,hazard_labels.get(label,label),x+10,yy+2,5.65,INK)
        level={'None':0,'1-2 events':1,'3-5 events':2,'> 5 events':3}.get(answer)
        for k in range(3):
            fill=(BLUE if level is not None and k<level else '#DFE8ED')
            rect(c,x+112+11*k, yy+4, 8, 8, fill, r=2)
        label_short={'None':'None','1-2 events':'1–2','3-5 events':'3–5',
                     '> 5 events':'>5'}.get(answer,'N/R')
        right(c,label_short,x+width-9,yy+1,5.9,
              BLUE if level is not None and level>0 else MUTED,True)
    text(c,'Frequency bands: none · 1–2 · 3–5 · >5',
         x+10,top+96,4.7,MUTED)

    resource_top = top+116
    section_panel(c,x,resource_top,width,112,'Operational resources')
    names={
        'Dedicated room':'Dedicated room','Shared room':'Shared room',
        'Virtual coordination':'Virtual platform','Communications':'Communications',
        'Situation displays':'Situation displays','Backup power':'Backup power',
        'Redundant internet':'Backup internet','Team workstations':'Workstations',
    }
    # 2 columns of four rows, with the dot conveying yes / no / unreported.
    cell_w=(width-27)/2
    for i,(label,idx) in enumerate(RESOURCES):
        xx=x+10+(i%2)*(cell_w+7)
        yy=resource_top+33+(i//2)*18
        selected_value=selected(row,idx)
        if selected_value is True:
            rect(c,xx,yy+3,6.7,6.7,BLUE,r=3.3)
        elif selected_value is False:
            c.setStrokeColor(col('#A9BDC8'));c.setLineWidth(.8)
            c.circle(xx+3.3,PAGE_H-(yy+6.4),3.3,fill=0,stroke=1)
        else:
            text(c,'–',xx+1,yy,6.5,MUTED)
        name=names.get(label,label)
        text(c,name,xx+10,yy+1,fit_text_size(name,cell_w-10,5.9,4.8),
             INK if selected_value else MUTED)
    text(c,'● Reported     ○ Not selected     – Missing',
         x+10,resource_top+101,4.55,MUTED)

    training_top = top+238
    section_panel(c,x,training_top,width,124,'Training')
    text(c,'✓ Completed     ★ Priority to strengthen',
         x+10,training_top+26,5.15,MUTED)
    alias={
        'EOC activation':'EOC activation',
        'Incident management':'Incident mgmt',
        'Information management':'Information mgmt',
        'Coordination':'Coordination',
        'Damage / needs assessment':'Damage / needs',
        'Rapid situation analysis':'Situation analysis',
        'Rapid response teams':'Response teams',
        'After-action reviews':'After-action review',
    }
    cw=(width-27)/2
    for i,(label,done_idx,priority_idx) in enumerate(TRAININGS):
        xx=x+10 + (i%2)*(cw+7)
        yy=training_top+38+(i//2)*20.5
        done=selected(row,done_idx)
        priority=selected(row,priority_idx)
        active = done is True or priority is True
        rect(c,xx,yy,cw,17.4,PALE if active else '#F2F6F8',r=5)
        short=alias.get(label,label)
        text(c,short,xx+5,yy+5,fit_text_size(short,cw-24,5.6,4.65),
             INK if active else MUTED)
        if done is True:
            right(c,'✓',xx+cw-13,yy+3.5,7.0,BLUE,True)
        if priority is True:
            right(c,'★',xx+cw-3,yy+4.2,6.0,ORANGE,True)
    return training_top+124


def bullet_metrics(items, width, font_size):
    style=ParagraphStyle('noteMeasure',fontName=FONT,fontSize=font_size,
                         leading=font_size*1.37,spaceAfter=0)
    heights=[]
    for item in items[:3]:
        para=Paragraph(html.escape(str(item)),style)
        _,h=para.wrap(width-23,1000)
        heights.append(max(12.1,h)+3.6)
    return heights


def narrative_panel(c, items, x, top, width, title, fill, accent):
    """Independently auto-sized note box, aligned at the top but not bottom."""
    usable=width-20
    fs=6.65
    heights=bullet_metrics(items,usable,fs)
    while fs>5.65 and 30+sum(heights)+5>106:
        fs-=.25
        heights=bullet_metrics(items,usable,fs)
    card_h=max(46,min(106,30+sum(heights)+5))
    rect(c,x,top,width,card_h,fill,r=7)
    text(c,title,x+11,top+10,7.0,accent,True)
    yy=top+29
    for text_item,line_h in zip(items[:3],heights):
        rect(c,x+12,yy+4,4,4,accent,r=2)
        paragraph(c,text_item,x+22,yy,usable-23,size=fs,
                  leading=fs*1.37,maxheight=line_h-2)
        yy+=line_h
    return card_h


def footer(c,country,source_row):
    rule(c,40,572,742,LINE)
    text(c,'SOURCE  PAHO/WHO Regional Survey on Health Emergency Operations Centres (2026)',40,752,6.1,BLUE,True)
    text(c,f'{country} · Source Excel row {source_row} · Self-reported information · Not independently verified',40,763,5.5,MUTED)
    text(c,'Indicative 24-item, 1–5 maturity scores (rescaled 0–100). Orange = responding-country mean; not a PAHO assessment.',40,774,5.0,MUTED)
    right(c,'paho.org',572,753,7,BRIGHT,True)


def core_single(c,country,row,region_means):
    inst=organization(row)
    paragraph(c,inst,42,151,528,size=9.0,color=INK,bold=True,maxheight=27)
    metrics=[(val(row,17) if val(row,17) and val(row,17)!='1900' else '—','Established'),
         (english_mode(row),'Operating mode'),(english_activation(row),'Activation time'),
         (english_mandate(row),'Mandate'),
         (str(number(row,67)) if number(row,67) is not None else '—','24/7 duty staff')]
    xs=[40,148,256,364,472]
    for (k,v),x in zip(metrics,xs):metric(c,x,188,100,k,v)
    cap_bars(c,row,40,250,323,region_means)
    attribute_table(c,row,40,399,323)
    side(c,row,375,250,197)
    a,b=narrative_for(country,row)
    narrative_panel(c,a,40,626,260,'REPORTED STRENGTHS',PALE2,BLUE)
    narrative_panel(c,b,312,626,260,'IMPROVEMENT PRIORITIES','#FFF5F0',ORANGE)


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


def do_page(c,country,row,page_idx,total,response_number,responses_in_country,source_row,region_means):
    header(c,country,row,page_idx,total,response_number,responses_in_country)
    if status(row) is False:
        core_no_eoc(c,country,row)
    else:
        core_single(c,country,row,region_means)
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
    region_means=responding_country_means(reports)
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
        do_page(c,country,row,page_idx,len(pages),response_number,n,source_row,region_means)
    c.save()
    for page_idx,(country,row,response_number,n,source_row,slug) in enumerate(pages,1):
        dest=out_country/f'{slug}.pdf'
        single=canvas.Canvas(str(dest),pagesize=letter,pageCompression=1)
        single.setTitle(f'{country} · Response {response_number}/{n} | PAHO EOC 2026')
        do_page(single,country,row,page_idx,len(pages),response_number,n,source_row,region_means)
        single.save()
    print(f'Generated {len(pages)} pages from {len(pages)} survey responses, '
          f'{len(reports)} distinct countries: {combined}')
    print('Benchmark (equal country weight):', [(name, round(mean, 1) if mean is not None else None, n) for name,mean,n in region_means])
    print('Individual pages:', ', '.join(p.name for p in sorted(out_country.glob('*.pdf'))))

if __name__=='__main__':main()