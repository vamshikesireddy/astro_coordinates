import streamlit as st
import pandas as pd
import geocoder
import pytz
from datetime import datetime
from timezonefinder import TimezoneFinder
from astropy.coordinates import EarthLocation, SkyCoord, FK5
from astropy import units as u
from astropy.time import Time

try:
    from streamlit_js_eval import get_geolocation
except ImportError:
    get_geolocation = None

# Import from local modules
from resolvers import resolve_simbad, resolve_horizons
from core import compute_trajectory
from scrape import scrape_unistellar_table

st.set_page_config(page_title="Astro Coordinates", page_icon="🔭", layout="wide")

st.title("🔭 Astro Coordinates Planner")
st.markdown("Plan your astrophotography sessions with visibility predictions.")

# ---------------------------
# SIDEBAR: Location & Time
# ---------------------------
st.sidebar.header("📍 Location & Time")

# 1. Location
# Initialize session state with empty location
if 'lat' not in st.session_state:
    st.session_state.lat = None
if 'lon' not in st.session_state:
    st.session_state.lon = None

def search_address():
    if st.session_state.addr_search:
        try:
            g = geocoder.osm(st.session_state.addr_search)
            if g.ok:
                st.session_state.lat = g.latlng[0]
                st.session_state.lon = g.latlng[1]
        except:
            pass

if get_geolocation:
    if st.sidebar.checkbox("📍 Use Browser GPS"):
        loc = get_geolocation()
        if loc:
            st.session_state.lat = loc['coords']['latitude']
            st.session_state.lon = loc['coords']['longitude']
else:
    st.sidebar.info("Install `streamlit-js-eval` for GPS support.")

st.sidebar.text_input("Search Address", key="addr_search", on_change=search_address, help="Enter city or address to update coordinates")

lat = st.sidebar.number_input("Latitude", key="lat", format="%.4f")
lon = st.sidebar.number_input("Longitude", key="lon", format="%.4f")

# 2. Timezone
tf = TimezoneFinder()
timezone_str = "UTC"
try:
    if lat is not None and lon is not None:
        timezone_str = tf.timezone_at(lat=lat, lng=lon) or "UTC"
except:
    pass
st.sidebar.caption(f"Timezone: {timezone_str}")
local_tz = pytz.timezone(timezone_str)

# 3. Date & Time
st.sidebar.subheader("🕒 Observation Start")
now = datetime.now(local_tz)

# Initialize session state for date and time
if 'selected_date' not in st.session_state:
    st.session_state['selected_date'] = now.date()
if 'selected_time' not in st.session_state:
    st.session_state['selected_time'] = now.time()

def update_date():
    st.session_state.selected_date = st.session_state._new_date
def update_time():
    st.session_state.selected_time = st.session_state._new_time

selected_date = st.sidebar.date_input("Date", value=st.session_state.selected_date, key='_new_date', on_change=update_date)
selected_time = st.sidebar.time_input("Time", value=st.session_state.selected_time, key='_new_time', on_change=update_time)

# Combine to timezone-aware datetime
start_time = datetime.combine(st.session_state.selected_date, st.session_state.selected_time)
start_time = local_tz.localize(start_time)

# 4. Duration
st.sidebar.subheader("⏳ Duration")
duration_options = [60, 120, 180, 240, 300, 360]
duration = st.sidebar.selectbox("Minutes", options=duration_options, index=3) # Default 240

# ---------------------------
# MAIN: Target Selection
# ---------------------------
st.header("1. Choose Target")

target_mode = st.radio(
    "Select Object Type:",
    ["Star/Galaxy/Nebula (SIMBAD)", "Comet/Asteroid (JPL Horizons)", "Cosmic Cataclysm", "Manual RA/Dec"],
    horizontal=True
)

name = "Unknown"
sky_coord = None
resolved = False


if target_mode == "Star/Galaxy/Nebula (SIMBAD)":
    obj_name = st.text_input("Enter Object Name (e.g., M31, Vega, Pleiades)", value="M42")
    if obj_name:
        try:
            with st.spinner(f"Resolving {obj_name}..."):
                name, sky_coord = resolve_simbad(obj_name)
            st.success(f"✅ Resolved: **{name}** (RA: {sky_coord.ra.to_string(unit=u.hour, sep=':', precision=1)}, Dec: {sky_coord.dec.to_string(sep=':', precision=1)})")
            resolved = True
        except Exception as e:
            st.error(f"Could not resolve object: {e}")

elif target_mode == "Comet/Asteroid (JPL Horizons)":
    obj_name = st.text_input("Enter Object Name (e.g., 1P/Halley, Ceres)", value="C/2023 A3")
    if obj_name:
        try:
            with st.spinner(f"Querying JPL Horizons for {obj_name}..."):
                # Pass UTC time for ephemeris lookup
                utc_start = start_time.astimezone(pytz.utc)
                name, sky_coord = resolve_horizons(obj_name, obs_time_str=utc_start.isoformat())
            st.success(f"✅ Resolved: **{name}**")
            resolved = True
        except Exception as e:
            st.error(f"Could not resolve object: {e}")

