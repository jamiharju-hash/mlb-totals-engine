from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests

from .ballparks import BALLPARKS

logger = logging.getLogger(__name__)

OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1"
FORECAST_TTL_HOURS = 2
MPS_TO_MPH = 0.621371
KPH_PER_MPH = 1.60934
TEMP_THRESHOLD_F = 60.0
TEMP_PENALTY_PER_DEGREE = -0.08
WIND_OUT_PER_5_MPH = 0.12
WIND_IN_PER_5_MPH = -0.10
RAIN_PROB_THRESHOLD = 60.0
RAIN_FLAT_PENALTY = -0.15
MAX_POSITIVE_ADJUSTMENT = 0.5
MAX_NEGATIVE_ADJUSTMENT = -0.5
VARIABLE_WIND_THRESHOLD_KPH = 1.0


@dataclass
class WeatherSnapshot:
    game_id: str
    game_date: date
    first_pitch_utc: datetime
    team: str
    ballpark: str
    roof: str
    temperature_c: float
    wind_speed_kph: float
    wind_direction_deg: float
    wind_direction_label: str
    precipitation_prob_pct: float
    condition_summary: str
    weather_adjustment: float
    is_dome: bool
    fetched_at: datetime
    source: str = "open-meteo"


def _cache_file(path: Path, ttl_hours: int | None = None) -> bool:
    if not path.exists():
        return False
    if ttl_hours is None:
        return True
    age = datetime.now(timezone.utc) - datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return age <= timedelta(hours=ttl_hours)


def _read_cache(path: Path) -> dict:
    return json.loads(path.read_text())


def _write_cache(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload))


def fetch_forecast(lat: float, lon: float, first_pitch_utc: datetime) -> dict:
    day = first_pitch_utc.date().isoformat()
    cache_path = Path(f"pipeline/data/raw/weather/{day}/{lat}_{lon}.json")
    if _cache_file(cache_path, ttl_hours=FORECAST_TTL_HOURS):
        return _read_cache(cache_path)

    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,wind_speed_10m,wind_direction_10m,precipitation_probability",
        "timezone": "UTC",
        "start_date": day,
        "end_date": day,
    }
    response = requests.get(f"{OPEN_METEO_BASE_URL}/forecast", params=params, timeout=20)
    response.raise_for_status()
    payload = response.json()
    _write_cache(cache_path, payload)
    return payload


def fetch_historical(lat: float, lon: float, game_date: date) -> dict:
    day = game_date.isoformat()
    cache_path = Path(f"pipeline/data/raw/weather/historical/{day}/{lat}_{lon}.json")
    if _cache_file(cache_path, ttl_hours=None):
        return _read_cache(cache_path)

    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,wind_speed_10m,wind_direction_10m,precipitation_probability",
        "timezone": "UTC",
        "start_date": day,
        "end_date": day,
    }
    response = requests.get(f"{OPEN_METEO_BASE_URL}/era5", params=params, timeout=20)
    response.raise_for_status()
    payload = response.json()
    _write_cache(cache_path, payload)
    return payload


def wind_direction_label(wind_deg: float, ballpark_cf_deg: float) -> str:
    if wind_deg < 0:
        return "variable"
    delta = ((wind_deg - ballpark_cf_deg + 180) % 360) - 180
    if abs(delta) <= 45:
        return "out to CF"
    if abs(abs(delta) - 180) <= 45:
        return "in from CF"
    return "crosswind R" if delta > 0 else "crosswind L"


def compute_weather_adjustment(snapshot: WeatherSnapshot) -> float:
    if snapshot.is_dome:
        return 0.0

    total = 0.0
    temp_f = snapshot.temperature_c * 9 / 5 + 32
    if temp_f < TEMP_THRESHOLD_F:
        total += (TEMP_THRESHOLD_F - temp_f) * TEMP_PENALTY_PER_DEGREE

    wind_mph = snapshot.wind_speed_kph / KPH_PER_MPH
    if snapshot.wind_direction_label == "out to CF":
        total += (wind_mph / 5.0) * WIND_OUT_PER_5_MPH
    elif snapshot.wind_direction_label == "in from CF":
        total += (wind_mph / 5.0) * WIND_IN_PER_5_MPH

    if snapshot.precipitation_prob_pct > RAIN_PROB_THRESHOLD:
        total += RAIN_FLAT_PENALTY

    return max(MAX_NEGATIVE_ADJUSTMENT, min(MAX_POSITIVE_ADJUSTMENT, total))


def _extract_hourly(payload: dict, first_pitch_utc: datetime) -> dict:
    target_hour = first_pitch_utc.replace(minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:00")
    hourly = payload.get("hourly", {})
    times = hourly.get("time", [])
    if target_hour in times:
        idx = times.index(target_hour)
    else:
        idx = 0
    return {
        "temperature_c": float(hourly.get("temperature_2m", [0.0])[idx]),
        "wind_speed_kph": float(hourly.get("wind_speed_10m", [0.0])[idx]),
        "wind_direction_deg": float(hourly.get("wind_direction_10m", [-1.0])[idx]),
        "precipitation_prob_pct": float(hourly.get("precipitation_probability", [0.0])[idx]),
    }


def get_weather_for_game(game_id: str, home_team: str, first_pitch_utc: datetime) -> WeatherSnapshot:
    team = home_team.upper()
    park = BALLPARKS[team]
    now = datetime.now(timezone.utc)
    first_pitch_utc = first_pitch_utc.astimezone(timezone.utc)
    is_dome = park["roof"] == "dome"

    try:
        payload = fetch_forecast(park["lat"], park["lon"], first_pitch_utc) if first_pitch_utc > now else fetch_historical(park["lat"], park["lon"], first_pitch_utc.date())
        observed = _extract_hourly(payload, first_pitch_utc)
        direction = wind_direction_label(observed["wind_direction_deg"], park["cf_bearing"]) if observed["wind_speed_kph"] > VARIABLE_WIND_THRESHOLD_KPH else "variable"

        snapshot = WeatherSnapshot(
            game_id=game_id,
            game_date=first_pitch_utc.date(),
            first_pitch_utc=first_pitch_utc,
            team=team,
            ballpark=park["ballpark_name"],
            roof=park["roof"],
            temperature_c=observed["temperature_c"],
            wind_speed_kph=observed["wind_speed_kph"],
            wind_direction_deg=observed["wind_direction_deg"],
            wind_direction_label=direction,
            precipitation_prob_pct=observed["precipitation_prob_pct"],
            condition_summary="Rain likely" if observed["precipitation_prob_pct"] > RAIN_PROB_THRESHOLD else "Clear",
            weather_adjustment=0.0,
            is_dome=is_dome,
            fetched_at=now,
        )
        snapshot.weather_adjustment = compute_weather_adjustment(snapshot)
        return snapshot
    except Exception as exc:  # noqa: BLE001
        logger.warning("Weather fetch failed for %s: %s", game_id, exc)
        return WeatherSnapshot(
            game_id=game_id,
            game_date=first_pitch_utc.date(),
            first_pitch_utc=first_pitch_utc,
            team=team,
            ballpark=park["ballpark_name"],
            roof=park["roof"],
            temperature_c=0.0,
            wind_speed_kph=0.0,
            wind_direction_deg=-1.0,
            wind_direction_label="variable",
            precipitation_prob_pct=0.0,
            condition_summary="unavailable",
            weather_adjustment=0.0,
            is_dome=is_dome,
            fetched_at=now,
        )
