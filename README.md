# 🔭 Astro Coordinates Planner

**Live App:** [https://astro-coordinates.streamlit.app/](https://astro-coordinates.streamlit.app/)

## Overview
The **Astro Coordinates Planner** is a web application designed for astrophotographers and astronomers. It helps you determine **if** and **when** a specific celestial object will be visible from your location tonight.

Instead of guessing, you can calculate the exact **Altitude** (height above horizon) and **Azimuth** (compass direction) of stars, comets, asteroids, or transient events over a specific time window.

## Key Features
*   **Precise Location & Time:** Automatically detects timezones based on your latitude/longitude.
*   **Deep Sky Resolver (SIMBAD):** Instantly find coordinates for millions of stars, galaxies, and nebulae.
*   **Solar System Objects (JPL Horizons):** Accurate ephemerides for planets, comets, and asteroids.
*   **Comet Tracking:** Batch visibility for all tracked comets with Observable/Unobservable tabs, Gantt timeline, and ⭐ Priority highlighting sourced from the Unistellar Citizen Science missions page (checked daily). Includes user add-requests (JPL-verified) and an admin approval panel that syncs to GitHub.
*   **Asteroid Tracking:** Same batch visibility system as comets with Unistellar Planetary Defense priority targets, observation windows for close-approach events (e.g. Apophis 2029), and smart JPL ID resolution for both numbered and provisional designations.
*   **Cosmic Cataclysms:** Live scraping of transient events (novae, supernovae) from Unistellar alerts. Includes a reporting system to filter out invalid/cancelled events or suggest target priorities.
*   **Observational Filters:** Filter targets based on Altitude (Min/Max), Azimuth, and Moon Separation.
*   **Moon Interference:** Automatically calculates Moon phase, separation, and assigns status (Safe/Caution/Avoid) to targets.
*   **Visibility Charts:** Gantt-style timeline chart (rise → set window per object) + Altitude vs Time trajectory chart for every target mode.
*   **Data Export:** Download trajectory data as CSV for use in telescope mount software.

## Installation

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **System Requirements (for Scraper):**
    Ensure Chrome/Chromium is installed if running locally.
    *   *Linux/Docker:* `apt-get install chromium chromium-driver`

## How to Use

### 1. Run the App
    ```bash
    streamlit run app.py
    ```

### 2. Set Location, Time & Filters (Sidebar)
*   **Location:** Search for a city, use Browser GPS, or enter coordinates manually.
*   **Time:** Set your observation start date and time.
*   **Duration:** Choose how long you plan to image.
*   **Filters:** Set Altitude (Min/Max), Azimuth, and Moon Separation limits to match your viewing site and conditions.

### 3. Choose a Target
Select one of the six modes:
*   **🌌 Star/Galaxy/Nebula:** Enter a name (e.g., `M42`, `Vega`).
*   **🪐 Planet:** View all planets at once — Observable/Unobservable tabs with Gantt timeline, or select one for a full trajectory.
*   **☄️ Comet:** Batch visibility for all tracked comets. Priority targets from Unistellar missions page are highlighted. Select any comet for a full trajectory + visibility window chart.
*   **🪨 Asteroid:** Batch visibility for all tracked asteroids. Priority targets from Unistellar Planetary Defense highlighted, with observation windows for close-approach events. Select any asteroid for a full trajectory.
*   **💥 Cosmic Cataclysm:** Scrape live alerts for transient events. Use the "Report" feature to flag invalid/cancelled targets or suggest priorities.
*   **✍️ Manual:** Enter RA/Dec directly.

### 4. Calculate & Analyze
*   Click **🚀 Calculate Visibility**.
*   View the **Altitude Chart** to see if the object is high enough.
*   **Download CSV** for detailed minute-by-minute data.

## Project Structure
*   `app.py`: Main Streamlit web application.
*   `targets.yaml`: Cosmic Cataclysm event priorities, blocklist, and too-faint list.
*   `comets.yaml`: Comet list, Unistellar priority targets, admin overrides, and cancelled list.
*   `asteroids.yaml`: Asteroid list, Unistellar Planetary Defense priority targets (with optional observation windows), admin overrides, and cancelled list.
*   `backend/scrape.py`: Selenium scrapers for Unistellar alerts, comet missions page, and asteroid planetary defense page.
*   `backend/core.py`: Trajectory calculation logic.
*   `backend/resolvers.py`: Interfaces for SIMBAD and JPL Horizons.
*   `Dockerfile`: Configuration for containerized deployment.