elif target_mode == "Cosmic Cataclysm":
    st.info("Fetching latest alerts from Unistellar (via Selenium scrape)...")
    
    @st.cache_data(ttl=3600, show_spinner="Scraping data...")
    def get_scraped_data():
        return scrape_unistellar_table()

    df_alerts = get_scraped_data()
    
    if df_alerts is not None and not df_alerts.empty:
        # Try to identify columns dynamically
        df_alerts.columns = df_alerts.columns.str.strip()
        cols = df_alerts.columns.tolist()
        
        # Look for 'Name' (preferred) or 'Target'
        target_col = next((c for c in cols if c.lower() in ['name', 'target', 'object']), None)
        ra_col = next((c for c in cols if c.lower() in ['ra', 'r.a.']), None)
        dec_col = next((c for c in cols if c.lower() in ['dec', 'declination']), None)
        
        if target_col:
            targets = df_alerts[target_col].unique()
            obj_name = st.selectbox("Select Target", targets)
            
            if obj_name:
                row = df_alerts[df_alerts[target_col] == obj_name].iloc[0]
                name = obj_name
                
                if ra_col and dec_col:
                    ra_val = row[ra_col]
                    dec_val = row[dec_col]
                    st.caption(f"Coordinates: RA {ra_val}, Dec {dec_val}")
                    
                    try:
                        # Handle potential string formatting issues
                        sky_coord = SkyCoord(str(ra_val), str(dec_val), frame='icrs')
                        resolved = True
                        st.success(f"✅ Resolved: **{name}**")
                    except Exception as e:
                        st.error(f"Error parsing coordinates: {e}")
            
            # Display data with shortened links
            st.subheader("Available Targets")
            display_df = df_alerts.copy()
            link_col = next((c for c in display_df.columns if 'link' in c.lower()), None)
            if link_col:
                display_df[link_col] = display_df[link_col].apply(
                    lambda x: "unistellar://..." if isinstance(x, str) and x.startswith("unistellar://") else x
                )
            st.dataframe(display_df)
        else:
            st.error(f"Could not find 'Name' column. Found: {cols}")
            st.dataframe(df_alerts)
    else:
        st.error("Failed to scrape data. Please check the scraper logs.")

elif target_mode == "Manual RA/Dec":
    col1, col2, col3 = st.columns(3)
    with col1:
        name = st.text_input("Object Name (optional)", value="Custom Target", help="Provide a name for your custom target.")
    with col2:
        ra_input = st.text_input("RA (e.g., 15h59m30s)", value="15h59m30s")
    with col3:
        dec_input = st.text_input("Dec (e.g., 25d55m13s)", value="25d55m13s")
    
    if ra_input and dec_input:
        try:
            sky_coord = SkyCoord(ra_input, dec_input, frame=FK5, unit=(u.hourangle, u.deg))
            st.success(f"✅ Coordinates parsed successfully.")
            resolved = True
        except Exception as e:
            st.error(f"Invalid coordinates format: {e}")

# ---------------------------
# MAIN: Calculation & Output
# ---------------------------
st.header("2. Trajectory Results")

if st.button("🚀 Calculate Visibility", type="primary", disabled=not resolved):
    if lat is None or lon is None:
        st.error("Please enter a valid location (Latitude & Longitude) in the sidebar.")
        st.stop()

    location = EarthLocation(lat=lat*u.deg, lon=lon*u.deg)
    
    with st.spinner("Calculating trajectory..."):
        results = compute_trajectory(sky_coord, location, start_time, duration_minutes=duration)
    
    df = pd.DataFrame(results)
    
    # Metrics
    max_alt = df["Altitude (°)"].max()
    best_time = df.loc[df["Altitude (°)"].idxmax()]["Local Time"]
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Max Altitude", f"{max_alt}°")
    m2.metric("Best Time", best_time.split(" ")[1])
    m3.metric("Direction at Max", df.loc[df["Altitude (°)"].idxmax()]["Direction"])

    # Chart
    st.subheader("Altitude vs Time")
    # Create a simple line chart
    chart_data = df[["Local Time", "Altitude (°)"]].copy()
    chart_data["Local Time"] = pd.to_datetime(chart_data["Local Time"])
    st.line_chart(chart_data.set_index("Local Time"))

    # Data Table
    st.subheader("Detailed Data")
    st.dataframe(df, width='stretch')

    # Sanitize filename
    safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
    date_str = start_time.strftime('%Y-%m-%d')

    st.download_button(
        label="Download CSV",
        data=df.to_csv(index=False).encode('utf-8'),
        file_name=f"{safe_name}_{date_str}_trajectory.csv",
        mime="text/csv",
    )