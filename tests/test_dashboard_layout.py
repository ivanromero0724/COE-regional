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