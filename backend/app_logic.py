"""backend/app_logic.py — Pure business logic extracted from app.py.

No Streamlit imports. All functions are independently testable.
Imported by app.py via: from backend.app_logic import <name>
"""

# ── Azimuth direction filter ───────────────────────────────────────────────

_AZ_OCTANTS = {
    "N":  [(337.5, 360.0), (0.0, 22.5)],
    "NE": [(22.5,  67.5)],
    "E":  [(67.5,  112.5)],
    "SE": [(112.5, 157.5)],
    "S":  [(157.5, 202.5)],
    "SW": [(202.5, 247.5)],
    "W":  [(247.5, 292.5)],
    "NW": [(292.5, 337.5)],
}
_AZ_LABELS   = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
_AZ_CAPTIONS = {
    "N":  "337.5–22.5°",
    "NE": "22.5–67.5°",
    "E":  "67.5–112.5°",
    "SE": "112.5–157.5°",
    "S":  "157.5–202.5°",
    "SW": "202.5–247.5°",
    "W":  "247.5–292.5°",
    "NW": "292.5–337.5°",
}


def az_in_selected(az_deg: float, selected_dirs: set) -> bool:
    """Return True if az_deg falls within any of the selected compass octants."""
    for d in selected_dirs:
        for lo, hi in _AZ_OCTANTS[d]:
            if lo <= az_deg < hi:
                return True
    return False
