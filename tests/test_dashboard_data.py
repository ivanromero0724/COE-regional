"""Smoke and consistency tests for the 2026 EOC-S Streamlit dashboard.

These tests deliberately do not hard-code 15/16 as future survey updates should
continue to build. Existing country maturity scores must match PDF scoring.
"""
from dashboard.data import (
 load_data,country_aggregate,capacity_table,domain_benchmark,DOMAINS,CAPACITIES,
 XLSX,GPKG,country_capacity,RESOURCE_LABELS,NETWORK_NAMES,safe_csv
)
import pandas as pd
import pytest


def test_schema_and_unique_keys():
    a,raw=load_data()
    b=country_aggregate(a)
    assert len(a)==len(raw)
    assert b.country.is_unique
    assert set(a.country)==set(b.country)
    assert a.record_id.is_unique
    assert set(DOMAINS).issubset(a.columns)


def test_maturity_same_as_pdf_generator():
    from scripts.generate_country_profiles import scores
    a,raw=load_data()
    for i in range(len(raw)):
        for _,(domain,value,_,_) in enumerate(scores(raw.iloc[i].tolist())):
            assert a.iloc[i][domain]==value


def test_capacity_denominators_and_country_level_union():
    a,_=load_data();countries=country_aggregate(a);caps=capacity_table(countries)
    assert caps['in_place'].ge(0).all()
    assert caps['denominator'].le(len(countries)).all()
    assert caps['in_place'].le(caps['denominator']).all()
    assert 'Updated surge roster' in set(caps.capacity)
    assert 'Integrated/interoperable platform' in set(caps.capacity)
    col=countries.query("country == 'Colombia'").iloc[0]
    assert col.institutions==len(a.query("country == 'Colombia'"))


def test_redaction_in_export():
    a,_=load_data();c=country_aggregate(a)
    data=safe_csv(c).decode('utf-8-sig')
    for sensitive in ['Teléfono','Correo electrónico','Nombre  de la persona','_uuid','Reported strengths']:
        assert sensitive not in data


def test_map_input_matches_country_codes():
    if not GPKG.is_file():pytest.skip('Geographic input not present in local test container')
    import geopandas as gpd
    geo=gpd.read_file(GPKG)
    assert {'ISO_CC','COUNTRY'}.issubset(geo.columns)
    a,_=load_data()
    missing=set(a.iso3)-set(geo.ISO_CC)
    assert not missing, f'Survey ISO3 not found in GeoPackage: {missing}'