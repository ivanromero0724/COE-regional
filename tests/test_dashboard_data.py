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