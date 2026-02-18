# Future Updates & Roadmap

## 1. Visualization Graph (Rise/Transit/Set)
*   **Goal:** Display a visual timeline of Rise, Transit, and Set times for all visible targets.
*   **Library:** Altair (or potentially Plotly/Matplotlib if Altair proves difficult with Streamlit containers).
*   **Key Requirements:**
    *   Plot three points per target: Rise (Blue), Transit (Orange), Set (Red).
    *   Y-axis: Target Names.
    *   X-axis: Local Time.
    *   **Sorting:** Allow sorting targets by Set Time (ascending) to prioritize early setters.
    *   **Scrollable:** The graph must handle 50+ targets without squishing; use a dynamic height or scrollable container.
*   **Technical Challenges to Solve:**
    *   **Timezones:** Altair often struggles with timezone-aware datetimes. Ensure all data is converted to naive local datetime before plotting.
    *   **Data Types:** Explicitly enforce `pd.to_datetime` on the dataframe columns before passing to the chart.
    *   **Container Interaction:** `st.container` with fixed height sometimes conflicts with Altair's interactive features.

## 2. Data Persistence & Export
*   **Google Sheets Integration:** Add a button to append the calculated trajectory or planning list to a Google Sheet for field use.
*   **Calendar Export:** Generate an `.ics` file for the observation session.

## 3. Backend Improvements
*   **Unit Tests:** Add `pytest` coverage for `backend/core.py` and `backend/resolvers.py`.
*   **Caching:** Implement robust caching (Redis or local file) for SIMBAD/JPL queries to reduce API latency.
*   **Error Handling:** Better feedback when JPL Horizons is down or returns ambiguous results.

## 4. UI Enhancements
*   **Constellation Filter:** Allow filtering the "Cosmic Cataclysm" table by Constellation.
*   **Mobile View:** Optimize the table columns for mobile screens (hide RA/Dec, show only Name/Mag/Alt).
*   **Address Search:** Add a "Clear" button to the address search box.