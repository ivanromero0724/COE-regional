"""Layout and navigation regressions, without requiring a browser or Streamlit."""
from pathlib import Path
import pandas as pd
from dashboard import charts
from dashboard.data import HAZARD_LABELS

ROOT = Path(__file__).resolve().parents[1]


def test_methods_data_page_removed():
    app = (ROOT / 'app.py').read_text(encoding='utf-8')
    assert "['Regional overview','Country profiles']" in app
    assert 'Methods & data' not in app
    assert 'def methodology(' not in app
    assert 'maturity_radar' not in app


def test_hazard_heatmap_has_legible_labels():
    cats = list(HAZARD_LABELS.values())
    data = pd.DataFrame([
        dict(country='Argentina', **dict(zip(cats, (1.0, 3.0, 0.0, float('nan'))))),
        dict(country='Belize', **dict(zip(cats, (2.0, 1.0, 1.0, 0.0))))])
    fig = charts.hazard_heatmap(data)
    assert len(fig.layout.annotations) == 8
    assert list(fig.data[0].x) == ['Geo / weather','Biological','Social','Technological']
    assert len(fig.data[0].y) == 2
    assert 'Not reported' in fig.data[0].customdata[0]

def test_streamlit_header_is_opaque_and_fixed():
    app = (ROOT / 'app.py').read_text(encoding='utf-8')
    header_css = app.split('[data-testid="stHeader"]{', 1)[1].split('}', 1)[0]
    assert 'position:fixed!important;' in header_css
    assert 'top:0!important;' in header_css
    assert 'background:#F7FAFC!important;' in header_css
    assert 'background-image:none!important;' in header_css
    assert 'opacity:1!important;' in header_css
    assert 'backdrop-filter:none!important;' in header_css
    assert 'background:rgba(247,250,252,.93)' not in app


def test_banner_clears_fixed_streamlit_toolbar():
    app = (ROOT / 'app.py').read_text(encoding='utf-8')
    assert 'position:fixed!important;' in app
    assert 'padding:3.25rem 1.35rem 2.6rem;' in app
    assert 'padding-top:2.75rem;' in app
    assert 'background:#F7FAFC!important;' in app
