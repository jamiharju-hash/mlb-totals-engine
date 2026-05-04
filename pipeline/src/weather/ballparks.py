from __future__ import annotations

from typing import Literal, TypedDict


RoofType = Literal["open", "retractable", "dome"]


class BallparkInfo(TypedDict):
    ballpark_name: str
    lat: float
    lon: float
    roof: RoofType
    elevation_ft: int
    cf_bearing: float


BALLPARKS: dict[str, BallparkInfo] = {
    "ARI": {"ballpark_name": "Chase Field", "lat": 33.4455, "lon": -112.0667, "roof": "dome", "elevation_ft": 1086, "cf_bearing": 20.0},
    "ATL": {"ballpark_name": "Truist Park", "lat": 33.8908, "lon": -84.4677, "roof": "open", "elevation_ft": 1050, "cf_bearing": 35.0},
    "BAL": {"ballpark_name": "Oriole Park at Camden Yards", "lat": 39.2838, "lon": -76.6217, "roof": "open", "elevation_ft": 20, "cf_bearing": 45.0},
    "BOS": {"ballpark_name": "Fenway Park", "lat": 42.3467, "lon": -71.0972, "roof": "open", "elevation_ft": 20, "cf_bearing": 55.0},
    "CHC": {"ballpark_name": "Wrigley Field", "lat": 41.9484, "lon": -87.6553, "roof": "open", "elevation_ft": 600, "cf_bearing": 20.0},
    "CIN": {"ballpark_name": "Great American Ball Park", "lat": 39.0979, "lon": -84.5082, "roof": "open", "elevation_ft": 490, "cf_bearing": 30.0},
    "CLE": {"ballpark_name": "Progressive Field", "lat": 41.4962, "lon": -81.6852, "roof": "open", "elevation_ft": 650, "cf_bearing": 25.0},
    "COL": {"ballpark_name": "Coors Field", "lat": 39.7561, "lon": -104.9942, "roof": "open", "elevation_ft": 5200, "cf_bearing": 35.0},
    "CWS": {"ballpark_name": "Rate Field", "lat": 41.8300, "lon": -87.6338, "roof": "open", "elevation_ft": 595, "cf_bearing": 15.0},
    "DET": {"ballpark_name": "Comerica Park", "lat": 42.3390, "lon": -83.0485, "roof": "open", "elevation_ft": 585, "cf_bearing": 30.0},
    "HOU": {"ballpark_name": "Daikin Park", "lat": 29.7573, "lon": -95.3555, "roof": "dome", "elevation_ft": 50, "cf_bearing": 25.0},
    "KC": {"ballpark_name": "Kauffman Stadium", "lat": 39.0517, "lon": -94.4803, "roof": "open", "elevation_ft": 910, "cf_bearing": 40.0},
    "LAA": {"ballpark_name": "Angel Stadium", "lat": 33.8003, "lon": -117.8827, "roof": "retractable", "elevation_ft": 160, "cf_bearing": 35.0},
    "LAD": {"ballpark_name": "Dodger Stadium", "lat": 34.0739, "lon": -118.2400, "roof": "open", "elevation_ft": 535, "cf_bearing": 25.0},
    "MIA": {"ballpark_name": "loanDepot park", "lat": 25.7781, "lon": -80.2197, "roof": "dome", "elevation_ft": 10, "cf_bearing": 20.0},
    "MIL": {"ballpark_name": "American Family Field", "lat": 43.0280, "lon": -87.9712, "roof": "dome", "elevation_ft": 640, "cf_bearing": 30.0},
    "MIN": {"ballpark_name": "Target Field", "lat": 44.9817, "lon": -93.2778, "roof": "open", "elevation_ft": 815, "cf_bearing": 35.0},
    "NYM": {"ballpark_name": "Citi Field", "lat": 40.7571, "lon": -73.8458, "roof": "open", "elevation_ft": 20, "cf_bearing": 40.0},
    "NYY": {"ballpark_name": "Yankee Stadium", "lat": 40.8296, "lon": -73.9262, "roof": "open", "elevation_ft": 55, "cf_bearing": 35.0},
    "OAK": {"ballpark_name": "Sutter Health Park", "lat": 38.5803, "lon": -121.5133, "roof": "open", "elevation_ft": 30, "cf_bearing": 30.0},
    "PHI": {"ballpark_name": "Citizens Bank Park", "lat": 39.9061, "lon": -75.1665, "roof": "open", "elevation_ft": 25, "cf_bearing": 35.0},
    "PIT": {"ballpark_name": "PNC Park", "lat": 40.4469, "lon": -80.0057, "roof": "open", "elevation_ft": 730, "cf_bearing": 45.0},
    "SD": {"ballpark_name": "Petco Park", "lat": 32.7073, "lon": -117.1566, "roof": "open", "elevation_ft": 60, "cf_bearing": 35.0},
    "SEA": {"ballpark_name": "T-Mobile Park", "lat": 47.5914, "lon": -122.3325, "roof": "dome", "elevation_ft": 20, "cf_bearing": 20.0},
    "SF": {"ballpark_name": "Oracle Park", "lat": 37.7786, "lon": -122.3893, "roof": "open", "elevation_ft": 10, "cf_bearing": 60.0},
    "STL": {"ballpark_name": "Busch Stadium", "lat": 38.6226, "lon": -90.1928, "roof": "open", "elevation_ft": 460, "cf_bearing": 20.0},
    "TB": {"ballpark_name": "George M. Steinbrenner Field", "lat": 27.9800, "lon": -82.5061, "roof": "dome", "elevation_ft": 45, "cf_bearing": 30.0},
    "TEX": {"ballpark_name": "Globe Life Field", "lat": 32.7473, "lon": -97.0847, "roof": "retractable", "elevation_ft": 550, "cf_bearing": 35.0},
    "TOR": {"ballpark_name": "Rogers Centre", "lat": 43.6414, "lon": -79.3894, "roof": "dome", "elevation_ft": 250, "cf_bearing": 30.0},
    "WSH": {"ballpark_name": "Nationals Park", "lat": 38.8730, "lon": -77.0074, "roof": "open", "elevation_ft": 25, "cf_bearing": 30.0},
}
