from astropy.coordinates import EarthLocation, AltAz, SkyCoord, FK5
from astropy.time import Time
from astropy import units as u
from datetime import datetime, timedelta
import pytz
import geocoder
import pandas as pd
from timezonefinder import TimezoneFinder
from astroquery.simbad import Simbad
from astroquery.jplhorizons import Horizons

# ----------------------------
# MODE SELECTION
# ----------------------------
print("Choose mode:")
print("1 - Manual RA/Dec Input")
print("2 - Lookup (Star, Galaxy, Planet via SIMBAD/CDS)")
print("3 - Comet or Asteroid via JPL Horizons")
mode = input("Enter option 1, 2, or 3: ").strip()

if mode == "1":
    from astro_coordinates.coordinates import user_ra, user_dec, name
    sky_coord = SkyCoord(user_ra, user_dec, frame=FK5, unit=(u.hourangle, u.deg), equinox=Time.now())
    user_ra = sky_coord.ra
    user_dec = sky_coord.dec

elif mode == "2":
    obj_name = input("Enter object name (e.g., Vega, M31, Mars): ").strip()
    try:
        sky_coord = SkyCoord.from_name(obj_name)
        user_ra = sky_coord.ra
        user_dec = sky_coord.dec

        custom_simbad = Simbad()
        custom_simbad.TIMEOUT = 10
        result_table = custom_simbad.query_object(obj_name)

        if result_table is not None and 'MAIN_ID' in result_table.colnames:
            main_id = result_table['MAIN_ID'][0]
            resolved_name = main_id.decode('utf-8') if isinstance(main_id, bytes) else str(main_id)
        else:
            resolved_name = obj_name
            print(f"⚠️ SIMBAD returned no MAIN_ID. Using input name: {obj_name}")

        name = resolved_name
        print(f"Resolved object: {name} at RA: {user_ra}, Dec: {user_dec}")

    except Exception as e:
        print(f"❌ SIMBAD/CDS lookup failed: {e}")
        exit(1)

elif mode == "3":
    obj_name = input("Enter comet or asteroid name (e.g., 1P/Halley, 29P/Schwassmann-Wachmann 1): ").strip()
    try:
        print(f"🔭 Using JPL Horizons to resolve '{obj_name}'...")
        obs_time = Time("2026-02-13 00:30:00")  # UTC
        location_code = '500'  # Geocentric

        obj = Horizons(id=obj_name, location=location_code, epochs=obs_time.jd, id_type='smallbody')
        result = obj.ephemerides()

        ra = result['RA'][0] * u.deg
        dec = result['DEC'][0] * u.deg
        sky_coord = SkyCoord(ra=ra, dec=dec, frame='icrs')
        user_ra = sky_coord.ra
        user_dec = sky_coord.dec
        name = obj_name

        print(f"Resolved {obj_name} at RA: {user_ra}, Dec: {user_dec}")

    except Exception as e:
        print(f"❌ JPL Horizons lookup failed: {e}")
        exit(1)

else:
    print("❌ Invalid mode. Exiting.")
    exit(1)

# ----------------------------
# GET USER LOCATION
# ----------------------------
g = geocoder.ip('me')
lat, lon = g.latlng
print(f"Lat: {lat}, Lon: {lon}")

tf = TimezoneFinder()
local_tz = tf.timezone_at(lat=lat, lng=lon)
timezone = pytz.timezone(local_tz)
print(f"Timezone: {local_tz}")

# ----------------------------
# TIME WINDOW SETUP
# ----------------------------
start_local = timezone.localize(datetime(2026, 2, 13, 19, 0, 0))
time_steps = [start_local + timedelta(minutes=i) for i in range(0, 241, 10)]

location = EarthLocation(lat=lat*u.deg, lon=lon*u.deg)

# ----------------------------
# DIRECTION LABELING
# ----------------------------
def azimuth_to_compass(az):
    directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                  'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    ix = int((az + 11.25) / 22.5) % 16
    return directions[ix]

# ----------------------------
# COMPUTE POSITION DATA
# ----------------------------
results = []
for t in time_steps:
    t_utc = t.astimezone(pytz.utc)
    time_utc = Time(t_utc)
    altaz_frame = AltAz(obstime=time_utc, location=location)
    altaz = sky_coord.transform_to(altaz_frame)
    lst = time_utc.sidereal_time('apparent', longitude=location.lon)
    compass_dir = azimuth_to_compass(altaz.az.degree)

    results.append({
        "Local Time": t.strftime('%Y-%m-%d %H:%M:%S'),
        "UTC Time": t_utc.strftime('%Y-%m-%d %H:%M:%S'),
        "LST": lst.to_string(sep=':', precision=2),
        "Name": name,
        "RA (input)": user_ra.to_string(unit=u.hour, sep=':', precision=2),
        "Dec (input)": user_dec.to_string(sep=':', precision=2),
        "Azimuth (°)": round(altaz.az.degree, 2),
        "Altitude (°)": round(altaz.alt.degree, 2),
        "Direction": compass_dir
    })

# ----------------------------
# OUTPUT TABLE
# ----------------------------
df = pd.DataFrame(results)
print(df)
