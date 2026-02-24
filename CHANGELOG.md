# Changelog

Bug fixes, discoveries, and notable changes. See CLAUDE.md for architecture and patterns.

---

## 2026-02-23 — Moon Separation calculation was completely wrong

**Bug:** Every Moon Sep value across all six sections was incorrect. Example: ZTF25abwjewp (RA 10h 24m, Dec +5°15') showed 4.4°–4.5° when the true separation was ~98°.

**Root cause:** Astropy's `get_body('moon')` returns a 3D GCRS coordinate with distance (~364,000 km). When computing `target.separation(moon)` where the target is in ICRS (at infinity) and the Moon is in GCRS (with finite distance), the cross-frame non-rotation transformation produces garbage angular separations. Astropy emits a `NonRotationTransformationWarning` for this, but it was suppressed by `warnings.filterwarnings("ignore")` in app.py line 44.

**Impact:** All Moon Sep values in all overview tables, trajectory views, Moon Sep filters, and Moon Status classifications were wrong since the feature was introduced. Objects near the Moon could show large separations (hiding Moon interference warnings), and objects far from the Moon could show small separations (incorrectly filtering them out).

**Fix:** Added `moon_sep_deg(target, moon)` helper in `backend/core.py` that strips the Moon's distance before computing separation, turning it into a direction-only unit-sphere coordinate. Replaced all 16 direct `.separation(moon)` calls across `app.py` and `backend/core.py`.

**Verification:**
```
OLD (broken): target.separation(moon_gcrs)           = 4.47°
NEW (fixed):  moon_sep_deg(target, moon_gcrs)        = 98.08°
Manual formula (spherical trig):                      = 98.08°
```

**Files changed:** `backend/core.py` (new helper + trajectory fix), `app.py` (16 call sites), `.gitignore` (added temp/).

**Commit:** `8373d94`
