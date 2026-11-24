"""Download the OpenFlights airports and routes datasets into data/raw/.

Data: OpenFlights (https://openflights.org/data), Open Database License (ODbL).
"""
from pathlib import Path
from urllib.request import urlretrieve

BASE_URL = "https://raw.githubusercontent.com/jpatokal/openflights/master/data"
FILES = ["airports.dat", "routes.dat"]
RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        target = RAW_DIR / name
        print(f"Downloading {name} ...")
        urlretrieve(f"{BASE_URL}/{name}", target)
        print(f"  saved {target} ({target.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
