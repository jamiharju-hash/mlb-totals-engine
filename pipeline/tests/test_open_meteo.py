from datetime import datetime, timedelta, timezone

from pipeline.src.weather.open_meteo import WeatherSnapshot, compute_weather_adjustment, get_weather_for_game


def _snapshot(**overrides):
    base = WeatherSnapshot(
        game_id="g1",
        game_date=datetime.now(timezone.utc).date(),
        first_pitch_utc=datetime.now(timezone.utc),
        team="SEA",
        ballpark="T-Mobile Park",
        roof="dome",
        temperature_c=10.0,
        wind_speed_kph=20.0,
        wind_direction_deg=0.0,
        wind_direction_label="out to CF",
        precipitation_prob_pct=0.0,
        condition_summary="Clear",
        weather_adjustment=0.0,
        is_dome=True,
        fetched_at=datetime.now(timezone.utc),
    )
    for k, v in overrides.items():
        setattr(base, k, v)
    return base


def test_compute_adjustment_zero_for_dome():
    assert compute_weather_adjustment(_snapshot()) == 0.0


def test_temperature_below_60_negative_adjustment():
    snap = _snapshot(is_dome=False, roof="open", temperature_c=0.0, wind_speed_kph=0.0, wind_direction_label="variable")
    assert compute_weather_adjustment(snap) < 0.0


def test_wind_out_positive_adjustment():
    snap = _snapshot(is_dome=False, roof="open", temperature_c=20.0, wind_speed_kph=24.0, wind_direction_label="out to CF")
    assert compute_weather_adjustment(snap) > 0.0


def test_wind_in_negative_adjustment():
    snap = _snapshot(is_dome=False, roof="open", temperature_c=20.0, wind_speed_kph=24.0, wind_direction_label="in from CF")
    assert compute_weather_adjustment(snap) < 0.0


def test_total_adjustment_capped():
    pos = _snapshot(is_dome=False, roof="open", temperature_c=30.0, wind_speed_kph=200.0, wind_direction_label="out to CF")
    neg = _snapshot(is_dome=False, roof="open", temperature_c=-20.0, wind_speed_kph=200.0, wind_direction_label="in from CF", precipitation_prob_pct=100.0)
    assert compute_weather_adjustment(pos) <= 0.5
    assert compute_weather_adjustment(neg) >= -0.5


def test_get_weather_handles_http_error(monkeypatch):
    def _raise(*args, **kwargs):
        raise RuntimeError("500 server error")

    monkeypatch.setattr("pipeline.src.weather.open_meteo.fetch_forecast", _raise)
    snapshot = get_weather_for_game("gid", "NYY", datetime.now(timezone.utc) + timedelta(hours=3))
    assert snapshot.condition_summary == "unavailable"
    assert snapshot.weather_adjustment == 0.0
