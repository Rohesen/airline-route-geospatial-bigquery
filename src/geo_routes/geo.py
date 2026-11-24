"""Spherical geometry helpers: great-circle distance and paths.

These mirror what BigQuery GIS does with ST_DISTANCE and ST_MAKELINE on
GEOGRAPHY values, so local results can be checked against BigQuery.
"""
import math

import numpy as np

EARTH_RADIUS_KM = 6371.0088  # mean Earth radius


def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance in km. Works on scalars or numpy arrays."""
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def great_circle_path(lat1, lon1, lat2, lon2, n_points: int = 32):
    """Points along the great circle between two coordinates, for drawing routes."""
    p1 = np.radians([lat1, lon1])
    p2 = np.radians([lat2, lon2])
    d = haversine_km(lat1, lon1, lat2, lon2) / EARTH_RADIUS_KM
    if d == 0:
        return [(lat1, lon1)]
    points = []
    for f in np.linspace(0, 1, n_points):
        a = math.sin((1 - f) * d) / math.sin(d)
        b = math.sin(f * d) / math.sin(d)
        x = a * math.cos(p1[0]) * math.cos(p1[1]) + b * math.cos(p2[0]) * math.cos(p2[1])
        y = a * math.cos(p1[0]) * math.sin(p1[1]) + b * math.cos(p2[0]) * math.sin(p2[1])
        z = a * math.sin(p1[0]) + b * math.sin(p2[0])
        lat = math.degrees(math.atan2(z, math.sqrt(x * x + y * y)))
        lon = math.degrees(math.atan2(y, x))
        points.append((lat, lon))
    return points
