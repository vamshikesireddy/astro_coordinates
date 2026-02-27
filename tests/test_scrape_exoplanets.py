"""Tests for scrape_unistellar_exoplanets() new return shape."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import patch, MagicMock


def _make_mock_page(headings, body_texts):
    """Build a mock Scrapling page with given headings and body text."""
    page = MagicMock()
    heading_elements = []
    for h in headings:
        el = MagicMock()
        el.text = h
        heading_elements.append(el)
    body_elements = []
    for t in body_texts:
        el = MagicMock()
        el.text = t
        body_elements.append(el)

    def css_side_effect(selector):
        if selector in ("h2", "h3", "h2,h3"):
            return heading_elements
        return body_elements + heading_elements

    page.css.side_effect = css_side_effect
    return page


def test_returns_dict_with_active_and_priority_keys():
    from backend.scrape import scrape_unistellar_exoplanets
    with patch("backend.scrape._ensure_browser"), \
         patch("backend.scrape._fetch_page") as mock_fetch, \
         patch("backend.scrape._deep_text", side_effect=lambda el: el.text):
        mock_fetch.return_value = _make_mock_page(
            headings=["WASP-43 b Campaign"],
            body_texts=["Study HAT-P-12 b transits", "WASP-43 b detailed info"],
        )
        result = scrape_unistellar_exoplanets()
    assert isinstance(result, dict)
    assert "active" in result
    assert "priority" in result


def test_priority_detected_from_heading():
    from backend.scrape import scrape_unistellar_exoplanets
    with patch("backend.scrape._ensure_browser"), \
         patch("backend.scrape._fetch_page") as mock_fetch, \
         patch("backend.scrape._deep_text", side_effect=lambda el: el.text):
        mock_fetch.return_value = _make_mock_page(
            headings=["WASP-43 b Campaign"],
            body_texts=["Study HAT-P-12 b transits", "WASP-43 b detailed info"],
        )
        result = scrape_unistellar_exoplanets()
    assert any("WASP-43" in p for p in result["priority"])
    assert any("HAT-P-12" in p for p in result["active"])
    assert not any("HAT-P-12" in p for p in result["priority"])


def test_returns_empty_dict_on_failure():
    from backend.scrape import scrape_unistellar_exoplanets
    with patch("backend.scrape._ensure_browser"), \
         patch("backend.scrape._fetch_page", return_value=None):
        result = scrape_unistellar_exoplanets()
    assert result == {"active": [], "priority": []}


def test_all_active_includes_priority():
    """Every priority planet is also in active."""
    from backend.scrape import scrape_unistellar_exoplanets
    with patch("backend.scrape._ensure_browser"), \
         patch("backend.scrape._fetch_page") as mock_fetch, \
         patch("backend.scrape._deep_text", side_effect=lambda el: el.text):
        mock_fetch.return_value = _make_mock_page(
            headings=["WASP-43 b featured"],
            body_texts=["WASP-43 b info"],
        )
        result = scrape_unistellar_exoplanets()
    for p in result["priority"]:
        assert p in result["active"], f"{p} in priority but not in active"
