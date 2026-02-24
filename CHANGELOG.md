# Changelog

Bug fixes, discoveries, and notable changes. See CLAUDE.md for architecture and patterns.

---

## 2026-02-24 — Migrate scrapers from Selenium to Scrapling + add priority removal detection

**Change 1 — Scraper migration:** Replaced Selenium + webdriver-manager with [Scrapling](https://github.com/D4Vinci/Scrapling) (`StealthyFetcher`) in `backend/scrape.py`. Scrapling uses Patchright (Playwright fork) — no more ChromeDriver version mismatches. Added `_deep_text()` helper because Scrapling's `.text` only returns direct text nodes (Selenium's `.text` returns all descendant text). Tested side-by-side: identical output across all 3 scrapers (transient events 78/78 rows, comet missions 7/7, asteroid missions 2/2). Scrapling also bypasses Cloudflare browser checks that block headless Selenium.

**Change 2 — Priority removal detection:** The app already detected when Unistellar *added* new priority targets. Now it also detects *removals* — objects in our `unistellar_priority` list that are no longer on Unistellar's missions page. Removals appear as pending requests in the admin panel (Accept removes from YAML priority list, Reject dismisses). Orange warning banners shown in the Priority expanders.

**Change 3 — GitHub Actions priority sync:** New workflow `check-unistellar-priorities.yml` (Mon + Thu 07:00 UTC) scrapes both Unistellar mission pages, compares with YAML, and creates GitHub Issues with `priority-added` (green) or `priority-removed` (red) labels. Supports `# aka 3I/ATLAS` YAML comments for redesignated objects (avoids false add/remove pairs when an object gets a new designation).

**Change 4 — Watchlist sync:** Updated `comets.yaml` (tagged C/2025 N1 as `# aka 3I/ATLAS`, removed 24P/Schaumasse from priority) and `asteroids.yaml` (removed 433 Eros, 2033 Basilea, 3260 Vizbor from priority — no longer on Unistellar's page).

**Files changed:** `backend/scrape.py`, `app.py`, `requirements.txt`, `comets.yaml`, `asteroids.yaml`, `.gitignore`, `CLAUDE.md`. **New files:** `scripts/check_unistellar_priorities.py`, `scripts/open_priority_issues.py`, `.github/workflows/check-unistellar-priorities.yml`.

---

## 2026-02-24 — Fix asteroid priority scraper (find all 5 Unistellar missions)

**Bug:** `scrape_unistellar_priority_asteroids()` only found 2 of 5 priority asteroids (2001 FD58, 1796 Riga). Missing: 433 Eros, 2033 Basilea, 3260 Vizbor.

**Root cause:** The scraper used regex on the full page body text. Unistellar's planetary defense page uses three different naming formats in `<h3>` headings:
- `2001 FD58` — standard provisional designation (regex matched)
- `2033 (Basilea)` — number then parenthesized name (regex missed)
- `Eros` — bare name with no number (regex missed)

**Fix:** Rewrote scraper to extract targets from `<h3>` headings directly instead of regex on body text. Added `_BARE_NAME_ALIASES` dict for well-known bare names (Eros→433 Eros, Apophis→99942 Apophis, etc.), `_NUM_PAREN_NAME_RE` regex to normalize `2033 (Basilea)` → `2033 Basilea`, and `_SKIP_HEADINGS` set to filter page-structure headings. Updated `asteroids.yaml` to include all 5 in `unistellar_priority`.

**Files changed:** `backend/scrape.py`, `asteroids.yaml`, `CLAUDE.md`.

---

## 2026-02-24 — Fix Scrapling browser issues (Streamlit Cloud + Windows)

**Bug 1 — Streamlit Cloud:** Cosmic page scraper failed with "Failed to scrape data". Patchright (Playwright fork) needs a Chromium browser binary installed, which isn't pre-installed on Streamlit Cloud.

**Fix:** Added `_ensure_browser()` that runs `patchright install chromium` once per session before the first scrape. Updated `packages.txt` from Selenium system deps (chromium, chromium-driver) to the ~20 system libraries Patchright's Chromium needs on Linux (libnss3, libgbm1, etc.).

**Bug 2 — Windows local:** `NotImplementedError` from `asyncio.base_events._make_subprocess_transport`. Windows' default `SelectorEventLoop` doesn't support subprocess creation, which Playwright needs to launch Chromium.

**Fix:** Added `_fetch_page(url, **kwargs)` wrapper that runs `StealthyFetcher.fetch()` in a `ThreadPoolExecutor` worker thread and sets `asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())` process-wide on `win32`. The process-wide policy is required because Playwright creates its own event loop in a background thread via `new_event_loop()` — per-thread `set_event_loop()` doesn't affect it.

**Files changed:** `backend/scrape.py`, `packages.txt`.

---

## 2026-02-24 — Simplify Night Plan Builder + add Moon Status filter

**Change 1 — Remove scheduling columns:** Removed Obs Start/End columns from the Night Plan table and PDF. The builder now returns a priority-sorted target list — the user decides when to observe each target. `build_night_plan()` no longer takes `start_time`/`end_time` parameters.

**Change 2 — Remove scheduling metrics:** Removed "Scheduled Time" and "Remaining Window" metrics. A single "Targets Planned" metric is shown above the table.

**Change 3 — Add Moon Status filter:** Added Moon Status multiselect to the Night Plan Builder's filter row (5th column). Options: 🌑 Dark Sky, ✅ Safe, ⚠️ Caution, ⛔ Avoid. All selected by default; only filters when the user deselects at least one status.

**Files changed:** `app.py`, `CLAUDE.md`.

**Branch:** `feature/night-plan-simplify`

---

## 2026-02-24 — Sync Gantt chart sort with overview table sort

**Change:** The Gantt chart sort radio buttons (Earliest Set / Rise / Transit / Default) now also reorder the overview table below. Previously, the chart and table were completely decoupled — the chart visual reordered but the table always stayed in its original order.

**Implementation:**
- `plot_visibility_timeline()` now returns the selected `sort_option` string (was implicit `None`)
- New `_sort_df_like_chart(df, sort_option, priority_col)` helper reorders the DataFrame to match the chart's sort
- All 6 call sites (DSO, Planet, Comet My List, Comet Catalog, Asteroid, Cosmic) capture the return and sort the table DataFrame before display
- `display_dso_table()` no longer sorts by magnitude internally — it receives the pre-sorted DataFrame from the caller

**Always Up handling:** For Earliest Rise/Set/Transit sorts, Always Up objects are pushed to the bottom of the table (sorted by transit among themselves), matching the Gantt chart. For Priority/Default/Discovery Date sorts, they stay in their ranked position.

**Files changed:** `app.py`, `CLAUDE.md`.

**Branch:** `feature/night-plan-simplify`

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

---

## 2026-02-23 — Moon Status column reintroduced in all overview tables

**Change:** `Moon Status` (🌑 Dark Sky / ⛔ Avoid / ⚠️ Caution / ✅ Safe) was previously computed but intentionally hidden because the underlying Moon Sep values were broken. Now that Moon Sep is fixed, Moon Status is shown as a separate column next to `Moon Sep (°)` in all overview tables (DSO, Planet, Comet, Asteroid, Cosmic), CSV exports, and the Night Plan PDF.

**Not included:** The per-step trajectory view (`compute_trajectory`) does not show Moon Status — it only shows the numeric `Moon Sep (°)` at each 10-minute step. Moon Status is an overview-level summary based on worst-case separation, not a per-step metric.

**Scope:** Removed `"Moon Status"` from all `.drop()` calls and column exclusion lists. Added to `display_cols_*` in all 5 sections, `_MOON_SEP_COL_CONFIG`, and `generate_plan_pdf()` column layout.

**Commit:** `b46a031`
