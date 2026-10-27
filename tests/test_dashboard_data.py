"""Checks for the survey-driven Streamlit dashboard (no PDF generator or maturity index)."""
from dashboard.data import (
 load_data,country_aggregate,capacity_table,CAPACITIES,
 XLSX,GPKG,country_capacity,RESOURCE_LABELS,NETWORK_NAMES,safe_csv
)
import pandas as pd
import pytest


def test_schema_and_unique_keys():
    records,raw=load_data()
    countries=country_aggregate(records)
    assert len(records)==len(raw)
    assert countries.country.is_unique
    assert set(records.country)==set(countries.country)
    assert records.record_id.is_unique
    assert 'Governance & legal' not in records.columns
    assert not any(col.startswith('level_') or col.startswith('N_') for col in records.columns)


def test_capacity_denominators_and_colombia():
    records,_=load_data()
    countries=country_aggregate(records)
    caps=capacity_table(countries)
    assert caps['in_place'].ge(0).all()
    assert caps['denominator'].le(len(countries)).all()
    assert caps['in_place'].le(caps['denominator']).all()
    assert 'Updated surge roster' in set(caps.capacity)
    assert 'Integrated/interoperable platform' in set(caps.capacity)
    col=countries.query("country == 'Colombia'").iloc[0]
    assert col.institutions==len(records.query("country == 'Colombia'"))


def test_no_composite_scores_in_safe_export():
    records,_=load_data();countries=country_aggregate(records)
    safe=safe_csv(countries).decode('utf-8-sig')
    for name in ['Teléfono','Correo electrónico','Nombre  de la persona',
                 '_uuid','Reported strengths','Governance & legal','Information management']:
        assert name not in safe


def test_map_input_matches_country_codes():
    if not GPKG.is_file():pytest.skip('GeoPackage not in local test container')
    import geopandas as gpd
    geo=gpd.read_file(GPKG)
    assert {'ISO_CC','COUNTRY'}.issubset(geo.columns)
    records,_=load_data()
    missing=set(records.iso3)-set(geo.ISO_CC)
    assert not missing, f'Survey ISO3 not found in GeoPackage: {missing}'

def test_question_15_formal_document_has_valid_responses():
    records,_=load_data()
    countries=country_aggregate(records)
    valid=countries.formal_document.dropna()
    assert len(valid)>0, 'Question 15 must contain country-level yes/no responses'
    assert set(valid.unique()).issubset({True,False})


def test_capacity_abbreviations_across_all_components_and_languages():
    """Match every actual choice in the bundled survey to a specific bilingual label."""
    from dashboard.capacity_labels import labels_for_question
    from app import capacity_response_distribution
    records,_=load_data()
    countries=country_aggregate(records)
    frame=capacity_table(countries)
    for component in CAPACITIES:
        selected=frame.loc[frame.component==component]
        assert len(selected)==len(CAPACITIES[component])
        for _,indicator in selected.iterrows():
            counts=capacity_response_distribution(countries,indicator)
            for language in ('es','en'):
                labels=labels_for_question(int(indicator['col']),counts.index,language)
                assert len(labels)==len(set(labels)), (component,indicator.capacity,language,labels)
                assert all(x and not x.startswith(('Other response','Otra respuesta','Option ','Opción '))
                           for x in labels), (component,indicator.capacity,language,labels)
    assert labels_for_question(37,['a. Sí','b. No','c. Parcialmente o En desarrollo'],'en')==[
        'Yes','No','Partial / developing']
    assert labels_for_question(108,['a. Crítico','b. Alto','c. Moderado','d. Bajo'],'en')==[
        'Critical','High','Moderate','Low']


def test_disagreement_between_institutions_uses_real_categories():
    """Colombia's two institutional responses cannot become a third category."""
    from app import capacity_response_distribution
    from dashboard.capacity_labels import labels_for_question
    records,_=load_data()
    countries=country_aggregate(records)
    colombia=countries.loc[countries.country=='Colombia'].iloc[0]
    assert colombia.institutions==2
    for col in (29,32,36,37,55,66,78,107,123):
        choices=colombia[f'ANSWER_CHOICES_{col}']
        assert len(choices)==2
        assert '__MIXED__' not in choices
        indicator=pd.Series({'col':col})
        distribution=capacity_response_distribution(countries,indicator)
        assert '__MIXED__' not in distribution.index
        assert abs(distribution.sum()-sum(bool(x) for x in countries[f'ANSWER_CHOICES_{col}']))<1e-8
        assert all('Different responses' not in x for x in
                   labels_for_question(col,distribution.index,'en'))
    # The mutually conflicting Colombian answers each count as half a country.
    col32=capacity_response_distribution(countries,pd.Series({'col':32}))
    code_a=next(x for x in colombia['ANSWER_CHOICES_32'] if x.startswith('a.'))
    code_e=next(x for x in colombia['ANSWER_CHOICES_32'] if x.startswith('e.'))
    other=countries.loc[countries.country!='Colombia']
    other_dist=capacity_response_distribution(other,pd.Series({'col':32}))
    assert abs(col32[code_a]-other_dist.get(code_a,0)-0.5)<1e-8
    assert abs(col32[code_e]-other_dist.get(code_e,0)-0.5)<1e-8


def test_country_profile_reuses_actual_bilingual_capacity_answer_labels():
    """Chips must say Initial / Developing / Consolidated etc., not collapse
    all non-qualifying questionnaire answers into Partial / absent.
    """
    from app import country_answer_caption, status_grid_html
    from dashboard.capacity_labels import labels_for_question
    from html import escape
    records,_=load_data()
    for _,r in records.iterrows():
        for component,entries in CAPACITIES.items():
            for title,col,positive in entries:
                status=country_capacity(r,col,positive)
                for lang in ('en','es'):
                    actual=country_answer_caption(r,col,lang)
                    raw=r.get(f'ANSWER_{col}')
                    if raw is None or pd.isna(raw) or not str(raw).strip():
                        expected='Sin información' if lang=='es' else 'Not reported'
                    else:
                        expected=labels_for_question(col,[str(raw)],lang)[0]
                    assert actual==expected, (r.record_id,component,title,col,lang)
                    html=status_grid_html([(title,status,actual)])
                    assert escape(actual) in html
                    # Keep qualitative assessments separate from exact answers.
                    if status is False and actual!=expected:
                        raise AssertionError((title,actual,expected))
        for col,title in RESOURCE_LABELS.items():
            raw=r.get(f'ANSWER_{col}')
            for lang in ('en','es'):
                displayed=country_answer_caption(r,col,lang)
                if raw is None or pd.isna(raw) or not str(raw).strip():
                    assert displayed==('Sin información' if lang=='es' else 'Not reported')
                else:
                    assert displayed==labels_for_question(col,[str(raw)],lang)[0]
                html=status_grid_html([(title,r[title],displayed)],paired_infrastructure=True)
                assert escape(displayed) in html


def test_country_choice_abbreviations_keep_distinct_levels():
    from app import country_answer_caption
    records,_=load_data()
    # Existing data contains multiple valid maturity levels and original
    # single-choice answers must not be reduced to the same status string.
    seen=set()
    for _,r in records.iterrows():
        col=29
        response=r.get('ANSWER_29')
        if response is not None and not pd.isna(response):
            seen.add(country_answer_caption(r,col,'en'))
    assert len(seen)>=2
    assert 'Partial / absent' not in seen
