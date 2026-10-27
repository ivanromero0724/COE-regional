"""Regression checks for matching heights of paired dashboard visualizations."""
from pathlib import Path
from dashboard import charts
from dashboard.data import load_data, country_aggregate

APP = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")


def test_paired_panels_have_shared_desktop_height_and_mobile_release():
    for pair in ("overview", "capacities", "cooperation"):
        assert f".card-panel.eoc-pair-{pair}" in APP
        assert f"pair='{pair}'" in APP or pair == "overview"
    assert "eoc-pair-heading" in APP
    assert "min-height:0;" in APP
    assert "eoc-pair-infrastructure" in APP


def test_geo_map_and_operation_card_share_500px():
    records, _ = load_data()
    fig = charts.countries_map(country_aggregate(records))
    assert fig is not None
    assert fig.layout.height == 500
    assert ".card-panel.eoc-pair-overview{min-height:500px" in APP


def test_country_hazards_and_infrastructure_share_390px():
    records, _ = load_data()
    fig = charts.country_hazards(records.iloc[0])
    assert fig.layout.height == 390
    assert ".status-tile-grid.eoc-pair-infrastructure{min-height:390px" in APP
