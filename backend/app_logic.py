"""backend/app_logic.py — Pure business logic extracted from app.py.

No Streamlit imports. All functions are independently testable.
Imported by app.py via: from backend.app_logic import <name>
"""

from astropy.coordinates import AltAz
from astropy.time import Time
from backend.core import moon_sep_deg

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


# ── Moon status ────────────────────────────────────────────────────────────

_MOON_DARK_SKY_ILLUM = 15   # illumination % below which it's "Dark Sky"
_MOON_AVOID_SEP      = 30   # separation ° below which it's "Avoid"
_MOON_CAUTION_SEP    = 60   # separation ° below which it's "Caution"


def get_moon_status(illumination: float, separation: float) -> str:
    """Return moon status emoji string for a given illumination % and separation °."""
    if illumination < _MOON_DARK_SKY_ILLUM:
        return "🌑 Dark Sky"
    elif separation < _MOON_AVOID_SEP:
        return "⛔ Avoid"
    elif separation < _MOON_CAUTION_SEP:
        return "⚠️ Caution"
    else:
        return "✅ Safe"


# ── Row observability check ─────────────────────────────────────────────────

def _check_row_observability(sc, row_status, location, check_times, moon_loc, moon_locs_chk,
                              moon_illum, min_alt, max_alt, az_dirs, min_moon_sep):
    """Compute observability for a single target row.

    Args:
        sc:            SkyCoord of the target.
        row_status:    Value of the 'Status' column (string, e.g. "Never Rises").
        location:      EarthLocation of the observer.
        check_times:   List of 3 datetime objects (start, mid, end of window).
        moon_loc:      Moon coordinate at start time (or None if unavailable).
        moon_locs_chk: List of moon coordinates at each check_time (or []).
        moon_illum:    Moon illumination 0-100 float.
        min_alt:       Minimum altitude filter (degrees).
        max_alt:       Maximum altitude filter (degrees).
        az_dirs:       Set of selected compass octant labels (empty = no filter).
        min_moon_sep:  Minimum moon separation filter (degrees).

    Returns:
        (obs: bool, reason: str, moon_sep_str: str, moon_status_str: str)
    """
    _seps = [moon_sep_deg(sc, ml) for ml in moon_locs_chk] if moon_locs_chk else []
    _min_sep = min(_seps) if _seps else (moon_sep_deg(sc, moon_loc) if moon_loc else 0.0)
    _max_sep = max(_seps) if _seps else _min_sep
    moon_sep_str    = f"{_min_sep:.1f}°–{_max_sep:.1f}°" if moon_loc else "–"
    moon_status_str = get_moon_status(moon_illum, _min_sep) if moon_loc else ""

    if str(row_status) == "Never Rises":
        return False, "Never Rises", moon_sep_str, moon_status_str

    obs, reason = False, "Not visible during window"
    for i_t, t_chk in enumerate(check_times):
        aa = sc.transform_to(AltAz(obstime=Time(t_chk), location=location))
        if min_alt <= aa.alt.degree <= max_alt and (not az_dirs or az_in_selected(aa.az.degree, az_dirs)):
            sep_ok = (not moon_locs_chk) or (moon_sep_deg(sc, moon_locs_chk[i_t]) >= min_moon_sep)
            if sep_ok:
                obs, reason = True, ""
                break
    return obs, reason, moon_sep_str, moon_status_str
