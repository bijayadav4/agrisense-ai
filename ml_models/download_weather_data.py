"""
AgriSense AI - Weather Time-Series Dataset Collector
=====================================================
Downloads multi-year daily meteorological time series across diverse Indian agricultural
zones from Open-Meteo's free Historical Archive API (2021 to 2024).
Includes robust offline synthetic fallback if network/API is unavailable.

Target Features:
- temp_max (°C)
- temp_min (°C)
- humidity (%)
- precipitation (mm)
- wind_speed (km/h)
"""

import os
import time
import math
import numpy as np
import pandas as pd
import requests

from config import BASE_DIR

OUTPUT_CSV_PATH = os.path.join(BASE_DIR, "datasets", "weather_timeseries.csv")

AGRO_STATIONS = [
    {"name": "Pune", "state": "Maharashtra", "lat": 18.5204, "lon": 73.8567},
    {"name": "Coimbatore", "state": "Tamil Nadu", "lat": 11.0055, "lon": 76.9661},
    {"name": "Ludhiana", "state": "Punjab", "lat": 30.9120, "lon": 75.8538},
    {"name": "Karnal", "state": "Haryana", "lat": 29.6920, "lon": 76.9845},
    {"name": "Patna", "state": "Bihar", "lat": 25.5941, "lon": 85.1356},
    {"name": "Hyderabad", "state": "Telangana", "lat": 17.3850, "lon": 78.4867},
    {"name": "Nagpur", "state": "Maharashtra", "lat": 21.1463, "lon": 79.0849},
    {"name": "Jaipur", "state": "Rajasthan", "lat": 26.9196, "lon": 75.7878},
]


def fetch_station_archive(lat, lon, start_date="2021-01-01", end_date="2024-12-31"):
    url = (
        f"https://archive-api.open-meteo.com/v1/archive?"
        f"latitude={lat}&longitude={lon}&"
        f"start_date={start_date}&end_date={end_date}&"
        f"daily=temperature_2m_max,temperature_2m_min,relative_humidity_2m_mean,precipitation_sum,wind_speed_10m_max&"
        f"timezone=Asia/Kolkata"
    )
    resp = requests.get(url, timeout=12)
    if resp.status_code == 200:
        data = resp.json()
        daily = data.get("daily", {})
        times = daily.get("time", [])
        if not times:
            return None
        df = pd.DataFrame({
            "date": times,
            "temp_max": daily.get("temperature_2m_max"),
            "temp_min": daily.get("temperature_2m_min"),
            "humidity": daily.get("relative_humidity_2m_mean"),
            "precipitation": daily.get("precipitation_sum"),
            "wind_speed": daily.get("wind_speed_10m_max"),
        })
        return df
    return None


def generate_synthetic_station_data(station, start_date="2021-01-01", end_date="2024-12-31"):
    """
    Physically grounded agro-climatic simulation of Indian monsoon and winter cycles
    for offline / isolated development setups.
    """
    dates = pd.date_range(start=start_date, end=end_date, freq="D")
    np.random.seed(int(station["lat"] * 100))
    n = len(dates)

    day_of_year = dates.dayofyear.values
    # Base temperature wave (summer peak day ~135, winter trough day ~15)
    t_mean_base = 27.0 - (station["lat"] - 18.0) * 0.4
    t_amp = 8.0 + (station["lat"] - 15.0) * 0.3
    temp_mid = t_mean_base + t_amp * np.sin(2 * np.pi * (day_of_year - 100) / 365.25)
    
    diurnal_diff = 10.0 + np.random.normal(0, 1.5, n)
    temp_max = temp_mid + diurnal_diff / 2.0 + np.random.normal(0, 1.2, n)
    temp_min = temp_mid - diurnal_diff / 2.0 + np.random.normal(0, 1.2, n)

    # Monsoon rainfall & humidity spike (Days 160 to 270)
    monsoon_envelope = np.exp(-((day_of_year - 215) ** 2) / (2 * 40 ** 2))
    humidity = 45.0 + 38.0 * monsoon_envelope + np.random.normal(0, 5.0, n)
    humidity = np.clip(humidity, 20.0, 95.0)

    # Rainfall occurrences with Pareto / Gamma distributions during monsoon
    rain_prob = 0.05 + 0.55 * monsoon_envelope
    rain_days = np.random.rand(n) < rain_prob
    precipitation = np.zeros(n)
    precipitation[rain_days] = np.random.gamma(shape=1.5, scale=8.0, size=rain_days.sum())
    precipitation = np.round(np.clip(precipitation, 0.0, 150.0), 1)

    wind_speed = 8.0 + 6.0 * monsoon_envelope + np.random.normal(0, 2.5, n)
    wind_speed = np.round(np.clip(wind_speed, 2.0, 45.0), 1)

    df = pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "temp_max": np.round(temp_max, 1),
        "temp_min": np.round(temp_min, 1),
        "humidity": np.round(humidity, 1),
        "precipitation": precipitation,
        "wind_speed": wind_speed,
    })
    return df


def collect_dataset():
    os.makedirs(os.path.dirname(OUTPUT_CSV_PATH), exist_ok=True)
    all_dfs = []
    print(f"📥 Fetching / Generating Weather Time-Series for {len(AGRO_STATIONS)} Agro Stations...")

    for st in AGRO_STATIONS:
        print(f"  -> Station: {st['name']}, {st['state']} (Lat: {st['lat']}, Lon: {st['lon']})")
        df = None
        try:
            df = fetch_station_archive(st["lat"], st["lon"])
            if df is not None:
                print(f"     ✅ Downloaded {len(df)} live historical records from Open-Meteo Archive.")
        except Exception as e:
            print(f"     ⚠️ API request failed: {e}. Switching to agro-climatic simulation.")

        if df is None or len(df) == 0:
            df = generate_synthetic_station_data(st)
            print(f"     ✨ Generated {len(df)} synthetic meteorological records.")

        df["station"] = st["name"]
        df["state"] = st["state"]
        df["latitude"] = st["lat"]
        df["longitude"] = st["lon"]
        all_dfs.append(df)
        time.sleep(0.3)

    final_df = pd.concat(all_dfs, ignore_index=True)
    # Clean NaN values if any
    final_df["humidity"] = final_df["humidity"].fillna(final_df["humidity"].median())
    final_df["precipitation"] = final_df["precipitation"].fillna(0.0)
    final_df["wind_speed"] = final_df["wind_speed"].fillna(final_df["wind_speed"].median())
    final_df["temp_max"] = final_df["temp_max"].fillna(final_df["temp_max"].median())
    final_df["temp_min"] = final_df["temp_min"].fillna(final_df["temp_min"].median())

    final_df.to_csv(OUTPUT_CSV_PATH, index=False)
    print(f"\n✅ Weather time series dataset successfully created: {OUTPUT_CSV_PATH}")
    print(f"   Total rows: {len(final_df)} | Columns: {list(final_df.columns)}")
    print(final_df.head(3))


if __name__ == "__main__":
    collect_dataset()
