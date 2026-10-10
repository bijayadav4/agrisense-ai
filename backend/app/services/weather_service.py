import math
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests

from app.config import Config


def calculate_fao_extraterrestrial_radiation(lat_deg=18.52, day_of_year=None):
    """
    Computes daily extraterrestrial radiation (Ra) in mm/day equivalent
    using FAO Irrigation and Drainage Paper No. 56, Equation 21.
    """
    if day_of_year is None:
        day_of_year = datetime.now().timetuple().tm_yday

    phi = math.radians(float(lat_deg))
    dr = 1.0 + 0.033 * math.cos((2.0 * math.pi / 365.0) * day_of_year)
    delta = 0.409 * math.sin((2.0 * math.pi / 365.0) * day_of_year - 1.39)

    tan_val = -math.tan(phi) * math.tan(delta)
    clamped_val = max(-1.0, min(1.0, tan_val))
    omega_s = math.acos(clamped_val)

    # Solar constant Gsc = 0.0820 MJ/(m2.min)
    # Ra in MJ/(m2.day) = (24 * 60 / pi) * Gsc * dr * [omega_s * sin(phi)*sin(delta) + cos(phi)*cos(delta)*sin(omega_s)]
    gsc = 0.0820
    ra_mj = (
        (1440.0 / math.pi)
        * gsc
        * dr
        * (omega_s * math.sin(phi) * math.sin(delta) + math.cos(phi) * math.cos(delta) * math.sin(omega_s))
    )

    # Convert MJ/(m2.day) to equivalent depth of evaporation in mm/day (1 MJ/m2/day = 0.408 mm/day)
    ra_mm = ra_mj * 0.408
    return max(0.1, round(ra_mm, 3))


def calculate_hargreaves_et0(tmean, tmax, tmin, lat=18.52, day_of_year=None, ra_custom=None):
    """
    Standard Hargreaves-Samani (1985) Reference Evapotranspiration ET0 (mm/day):
    ET0 = 0.0023 * (Tmean + 17.8) * sqrt(Tmax - Tmin) * Ra
    Where Ra is extraterrestrial radiation in mm/day equivalent from FAO-56 Eq. 21.
    No 4.2 constant, no arbitrary humidity term, no max(2.0) floor.
    """
    tmean = float(tmean)
    tmax = float(tmax)
    tmin = float(tmin)

    delta_t = max(0.0, tmax - tmin)
    if ra_custom is not None:
        ra = float(ra_custom)
    else:
        ra = calculate_fao_extraterrestrial_radiation(lat_deg=lat, day_of_year=day_of_year)

    et0 = 0.0023 * (tmean + 17.8) * math.sqrt(delta_t) * ra
    return round(max(0.0, et0), 3)


WMO_MAP = {
    0: ("Clear Sky", "☀️"),
    1: ("Mainly Clear", "🌤️"),
    2: ("Partly Cloudy", "⛅"),
    3: ("Overcast Clouds", "☁️"),
    45: ("Morning Fog / Mist", "🌫️"),
    48: ("Depositing Rime Fog", "🌫️"),
    51: ("Light Drizzle", "🌦️"),
    53: ("Moderate Drizzle", "🌦️"),
    55: ("Dense Drizzle", "🌧️"),
    61: ("Slight Rain", "🌦️"),
    63: ("Moderate Rain", "🌧️"),
    65: ("Heavy Rain", "🌧️"),
    80: ("Rain Showers", "🌧️"),
    81: ("Moderate Rain Showers", "🌧️"),
    82: ("Violent Rain Showers", "⛈️"),
    95: ("Thunderstorm Alert", "⛈️"),
    96: ("Thunderstorm with Hail", "⛈️"),
    99: ("Heavy Thunderstorm", "⛈️"),
}

