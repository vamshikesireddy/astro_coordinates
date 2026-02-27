"""Tests for backend/app_logic.py — pure business logic."""
import pytest
from backend.app_logic import az_in_selected, _AZ_OCTANTS, _AZ_LABELS


def test_az_in_selected_single_dir():
    assert az_in_selected(90.0, {"E"}) is True      # E = 67.5–112.5
    assert az_in_selected(180.0, {"E"}) is False

def test_az_in_selected_empty_dirs_should_raise_or_return_false():
    # Empty set = no filter at call site, but function itself should return False
    assert az_in_selected(90.0, set()) is False

def test_az_in_selected_north_wrap():
    # N spans 337.5–360 AND 0–22.5 (wrap-around case)
    assert az_in_selected(350.0, {"N"}) is True
    assert az_in_selected(10.0, {"N"}) is True
    assert az_in_selected(180.0, {"N"}) is False

def test_az_in_selected_boundary_exclusive():
    # NE = [22.5, 67.5)
    assert az_in_selected(22.5, {"NE"}) is True
    assert az_in_selected(67.5, {"NE"}) is False   # upper bound exclusive

def test_az_in_selected_multiple_dirs():
    assert az_in_selected(90.0, {"E", "S"}) is True   # in E
    assert az_in_selected(180.0, {"E", "S"}) is True  # in S
    assert az_in_selected(270.0, {"E", "S"}) is False  # in W

def test_az_labels_order():
    assert _AZ_LABELS == ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]

def test_az_octants_all_dirs_present():
    for d in _AZ_LABELS:
        assert d in _AZ_OCTANTS
