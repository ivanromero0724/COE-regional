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


def test_regional_sections_and_explanations_translate_consistently():
    assert tr('Capacities, gaps & training','en')=='Capacities, gaps & training'
    assert tr('Capacities, gaps & training','es')=='Capacidades, brechas y capacitación'
    assert tr('Explore capacities in detail','es')=='Explorar capacidades en detalle'
    assert tr('01 / REPORTED CAPACITIES','es')=='01 / CAPACIDADES REPORTADAS'
    assert tr('02 / COOPERATION PRIORITIES','es')=='02 / PRIORIDADES DE COOPERACIÓN'
    assert tr('03 / CAPACITY PROFILES','es')=='03 / PERFILES DE CAPACIDADES'
    assert tr('04 / WORKFORCE DEVELOPMENT','es')=='04 / DESARROLLO DEL PERSONAL'
    training='For each training area, compare the share of countries reporting training completed in the past year with the share prioritizing it for the next period.'
    hazard='Responses indicate frequency categories (0, 1–2, 3–5, more than 5), not exact event totals.'
    assert tr(training,'es').startswith('Para cada tema')
    assert tr(hazard,'es').startswith('Las respuestas indican rangos de frecuencia')


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
            # Keep the labels compact; full counts stay available on hover.
            assert all('%' in value for value in trace.text if value != '—')
            assert '%{customdata[0]}/%{customdata[1]}' in trace.hovertemplate
            assert all(0 <= n <= d <= len(frame) for n,d in trace.customdata)
    assert charts.country_training(rows.iloc[0], lang='es').data[0].z is not None
    assert charts.country_hazards(rows.iloc[0], lang='es').data[0].x is not None

def test_map_presence_title_translates_in_both_languages():
    assert tr('Which countries have an H-EOC?', 'en') == 'Which countries have an H-EOC?'
    assert tr('Which countries have an H-EOC?', 'es') == '¿Qué países tienen COE-S?'
    assert tr('01 / H-EOC STATUS', 'es') == '01 / ESTADO DE LOS COE-S'
    assert 'sin respuesta' in tr(
        'Established or in implementation; countries without survey responses remain gray.', 'es'
    )


def test_health_eoc_acronym_matches_selected_language():
    """English uses H-EOC; the Spanish interface consistently uses COE-S."""
    translations={
        'H-EOC · Americas':'COE-S · Américas',
        'Established H-EOC':'COE-S establecidos',
        'Which countries have an H-EOC?':'¿Qué países tienen COE-S?',
        '01 / H-EOC STATUS':'01 / ESTADO DE LOS COE-S',
        'How the H-EOC operates':'¿Cómo operan los COE-S?',
        'H-EOC status':'Estado del COE-S',
    }
    for english,spanish in translations.items():
        assert tr(english,'en')==english
        assert tr(english,'es')==spanish
    from pathlib import Path
    app=(Path(__file__).resolve().parents[1]/'app.py').read_text(encoding='utf-8')
    for english in translations:
        assert english in app
    assert 'EOC-S' not in app


def test_institutional_narratives_are_reviewed_bilingually_without_editing_excel():
    from dashboard.narratives import REVIEWED,narrative_for_display
    from dashboard.data import load_data
    records,_=load_data()
    by_id=records.set_index('record_id')
    assert len(REVIEWED)>=18
    for (record_id,kind),(prefix,spanish,english) in REVIEWED.items():
        assert record_id in by_id.index
        column=('Reported strengths (original language)' if kind=='strengths'
                else 'Improvement areas (original language)')
        original=by_id.loc[record_id,column]
        assert original.casefold().startswith(prefix.casefold()), (record_id,kind)
        assert narrative_for_display(record_id,kind,original,'es')==spanish
        assert narrative_for_display(record_id,kind,original,'en')==english
        assert spanish!=english
        assert len(spanish)>20 and len(english)>20
        # Updated survey input must never receive a stale translation.
        assert narrative_for_display(record_id,kind,'UPDATED ANSWER','en')=='UPDATED ANSWER'
    # No invented text for missing responses.
    assert narrative_for_display('COL-008','strengths','','es')=='No se proporcionó respuesta narrativa.'


def test_country_profile_hides_excel_rows_and_the_colombia_explanatory_note():
    from pathlib import Path
    source=(Path(__file__).resolve().parents[1]/'app.py').read_text(encoding='utf-8')
    scope=source.split('def country_profile(records,countries):',1)[1].split('def main():',1)[0]
    assert 'Excel row' not in scope
    assert 'source_excel_row' not in scope
    assert 'Each institution has its own response.' not in scope
    assert 'narrative_for_display(r.record_id,kind,r[source],chosen_language())' in scope