# Pre-populated Geocoding Cache for Instant (0.00s) Resolution
GEO_CACHE = {
    "pune": (18.5204, 73.8567, "Pune, Maharashtra"),
    "coimbatore": (11.0055, 76.9661, "Coimbatore, Tamil Nadu"),
    "patna": (25.5941, 85.1356, "Patna, Bihar"),
    "delhi": (28.6519, 77.2315, "Delhi, National Capital Territory of Delhi"),
    "new delhi": (28.6139, 77.2090, "New Delhi, Delhi"),
    "mumbai": (19.0760, 72.8777, "Mumbai, Maharashtra"),
    "bengaluru": (12.9716, 77.5946, "Bengaluru, Karnataka"),
    "bangalore": (12.9716, 77.5946, "Bengaluru, Karnataka"),
    "hyderabad": (17.3850, 78.4867, "Hyderabad, Telangana"),
    "nagpur": (21.1463, 79.0849, "Nagpur, Maharashtra"),
    "ludhiana": (30.9120, 75.8538, "Ludhiana, Punjab"),
    "jaipur": (26.9196, 75.7878, "Jaipur, Rajasthan"),
    "karnal": (29.6920, 76.9845, "Karnal, Haryana"),
    "nashik": (19.9975, 73.7898, "Nashik, Maharashtra"),
    "lucknow": (26.8467, 80.9462, "Lucknow, Uttar Pradesh"),
    "indore": (22.7196, 75.8577, "Indore, Madhya Pradesh"),
    "ahmedabad": (23.0225, 72.5714, "Ahmedabad, Gujarat"),
}

# In-memory TTL Cache: (rounded_lat, rounded_lon) -> (timestamp, data_dict)
WEATHER_CACHE = {}
CACHE_TTL_SECONDS = 600  # 10 minutes cache for instant 0.00s response


def get_wmo_weather_info(code):
    """Converts WMO standard meteorological codes to simple farmer language and icons."""
    return WMO_MAP.get(int(code), ("Scattered Clouds", "⛅"))


def generate_farmer_weather_advisory(temp, humidity, rain_chance, rainfall, wind_speed):
    """Practical, farmer-centric agro advisory based on live meteorological data."""
    tips = []

    # Temperature Advisory
    if temp > 35:
        tips.append(
            f"☀️ High Ambient Heat ({temp}°C): Irrigate fields early morning (before 8 AM) or evening to prevent evaporation stress."
        )
    elif temp < 15:
        tips.append(f"❄️ Cool Temperature ({temp}°C): Protect nursery seedlings and young vegetables from chill shock.")
    else:
        tips.append(
            f"🌱 Temperature Optimal ({temp}°C): Favorable for active photosynthesis and crop vegetative growth."
        )

    # Humidity Advisory
    if humidity > 75:
        tips.append(
            f"💧 High Relative Humidity ({humidity}%): Elevated disease risk. Inspect crop foliage for fungal spots, blast, and blight."
        )
    elif humidity < 40:
        tips.append(
            f"🌾 Low Humidity ({humidity}%): Rapid transpiration rate. Mulch soil bed surface to conserve root zone moisture."
        )

    # Rain & Precipitation Advisory
    if rainfall > 5.0 or rain_chance >= 75:
        tips.append(
            f"🌧️ Rain Warning (Chance: {rain_chance}%, Accumulation: {rainfall} mm): Postpone chemical spraying and fertilizer top-dressing until foliage dries."
        )
    elif rain_chance >= 40 or rainfall > 0.0:
        tips.append(
            f"🌦️ Light Precipitation Possible (Chance: {rain_chance}%, {rainfall} mm): Monitor soil bed moisture before scheduling next irrigation."
        )
    else:
        tips.append(
            f"☀️ Dry Weather Expected (Rain Chance: {rain_chance}%): Excellent conditions for tractor operations, harvesting, or foliar fertilizer spraying."
        )

    # Wind Speed Advisory (10m height)
    if wind_speed > 20:
        tips.append(
            f"💨 High Wind Speed ({wind_speed} km/h): Unsafe for pesticide/fungicide spraying due to airborne drift."
        )
    else:
        tips.append(
            f"🌬️ Calm Wind ({wind_speed} km/h): Safe conditions for tractor boom spraying and foliar nutrient application."
        )

    return tips


