import pytest

from geo_routes.geo import great_circle_path, haversine_km

DEL = (28.5665, 77.1031)   # Indira Gandhi International, Delhi
BOM = (19.0887, 72.8679)   # Chhatrapati Shivaji Maharaj International, Mumbai
LHR = (51.4706, -0.461941)
JFK = (40.6398, -73.7789)


def test_same_point_is_zero():
    assert haversine_km(*DEL, *DEL) == pytest.approx(0.0)


def test_delhi_mumbai_distance():
    # Published great-circle distance is about 1,140 km
    assert haversine_km(*DEL, *BOM) == pytest.approx(1140, abs=10)


def test_london_new_york_distance():
    # Published great-circle distance is about 5,540 km
    assert haversine_km(*LHR, *JFK) == pytest.approx(5540, abs=20)


def test_distance_is_symmetric():
    assert haversine_km(*DEL, *BOM) == pytest.approx(haversine_km(*BOM, *DEL))


def test_path_starts_and_ends_at_airports():
    path = great_circle_path(*LHR, *JFK, n_points=10)
    assert len(path) == 10
    assert path[0] == pytest.approx(LHR, abs=1e-6)
    assert path[-1] == pytest.approx(JFK, abs=1e-6)


def test_great_circle_bends_north():
    # London to New York arcs north of both endpoints
    path = great_circle_path(*LHR, *JFK, n_points=20)
    assert max(lat for lat, _ in path) > LHR[0]


def test_nearby_airports_finds_close_pairs():
    import pandas as pd
    from geo_routes.local_pipeline import nearby_airports

    airports = pd.DataFrame({
        "iata": ["DEL", "BOM", "HDO"],
        "city": ["Delhi", "Mumbai", "Ghaziabad"],
        "country": ["India"] * 3,
        "latitude": [28.5665, 19.0887, 28.7075],
        "longitude": [77.1031, 72.8679, 77.3577],
    })
    result = nearby_airports(airports, "India", 100)
    assert list(zip(result["iata"], result["iata_b"])) == [("DEL", "HDO")]
