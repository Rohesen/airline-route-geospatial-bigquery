"""Clean the raw OpenFlights files into typed CSVs ready for BigQuery.

Raw files have no header and use "\\N" for missing values.
"""
from pathlib import Path

import pandas as pd

AIRPORT_COLUMNS = [
    "airport_id", "name", "city", "country", "iata", "icao",
    "latitude", "longitude", "altitude_ft", "utc_offset", "dst",
    "timezone", "type", "source",
]
ROUTE_COLUMNS = [
    "airline", "airline_id", "source_iata", "source_airport_id",
    "dest_iata", "dest_airport_id", "codeshare", "stops", "equipment",
]


def load_airports(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, header=None, names=AIRPORT_COLUMNS, na_values=["\\N"],
                     keep_default_na=False)
    df = df[df["type"] == "airport"]
    df = df.dropna(subset=["iata", "latitude", "longitude"])
    df = df[df["latitude"].between(-90, 90) & df["longitude"].between(-180, 180)]
    df = df.drop_duplicates(subset="iata")
    keep = ["airport_id", "iata", "icao", "name", "city", "country",
            "latitude", "longitude", "altitude_ft", "timezone"]
    return df[keep].reset_index(drop=True)


def load_routes(path: Path, airports: pd.DataFrame) -> pd.DataFrame:
    df = pd.read_csv(path, header=None, names=ROUTE_COLUMNS, na_values=["\\N"],
                     keep_default_na=False)
    df = df[df["stops"] == 0]  # direct flights only
    known = set(airports["iata"])
    df = df[df["source_iata"].isin(known) & df["dest_iata"].isin(known)]
    df = df[df["source_iata"] != df["dest_iata"]]
    df["codeshare"] = df["codeshare"].eq("Y")
    keep = ["airline", "source_iata", "dest_iata", "codeshare", "equipment"]
    return df[keep].drop_duplicates().reset_index(drop=True)


def clean(raw_dir: Path, out_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    out_dir.mkdir(parents=True, exist_ok=True)
    airports = load_airports(raw_dir / "airports.dat")
    routes = load_routes(raw_dir / "routes.dat", airports)
    airports.to_csv(out_dir / "airports.csv", index=False)
    routes.to_csv(out_dir / "routes.csv", index=False)
    return airports, routes


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    a, r = clean(root / "data" / "raw", root / "data" / "clean")
    print(f"airports: {len(a):,}  routes: {len(r):,}")