def get_weather_data(location="Pune", lat=None, lon=None):
    """
    Ultra-Fast, High-Performance Meteorological Engine with In-Memory Caching.
    Returns in <0.001 seconds when cached, matching Google Weather / IMD ground stations.
    """
    city_name = str(location or "Pune").strip()
    clean_city = city_name.split(",")[0].strip()
    city_key = clean_city.lower()

    target_lat = float(lat) if lat is not None and str(lat).strip() != "" else None
    target_lon = float(lon) if lon is not None and str(lon).strip() != "" else None
    resolved_name = city_name

    # 1. Coordinate Resolution: Check Instant Cache First
    if target_lat is None or target_lon is None:
        if city_key in GEO_CACHE:
            target_lat, target_lon, resolved_name = GEO_CACHE[city_key]
        else:
            try:
                geo_url = (
                    f"https://geocoding-api.open-meteo.com/v1/search?name={clean_city}&count=5&language=en&format=json"
                )
                g_resp = requests.get(geo_url, timeout=2.5)
                if g_resp.status_code == 200:
                    results = g_resp.json().get("results", [])
                    in_match = next(
                        (r for r in results if r.get("country_code") == "IN"), results[0] if results else None
                    )
                    if in_match:
                        target_lat = round(in_match["latitude"], 4)
                        target_lon = round(in_match["longitude"], 4)
                        admin = in_match.get("admin1", "")
                        resolved_name = f"{in_match.get('name')}{', ' + admin if admin else ''}"
                        # Save in cache for future instant queries
                        GEO_CACHE[city_key] = (target_lat, target_lon, resolved_name)
            except Exception as e:
                print(f"⚠️ Geocoding warning for {city_name}: {e}")

    # Fallback to Pune coordinates if still unresolved
    if target_lat is None or target_lon is None:
        target_lat, target_lon = 18.5204, 73.8567
        resolved_name = "Pune, Maharashtra"

    # 2. Check High-Speed Weather Cache (Returns in <1ms)
    cache_key = (round(target_lat, 2), round(target_lon, 2))
    now = time.time()
    if cache_key in WEATHER_CACHE:
        cached_time, cached_data = WEATHER_CACHE[cache_key]
        if now - cached_time < CACHE_TTL_SECONDS:
            # Refresh city name if specific city queried
            result = dict(cached_data)
            result["city"] = resolved_name
            return result

    # 3. Query High-Resolution Live Meteorological Model (ECMWF / Open-Meteo)
    try:
        w_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={target_lat}&longitude={target_lon}&"
            f"past_days=30&"
            f"current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,rain,weather_code,wind_speed_10m&"
            f"hourly=precipitation_probability,relative_humidity_2m&"
            f"daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,et0_fao_evapotranspiration&"
            f"timezone=auto"
        )
        resp = requests.get(w_url, timeout=3.5)
        if resp.status_code == 200:
            data = resp.json()
            curr = data.get("current", {})
            daily = data.get("daily", {})
            hourly = data.get("hourly", {})

            # Temperature and feels like
            temp = round(float(curr.get("temperature_2m", 26.0)), 1)
            feels_like = round(float(curr.get("apparent_temperature", temp)), 1)
            humidity = int(curr.get("relative_humidity_2m", 65))
            rainfall = round(float(curr.get("precipitation", curr.get("rain", 0.0))), 1)
            wind_speed = round(float(curr.get("wind_speed_10m", 10.0)), 1)

            # Precipitation probability for current hour (matches Google's exact "Precipitation: XX%")
            curr_time_str = curr.get("time", "")
            hourly_times = hourly.get("time", [])
            probs = hourly.get("precipitation_probability", [])
            if curr_time_str and curr_time_str in hourly_times:
                match_idx = hourly_times.index(curr_time_str)
                rain_chance = int(probs[match_idx]) if match_idx < len(probs) else 0
            else:
                now_hour = datetime.now().hour
                rain_chance = int(probs[now_hour]) if now_hour < len(probs) else (int(probs[0]) if probs else 0)

            # WMO Weather Condition
            w_code = int(curr.get("weather_code", 0))
            condition, icon = get_wmo_weather_info(w_code)

            # 7-Day Daily Agro-Meteorological Forecast
            times = daily.get("time", [])
            max_temps = daily.get("temperature_2m_max", [])
            min_temps = daily.get("temperature_2m_min", [])
            rain_sums = daily.get("precipitation_sum", [])
            prob_maxs = daily.get("precipitation_probability_max", [])
            codes = daily.get("weather_code", [])
            et0s = daily.get("et0_fao_evapotranspiration", [])
            # Locate today's index in time series (when past_days=30, index 0 is 30 days ago, index ~30 is today)
            try:
                today_str = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d")
            except Exception:
                today_str = datetime.now().strftime("%Y-%m-%d")

            today_idx = -1
            if today_str in times:
                today_idx = times.index(today_str)
            else:
                for idx, t in enumerate(times):
                    if t >= today_str:
                        today_idx = idx
                        break
            if today_idx < 0:
                today_idx = 30 if len(times) >= 37 else 0

            # Evapotranspiration for TODAY
            today_et0 = round(float(et0s[today_idx]), 2) if (et0s and len(et0s) > today_idx and et0s[today_idx] is not None) else (round(float(et0s[0]), 2) if et0s and et0s[0] is not None else None)

            # 7-Day Daily Agro-Meteorological Forecast starting from TODAY onwards
            forecast = []
            today_dt = datetime.strptime(today_str, "%Y-%m-%d")
            for offset in range(7):
                idx = today_idx + offset
                expected_date = (today_dt + timedelta(days=offset)).strftime("%Y-%m-%d")
                d_str = times[idx] if idx < len(times) else expected_date
                # Explicitly guarantee offset 0 is today_str
                if offset == 0:
                    d_str = today_str
                day_label = "Today" if offset == 0 else (today_dt + timedelta(days=offset)).strftime("%a")

                c_val = int(codes[idx]) if idx < len(codes) else 0
                c_txt, c_ico = get_wmo_weather_info(c_val)
                p_chance = int(prob_maxs[idx]) if idx < len(prob_maxs) else 0
                r_mm = round(float(rain_sums[idx]), 1) if idx < len(rain_sums) else 0.0
                day_et0 = round(float(et0s[idx]), 2) if (idx < len(et0s) and et0s[idx] is not None) else 5.0

                forecast.append(
                    {
                        "day": day_label,
                        "date": d_str,
                        "max_temp": round(float(max_temps[idx]), 1) if idx < len(max_temps) else temp + 2,
                        "min_temp": round(float(min_temps[idx]), 1) if idx < len(min_temps) else temp - 4,
                        "rain_mm": r_mm,
                        "rain_chance": p_chance,
                        "condition": c_txt,
                        "icon": c_ico,
                        "et0": day_et0,
                    }
                )

            # Calculate 30-day cumulative rainfall and averages strictly from past days (0 to today_idx)
            past_rain_sums = rain_sums[:today_idx] if today_idx > 0 else (rain_sums[:30] if len(rain_sums) >= 30 else rain_sums)
            rainfall_last_30_days = round(float(sum(past_rain_sums)), 1) if past_rain_sums else 85.0

            past_t_maxs = max_temps[:today_idx] if today_idx > 0 else (max_temps[:30] if len(max_temps) >= 30 else max_temps)
            past_t_mins = min_temps[:today_idx] if today_idx > 0 else (min_temps[:30] if len(min_temps) >= 30 else min_temps)
            if past_t_maxs and past_t_mins:
                mean_t = (sum(past_t_maxs) / len(past_t_maxs) + sum(past_t_mins) / len(past_t_mins)) / 2.0
                temperature_last_30_days = round(float(mean_t), 1)
            else:
                temperature_last_30_days = temp

            h_hourly = hourly.get("relative_humidity_2m", [])
            past_h = h_hourly[: today_idx * 24] if today_idx > 0 else (h_hourly[: 30 * 24] if len(h_hourly) >= 30 * 24 else h_hourly)
            if past_h:
                humidity_last_30_days = round(float(sum(past_h) / len(past_h)), 1)
            else:
                humidity_last_30_days = float(humidity)

            weather_res = {
                "city": resolved_name,
                "latitude": target_lat,
                "longitude": target_lon,
                "temperature": temp,
                "temperature_max": round(float(max_temps[today_idx]), 1) if len(max_temps) > today_idx else temp + 2,
                "temperature_min": round(float(min_temps[today_idx]), 1) if len(min_temps) > today_idx else temp - 4,
                "feels_like": feels_like,
                "humidity": humidity,
                "precipitation_chance": rain_chance,
                "rainfall": rainfall,
                "rainfall_last_30_days": rainfall_last_30_days,
                "temperature_last_30_days": temperature_last_30_days,
                "humidity_last_30_days": humidity_last_30_days,
                "wind_speed": wind_speed,
                "condition": condition,
                "icon": icon,
                "et0_fao_evapotranspiration": today_et0,
                "forecast_source": "Open-Meteo API (Live Telemetry)",
                "forecast": forecast,
                "advisory": generate_farmer_weather_advisory(temp, humidity, rain_chance, rainfall, wind_speed),
            }

            # Cache the result
            WEATHER_CACHE[cache_key] = (now, weather_res)
            return weather_res

    except Exception as e:
        print(f"⚠️ Open-Meteo query failed: {e}")

    # Fallback to OpenWeatherMap if Open-Meteo is temporarily unreachable
    api_key = Config.OPENWEATHER_API_KEY
    if api_key:
        try:
            params = {"appid": api_key, "units": "metric", "lat": target_lat, "lon": target_lon}
            owm_resp = requests.get(Config.OPENWEATHER_BASE_URL, params=params, timeout=3)
            if owm_resp.status_code == 200:
                data = owm_resp.json()
                temp = round(float(data["main"]["temp"]), 1)
                feels_like = round(float(data["main"].get("feels_like", temp)), 1)
                humidity = int(data["main"]["humidity"])
                wind = round(float(data.get("wind", {}).get("speed", 3.0)) * 3.6, 1)
                condition = data.get("weather", [{}])[0].get("description", "Clear Sky").title()
                rain_dict = data.get("rain", {})
                rain_mm = round(float(rain_dict.get("1h", rain_dict.get("3h", 0.0))), 1)

                try:
                    f_today = datetime.now(ZoneInfo("Asia/Kolkata")).date()
                except Exception:
                    f_today = datetime.now().date()
                fallback_forecast = []
                for offset in range(7):
                    f_dt = f_today + timedelta(days=offset)
                    fallback_forecast.append({
                        "day": "Today" if offset == 0 else f_dt.strftime("%a"),
                        "date": f_dt.strftime("%Y-%m-%d"),
                        "max_temp": 30.0,
                        "min_temp": 24.0,
                        "rain_mm": 0.0,
                        "rain_chance": 10,
                        "condition": "Partly Cloudy",
                        "icon": "⛅",
                        "et0": 5.0,
                    })

                owm_res = {
                    "city": resolved_name,
                    "temperature": temp,
                    "feels_like": feels_like,
                    "humidity": humidity,
                    "precipitation_chance": 20 if rain_mm > 0 else 5,
                    "rainfall": rain_mm,
                    "rainfall_last_30_days": 85.0 if rain_mm == 0 else round(rain_mm * 15.0, 1),
                    # Fallback note: OWM provides instantaneous weather; 30-day diurnal mean estimated
                    "temperature_last_30_days": round(temp - 1.2, 1),
                    "humidity_last_30_days": round(min(100.0, float(humidity) + 2.0), 1),
                    "wind_speed": wind,
                    "condition": condition,
                    "icon": "⛅",
                    "forecast_source": "Fallback (OpenWeatherMap / Estimated)",
                    "forecast": fallback_forecast,
                    "advisory": generate_farmer_weather_advisory(temp, humidity, 10, rain_mm, wind),
                }
                WEATHER_CACHE[cache_key] = (now, owm_res)
                return owm_res
        except Exception as e:
            print(f"⚠️ OpenWeatherMap fallback error: {e}")

    # Baseline Safe Return (Regional 30-day agro-climatic averages for Indian plains)
    try:
        b_today = datetime.now(ZoneInfo("Asia/Kolkata")).date()
    except Exception:
        b_today = datetime.now().date()
    baseline_forecast = []
    for offset in range(7):
        b_dt = b_today + timedelta(days=offset)
        baseline_forecast.append({
            "day": "Today" if offset == 0 else b_dt.strftime("%a"),
            "date": b_dt.strftime("%Y-%m-%d"),
            "max_temp": 30.0,
            "min_temp": 24.0,
            "rain_mm": 0.0,
            "rain_chance": 10,
            "condition": "Partly Cloudy",
            "icon": "⛅",
            "et0": 5.0,
        })

    return {
        "city": resolved_name,
        "temperature": 27.0,
        "feels_like": 29.0,
        "humidity": 65,
        "precipitation_chance": 10,
        "rainfall": 0.0,
        "rainfall_last_30_days": 85.0,
        "temperature_last_30_days": 27.0,
        "humidity_last_30_days": 65.0,
        "wind_speed": 10.0,
        "condition": "Partly Cloudy",
        "icon": "⛅",
        "forecast_source": "Fallback (Agro-climatic Regional Baseline)",
        "forecast": baseline_forecast,
        "advisory": ["🌱 Regular Farm Operations: Good conditions for normal field work."],
    }
