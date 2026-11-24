"""Run the same analyses locally with pandas and draw an interactive map.

Useful to check BigQuery results and to explore without a Google Cloud
account. Writes docs/results.md and docs/india_routes_map.html.
"""
from pathlib import Path

import folium
import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from geo_routes.clean import clean
from geo_routes.geo import great_circle_path, haversine_km

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"


def enrich_routes(airports: pd.DataFrame, routes: pd.DataFrame) -> pd.DataFrame:
    """Local equivalent of sql/02_routes_geo.sql."""
    a = airports.set_index("iata")[["country", "latitude", "longitude"]]
    df = routes.join(a.add_prefix("src_"), on="source_iata").join(a.add_prefix("dst_"), on="dest_iata")
    df["distance_km"] = haversine_km(df["src_latitude"], df["src_longitude"],
                                     df["dst_latitude"], df["dst_longitude"]).round(1)
    df["is_domestic"] = df["src_country"] == df["dst_country"]
    return df


def longest_routes(routes: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    pairs = routes[routes["source_iata"] < routes["dest_iata"]]
    return (pairs.groupby(["source_iata", "dest_iata", "src_country", "dst_country", "distance_km"])
            ["airline"].nunique().rename("airlines").reset_index()
            .sort_values("distance_km", ascending=False).head(n))


def hubs(routes: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    return (routes.groupby("source_iata")
            .agg(destinations=("dest_iata", "nunique"),
                 countries_served=("dst_country", "nunique"),
                 avg_route_km=("distance_km", "mean"))
            .round({"avg_route_km": 0})
            .sort_values("destinations", ascending=False).head(n).reset_index())


def nearby_airports(airports: pd.DataFrame, country: str, max_km: float) -> pd.DataFrame:
    """Local equivalent of the ST_DWITHIN join in sql/05_nearby_airports.sql."""
    a = airports[airports["country"] == country]
    pairs = a.merge(a, how="cross", suffixes=("", "_b"))
    pairs = pairs[pairs["iata"] < pairs["iata_b"]].copy()
    pairs["distance_km"] = haversine_km(pairs["latitude"], pairs["longitude"],
                                        pairs["latitude_b"], pairs["longitude_b"]).round(1)
    return (pairs[pairs["distance_km"] <= max_km]
            [["iata", "city", "iata_b", "city_b", "distance_km"]]
            .sort_values("distance_km").reset_index(drop=True))


def domestic_bands(routes: pd.DataFrame, country: str) -> pd.DataFrame:
    d = routes[routes["is_domestic"] & (routes["src_country"] == country)]
    d = d[d["source_iata"] < d["dest_iata"]].drop_duplicates(["source_iata", "dest_iata"])
    bands = pd.cut(d["distance_km"], [0, 500, 1000, 1500, 10_000],
                   labels=["under 500 km", "500-1,000 km", "1,000-1,500 km", "over 1,500 km"])
    out = bands.value_counts().sort_index().rename_axis("distance_band").reset_index(name="routes")
    out["share"] = (out["routes"] / out["routes"].sum() * 100).round(1).astype(str) + "%"
    return out


def india_map(airports: pd.DataFrame, routes: pd.DataFrame, path: Path) -> None:
    d = routes[routes["is_domestic"] & (routes["src_country"] == "India")]
    pairs = d[d["source_iata"] < d["dest_iata"]].drop_duplicates(["source_iata", "dest_iata"])
    degree = d.groupby("source_iata")["dest_iata"].nunique()

    m = folium.Map(location=[22.5, 79], zoom_start=5, tiles="OpenStreetMap")
    for _, r in pairs.iterrows():
        line = great_circle_path(r["src_latitude"], r["src_longitude"],
                                 r["dst_latitude"], r["dst_longitude"], n_points=16)
        folium.PolyLine(line, weight=1, opacity=0.35, color="#1f5fbf",
                        tooltip=f"{r['source_iata']}-{r['dest_iata']}: {r['distance_km']:,.0f} km").add_to(m)
    india = airports[airports["iata"].isin(degree.index)]
    for _, a in india.iterrows():
        n = int(degree[a["iata"]])
        folium.CircleMarker([a["latitude"], a["longitude"]], radius=3 + n ** 0.5 * 1.5,
                            color="#c0392b", fill=True, fill_opacity=0.8, weight=1,
                            tooltip=f"{a['iata']} ({a['city']}): {n} domestic destinations").add_to(m)
    m.save(path)


def india_png(airports: pd.DataFrame, routes: pd.DataFrame, path: Path) -> None:
    """Static picture of the same network, for the README."""
    d = routes[routes["is_domestic"] & (routes["src_country"] == "India")]
    pairs = d[d["source_iata"] < d["dest_iata"]].drop_duplicates(["source_iata", "dest_iata"])
    degree = d.groupby("source_iata")["dest_iata"].nunique()
    india = airports[airports["iata"].isin(degree.index)].copy()
    india["degree"] = india["iata"].map(degree)

    fig, ax = plt.subplots(figsize=(8, 9), dpi=130)
    for _, r in pairs.iterrows():
        line = great_circle_path(r["src_latitude"], r["src_longitude"],
                                 r["dst_latitude"], r["dst_longitude"], n_points=16)
        lats, lons = zip(*line)
        ax.plot(lons, lats, color="#1f5fbf", alpha=0.25, linewidth=0.7)
    ax.scatter(india["longitude"], india["latitude"], s=8 + india["degree"] * 4,
               color="#c0392b", alpha=0.85, edgecolor="white", linewidth=0.5, zorder=3)
    for _, a in india.nlargest(8, "degree").iterrows():
        ax.annotate(a["iata"], (a["longitude"], a["latitude"]), xytext=(5, 4),
                    textcoords="offset points", fontsize=9, fontweight="bold")
    ax.set_title("India domestic air network: great-circle routes, hubs sized by destinations")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_aspect("equal")
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def to_md(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for row in df.itertuples(index=False):
        lines.append("| " + " | ".join(f"{v:,.0f}" if isinstance(v, float) else str(v) for v in row) + " |")
    return "\n".join(lines)


def main() -> None:
    airports, routes = clean(ROOT / "data" / "raw", ROOT / "data" / "clean")
    routes = enrich_routes(airports, routes)
    DOCS.mkdir(exist_ok=True)

    sections = [
        ("Longest direct routes in the world", longest_routes(routes)),
        ("Top hub airports by direct destinations", hubs(routes)),
        ("Closest pairs of Indian airports (within 100 km)", nearby_airports(airports, "India", 100).head(15)),
        ("India domestic routes by distance band", domestic_bands(routes, "India")),
    ]
    md = ["# Results (local run)", "",
          f"{len(airports):,} airports and {len(routes):,} direct airline routes after cleaning.", ""]
    for title, df in sections:
        md += [f"## {title}", "", to_md(df), ""]
    (DOCS / "results.md").write_text("\n".join(md))
    india_map(airports, routes, DOCS / "india_routes_map.html")
    india_png(airports, routes, DOCS / "india_routes_map.png")
    print("\n".join(md))


if __name__ == "__main__":
    main()
