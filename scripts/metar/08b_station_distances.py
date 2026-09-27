"""
Step 8b · METAR · Distance from each airport to its city hall (read-only).
Great-circle (haversine) distance, straight line. Changes no data.
Airport coordinates: transcribed by Claude from each station's IEM page
  https://mesonet.agron.iastate.edu/sites/site.php?station=<ID>&network=<NET>
City hall coordinates: supplied by Claude (approx. one block); verify in Google Maps.
In-city-limits notes: from the handoff doc only; otherwise "not checked".

Run from the repo root:  python3 scripts/metar/08b_station_distances.py
"""
import math
import pandas as pd

OUT = "data/processed/metar/metar_station_distances.csv"

AIRPORTS = [  # city, station, network, IEM name, lat, lon, in-city note (from handoff)
    ("bakersfield",  "BFL",  "CA_ASOS", "BAKERSFIELD/MEADOWS",      35.43440, -119.05420, "not checked"),
    ("fresno",       "FAT",  "CA_ASOS", "FRESNO AIR TERMINAL",      36.78000, -119.71940, "not checked"),
    ("losangeles",   "LAX",  "CA_ASOS", "LOS ANGELES INTL",         33.93816, -118.38653, "in city limits (handoff)"),
    ("sanfrancisco", "SFO",  "CA_ASOS", "SAN FRANCISCO INTL",       37.61897, -122.37489, "just south of city limits (handoff)"),
    ("eugene",       "EUG",  "OR_ASOS", "EUGENE/MAHLON SWEET",      44.12458, -123.21197, "not checked"),
    ("fairbanks",    "PAFA", "AK_ASOS", "FAIRBANKS INTL ARPT (ASOS)", 64.80389, -147.87611, "not checked"),
    ("brownsville",  "BRO",  "TX_ASOS", "BROWNSVILLE INTL",         25.91461,  -97.42313, "not checked"),
    ("detroit",      "DET",  "MI_ASOS", "DETROIT/CITY AIR",         42.40919,  -83.00986, "in city (handoff)"),
    ("detroit",      "DTW",  "MI_ASOS", "DETROIT/WAYNE",            42.23000,  -83.33000, "outside, Romulus (handoff)"),
    ("pittsburgh",   "AGC",  "PA_ASOS", "PITTSBURGH/ALLEGHEN",      40.35472,  -79.92167, "next to the city (handoff)"),
    ("pittsburgh",   "PIT",  "PA_ASOS", "PITTSBURGH INTL",          40.49147,  -80.23286, "outside (handoff)"),
    ("boston",       "BOS",  "MA_ASOS", "BOSTON/LOGAN INTL",        42.36057,  -71.00973, "not checked"),
]

CITY_HALLS = {  # city: (address, lat, lon)  -- Claude-supplied, verify
    "bakersfield":  ("1600 Truxtun Ave, Bakersfield CA",           35.3752, -119.0209),
    "fresno":       ("2600 Fresno St, Fresno CA",                  36.7375, -119.7867),
    "losangeles":   ("200 N Spring St, Los Angeles CA",            34.0537, -118.2428),
    "sanfrancisco": ("1 Dr Carlton B Goodlett Pl, San Francisco CA", 37.7793, -122.4192),
    "eugene":       ("101 W 10th Ave, Eugene OR",                  44.0497, -123.0930),
    "fairbanks":    ("800 Cushman St, Fairbanks AK",               64.8355, -147.7164),
    "brownsville":  ("1001 E Elizabeth St, Brownsville TX",        25.9016,  -97.4958),
    "detroit":      ("2 Woodward Ave, Detroit MI",                 42.3294,  -83.0445),
    "pittsburgh":   ("414 Grant St, Pittsburgh PA",                40.4383,  -79.9967),
    "boston":       ("1 City Hall Square, Boston MA",              42.3603,  -71.0580),
}

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0088  # mean Earth radius, km
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi, dlmb = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))

rows = []
for city, stn, net, name, lat, lon, note in AIRPORTS:
    addr, clat, clon = CITY_HALLS[city]
    km = haversine_km(lat, lon, clat, clon)
    rows.append({"city": city, "station": stn, "iem_network": net, "iem_name": name,
                 "station_lat": lat, "station_lon": lon,
                 "city_hall": addr, "city_hall_lat": clat, "city_hall_lon": clon,
                 "distance_km": round(km, 1), "distance_mi": round(km / 1.609344, 1),
                 "in_city_limits_note": note})

df = pd.DataFrame(rows)
df.to_csv(OUT, index=False)
print(df[["city", "station", "distance_mi", "distance_km", "in_city_limits_note"]].to_string(index=False))
