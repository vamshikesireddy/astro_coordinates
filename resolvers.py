from astropy.coordinates import SkyCoord, FK5
from astropy import units as u
from astropy.time import Time
from astroquery.simbad import Simbad
from astroquery.jplhorizons import Horizons

def resolve_simbad(obj_name):
    """Resolves an object name using SIMBAD."""
    try:
        # Get ICRS coordinates from SIMBAD
        icrs_coord = SkyCoord.from_name(obj_name)
        
        # Transform to FK5 with current epoch
        t = Time.now()
        fk5_coord = icrs_coord.transform_to(FK5(equinox=t))
        
        custom_simbad = Simbad()
        custom_simbad.TIMEOUT = 10
        result_table = custom_simbad.query_object(obj_name)

        resolved_name = obj_name
        if result_table is not None and 'MAIN_ID' in result_table.colnames:
            main_id = result_table['MAIN_ID'][0]
            resolved_name = main_id.decode('utf-8') if isinstance(main_id, bytes) else str(main_id)
        
        return resolved_name, fk5_coord
    except Exception as e:
        raise RuntimeError(f"SIMBAD lookup failed for {obj_name}: {e}")

def resolve_horizons(obj_name, obs_time_str="2026-02-13 00:30:00", location_code='500'):
    """Resolves a solar system body using JPL Horizons."""
    try:
        obs_time = Time(obs_time_str)
        try:
            obj = Horizons(id=obj_name, location=location_code, epochs=obs_time.jd, id_type='smallbody')
            result = obj.ephemerides()
        except Exception:
            # Fallback: try without id_type (allows search strings like "4 Vesta")
            obj = Horizons(id=obj_name, location=location_code, epochs=obs_time.jd)
            result = obj.ephemerides()

        ra = result['RA'][0] * u.deg
        dec = result['DEC'][0] * u.deg
        sky_coord = SkyCoord(ra=ra, dec=dec, frame='icrs')
        
        return obj_name, sky_coord
    except Exception as e:
        raise RuntimeError(f"JPL Horizons lookup failed for {obj_name}: {e}")