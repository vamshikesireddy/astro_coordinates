import streamlit as st
import pandas as pd
import geocoder
import pytz
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from timezonefinder import TimezoneFinder
from astropy.coordinates import EarthLocation, SkyCoord, FK5
from astropy import units as u
from astropy.time import Time

# Import from local modules
from resolvers import resolve_simbad, resolve_horizons
from core import compute_trajectory

st.set_page_config(page_title="Astro Coordinates", page_icon="🔭", layout="wide")

st.title("🔭 Astro Coordinates Planner")
st.markdown("Plan your astrophotography sessions with visibility predictions.")

# ---------------------------
# SIDEBAR: Location & Time
# ---------------------------
st.sidebar.header("📍 Location & Time")

# 1. Location
@st.cache_data
def get_default_location():
    try:
        g = geocoder.ip('me')
        if g.latlng:
            return g.latlng
    except:
        pass
    return [40.7128, -74.0060] # Default to NYC if IP fails

default_lat, default_lon = get_default_location()

use_manual_loc = st.sidebar.checkbox("📍 Enter Address/Coordinates manually", value=False)

if use_manual_loc:
    address = st.sidebar.text_input("Search Address (e.g., 'Central Park, NY')")
    if address:
        try:
            g = geocoder.osm(address)
            if g.ok:
                default_lat, default_lon = g.latlng
                st.sidebar.success(f"Found: {g.address}")
            else:
                st.sidebar.error("Address not found.")
        except:
            st.sidebar.error("Geocoding service unavailable.")
    
    lat = st.sidebar.number_input("Latitude", value=float(default_lat), format="%.4f")
    lon = st.sidebar.number_input("Longitude", value=float(default_lon), format="%.4f")
else:
    lat = default_lat
    lon = default_lon
    st.sidebar.info(f"Using detected location: {lat:.4f}, {lon:.4f}")

# 2. Timezone
tf = TimezoneFinder()
try:
    timezone_str = tf.timezone_at(lat=lat, lng=lon) or "UTC"
except:
    timezone_str = "UTC"
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
    ["Star/Galaxy/Nebula (SIMBAD)", "Comet/Asteroid (JPL Horizons)", "Manual RA/Dec"],
    horizontal=True
)

name = "Unknown"
sky_coord = None
resolved = False


@st.cache_data(ttl=3600)
def get_unistellar_data():
    alert_page_url = "https://alerts.unistellaroptics.com/transient/events.html"
    try:
        # Fetch the main page
        response = requests.get(alert_page_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        response.raise_for_status()
        
        # Parse the HTML to find the iframe URL
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Find the h3 tag with the specific text
        h3_tag = soup.find('h3', string='Cosmic Alert Targets')
        
        if not h3_tag:
            st.error("Could not find the 'Cosmic Alert Targets' section.")
            return None
            
        # Find the next iframe after the h3 tag
        iframe = h3_tag.find_next('iframe')
        
        if not iframe or not iframe.has_attr('src') or 'docs.google.com/spreadsheets' not in iframe['src']:
            st.error("Could not find the embedded Google Sheet with event data after the 'Cosmic Alert Targets' section.")
            return None
            
        # Modify the URL to get the CSV export link
        sheet_url = iframe['src']
        # Replace /pubhtml with /export?format=csv
        csv_url = sheet_url.replace("/pubhtml", "/export?format=csv")

        # Fetch the CSV data
        df = pd.read_csv(csv_url)
        return df

    except Exception as e:
        st.error(f"Error fetching or parsing Unistellar data: {e}")
        return None

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

    st.download_button(
        label="Download CSV",
        data=df.to_csv(index=False).encode('utf-8'),
        file_name=f"{name}_trajectory.csv",
        mime="text/csv",
    )