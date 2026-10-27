"""Bilingual UI and percentage labeling regression tests."""

import pandas as pd
from dashboard.data import load_data, country_aggregate, capacity_table, TRAINING_LABELS
from dashboard.i18n import tr
from dashboard import charts


def test_english_default_and_spanish_labels():
    assert tr('Country profiles', 'en') == 'Country profiles'
    assert tr('Country profiles', 'es') == 'Perfiles por país'
    assert tr('Regional overview', 'es') == 'Panorama regional'
    assert tr('Not reported', 'es') == 'Sin información'
    assert tr('Brazil', 'es') == 'Brasil'
    assert tr('Information management', 'es') == 'Gestión de información'


def test_chart_percent_denominators_are_valid():
    raw, _ = load_data()
    countries = country_aggregate(raw)
    scores = capacity_table(countries)
    assert len(raw) == 16 and len(countries) == 15
    assert scores.denominator.between(0, len(countries)).all()
    assert scores.in_place.le(scores.denominator).all()
    positive = scores[scores.denominator.gt(0)].copy()
    fig = charts.horizontal_bars(positive.head(7), lang='es')
    assert '%' in ' '.join(fig.data[0].text)
    assert '/' in ' '.join(fig.data[0].text)
    assert all(0 <= float(v) <= 100 for v in fig.data[0].x)


def test_training_chart_shows_percent_and_fraction_in_both_languages():
    rows, _ = load_data()
    frame = country_aggregate(rows)
    data = []
    for course in TRAINING_LABELS:
        completed = frame['Completed: ' + course].dropna()
        priority = frame['Priority: ' + course].dropna()
        data.append({'area': course, 'done_n': sum(bool(x) for x in completed),
                     'done_d': len(completed), 'priority_n': sum(bool(x) for x in priority),
                     'priority_d': len(priority)})
    for lang in ['en', 'es']:
        fig = charts.training_comparison(pd.DataFrame(data), lang=lang)
        assert len(fig.data) == 2
        for trace in fig.data:
            assert len(trace.text) == len(TRAINING_LABELS)
            assert all('%' in text and '/' in text for text in trace.text if text != '—')
    assert charts.country_training(rows.iloc[0], lang='es').data[0].z is not None
    assert charts.country_hazards(rows.iloc[0], lang='es').data[0].x is not None

def test_map_presence_title_translates_in_both_languages():
    assert tr('Which countries have EOC-S?', 'en') == 'Which countries have EOC-S?'
    assert tr('Which countries have EOC-S?', 'es') == '¿Qué países tienen COE-S?'
    assert tr('01 / EOC-S STATUS', 'es') == '01 / ESTADO DE LOS COE-S'
    assert 'sin respuesta' in tr(
        'Established or in implementation; countries without survey responses remain gray.', 'es'
    )
