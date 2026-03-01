# AstroPlanner — Key Functions Reference

> Read this file when looking up where a function lives or planning where new logic goes.
> See `CLAUDE.md` for architecture overview.

---

### 6. Comet Mode Toggle

The Comet section has an internal radio toggle: `"📋 My List"` and `"🔭 Explore Catalog"`. My List is the default. My List code is completely unchanged by the Explore Catalog addition — it is wrapped in `if _comet_view == "📋 My List":`.

`get_comet_summary()` is **reused** by both modes. The Explore Catalog passes filtered designation tuples to it identically to My List.

---

## Key Functions Reference

| Function | File | Purpose |
|---|---|---|
| `az_in_selected()` | `backend/app_logic.py` | Check if azimuth falls in selected compass octants |
| `get_moon_status()` | `backend/app_logic.py` | Moon status emoji + label from illumination + separation |
| `_check_row_observability()` | `backend/app_logic.py` | Per-row alt/az/moon/sep observability check |
| `_sort_df_like_chart()` | `backend/app_logic.py` | Reorder DataFrame to match Gantt chart sort selection |
| `build_night_plan()` | `backend/app_logic.py` | Sort targets by set-time or transit-time for night plan |
| `_sanitize_csv_df()` | `backend/app_logic.py` | Escape formula-injection prefixes in CSV export |
| `_add_peak_alt_session()` | `backend/app_logic.py` | Add `_peak_alt_session` column to DataFrame |
| `_apply_night_plan_filters()` | `backend/app_logic.py` | Apply all 6 night plan filters (priority/mag/type/disc/window/moon) |
| `_get_dso_local_image()` | `backend/app_logic.py` | Local JPEG lookup for DSO image card; injectable `base_dir` for tests |
| `calculate_planning_info()` | `backend/core.py` | Rise/Set/Transit + Status per object |
| `moon_sep_deg()` | `backend/core.py` | Moon–target angular separation (strips 3D distance artifact) |
| `compute_trajectory()` | `backend/core.py` | Altitude/Az/RA/Dec/Constellation/Moon Sep (°) per 10-min step |
| `resolve_simbad()` | `backend/resolvers.py` | SIMBAD name lookup → SkyCoord |
| `resolve_horizons()` | `backend/resolvers.py` | JPL Horizons comet/asteroid position |
| `resolve_horizons_with_mag()` | `backend/resolvers.py` | JPL Horizons position + vmag (live fallback for dates >30 days); returns `(name, SkyCoord, vmag)` |
| `resolve_planet()` | `backend/resolvers.py` | JPL Horizons planet position |
| `_horizons_query()` | `backend/resolvers.py` | 3-level Horizons fallback (smallbody → search → regex); used by `resolve_horizons` + `get_horizons_ephemerides` |
| `sbdb_lookup()` | `backend/sbdb.py` | SBDB cascade resolver — SPK-ID lookup with multi-match disambiguation |
| `plot_visibility_timeline()` | `app.py` | Gantt chart (all sections); returns sort selection string |
| `get_comet_summary()` | `app.py` | Batch comet visibility (cached) |
| `get_asteroid_summary()` | `app.py` | Batch asteroid visibility (cached) |
| `get_dso_summary()` | `app.py` | Batch DSO visibility (cached, no API) |
| `get_planet_summary()` | `app.py` | Batch planet visibility |
| `generate_plan_pdf()` | `app.py` | Render night plan as downloadable PDF |
| `_render_night_plan_builder()` | `app.py` | Shared Night Plan Builder UI (all sections) |
| `_dso_table_and_image()` | `app.py` | `@st.fragment` — DSO table + click-to-reveal image card (fragment = row click skips full app rerun) |
| `_df_to_cosmic_xlsx()` | `app.py` | Cosmic XLSX export; Name cells use `=HYPERLINK()` formula for `unistellar://` deep links |
| `load_comet_catalog()` | `app.py` | Load comets_catalog.json |
| `load_comets_config()` | `app.py` | Load + parse comets.yaml |
| `save_comets_config()` | `app.py` | Save comets.yaml + GitHub push |
| `_send_github_notification()` | `app.py` | Create GitHub Issue (admin alerts); delegates to `backend/github.py` |
| `create_issue()` | `backend/github.py` | Pure GitHub Issue creation (takes token/repo as params, no Streamlit) |
| `read_comets_config()` | `backend/config.py` | Load comets.yaml → dict (pure, no cache) |
| `read_comet_catalog()` | `backend/config.py` | Load comets_catalog.json → (updated, entries) |
| `read_asteroids_config()` | `backend/config.py` | Load asteroids.yaml → dict (pure, no cache) |
| `read_dso_config()` | `backend/config.py` | Load dso_targets.yaml → dict (pure, no cache) |
| `render_dso_section()` | `app.py` | DSO section render (Stars/Galaxies/Nebulae) |
| `render_planet_section()` | `app.py` | Planet section render |
| `render_comet_section()` | `app.py` | Comet section render (My List + Explore Catalog) |
| `render_asteroid_section()` | `app.py` | Asteroid section render |
| `render_cosmic_section()` | `app.py` | Cosmic Cataclysm section render |
| `scrape_unistellar_table()` | `backend/scrape.py` | Scrape Cosmic Cataclysm alerts (Scrapling) |
| `scrape_unistellar_priority_comets()` | `backend/scrape.py` | Scrape comet missions page (Scrapling) |
| `scrape_unistellar_priority_asteroids()` | `backend/scrape.py` | Scrape planetary defense page (Scrapling) |
| `_deep_text()` | `backend/scrape.py` | Get all descendant text from Scrapling element |
| `_fetch_page()` | `backend/scrape.py` | Thread-safe StealthyFetcher wrapper (Streamlit + Windows compat) |
| `_ensure_browser()` | `backend/scrape.py` | Auto-install Patchright Chromium (idempotent, once per session) |
| `check_unistellar_priorities.main()` | `scripts/check_unistellar_priorities.py` | Scrape + diff priorities, write `_priority_changes.json` |
| `open_priority_issues.main()` | `scripts/open_priority_issues.py` | Create GitHub Issues for priority changes |
