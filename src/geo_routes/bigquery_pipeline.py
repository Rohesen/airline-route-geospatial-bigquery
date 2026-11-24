"""Load the cleaned CSVs into BigQuery and run the GIS SQL in order.

Usage:
    python src/geo_routes/bigquery_pipeline.py --project YOUR_PROJECT_ID

Works with the free BigQuery sandbox. Authenticate first with:
    gcloud auth application-default login
"""
import argparse
from pathlib import Path

from google.cloud import bigquery

ROOT = Path(__file__).resolve().parents[2]
CLEAN_DIR = ROOT / "data" / "clean"
SQL_DIR = ROOT / "sql"
RESULTS_DIR = ROOT / "docs" / "bigquery_results"

AIRPORTS_SCHEMA = [
    bigquery.SchemaField("airport_id", "INT64"),
    bigquery.SchemaField("iata", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("icao", "STRING"),
    bigquery.SchemaField("name", "STRING"),
    bigquery.SchemaField("city", "STRING"),
    bigquery.SchemaField("country", "STRING"),
    bigquery.SchemaField("latitude", "FLOAT64", mode="REQUIRED"),
    bigquery.SchemaField("longitude", "FLOAT64", mode="REQUIRED"),
    bigquery.SchemaField("altitude_ft", "INT64"),
    bigquery.SchemaField("timezone", "STRING"),
]
ROUTES_SCHEMA = [
    bigquery.SchemaField("airline", "STRING"),
    bigquery.SchemaField("source_iata", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("dest_iata", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("codeshare", "BOOL"),
    bigquery.SchemaField("equipment", "STRING"),
]

# Files that build tables; everything else is an analysis query whose result is saved.
BUILD_STEPS = {"01_airports_geo.sql", "02_routes_geo.sql"}


def load_csv(client: bigquery.Client, table_id: str, path: Path, schema) -> None:
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )
    with path.open("rb") as f:
        client.load_table_from_file(f, table_id, job_config=job_config).result()
    print(f"Loaded {client.get_table(table_id).num_rows:,} rows into {table_id}")


def run(project: str, dataset: str, location: str) -> None:
    client = bigquery.Client(project=project)
    ds = bigquery.Dataset(f"{project}.{dataset}")
    ds.location = location
    client.create_dataset(ds, exists_ok=True)

    load_csv(client, f"{project}.{dataset}.airports_raw", CLEAN_DIR / "airports.csv", AIRPORTS_SCHEMA)
    load_csv(client, f"{project}.{dataset}.routes_raw", CLEAN_DIR / "routes.csv", ROUTES_SCHEMA)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    for sql_file in sorted(SQL_DIR.glob("*.sql")):
        sql = sql_file.read_text().format(project=project, dataset=dataset)
        print(f"Running {sql_file.name} ...")
        job = client.query(sql)
        if sql_file.name in BUILD_STEPS:
            job.result()
            continue
        df = job.to_dataframe()
        geo_cols = [c for c in df.columns if c in ("route_line", "cluster_centre", "cluster_area")]
        df.drop(columns=geo_cols).to_csv(RESULTS_DIR / f"{sql_file.stem}.csv", index=False)
        print(df.drop(columns=geo_cols).head(10).to_string(index=False))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, help="Google Cloud project ID")
    parser.add_argument("--dataset", default="airline_geo")
    parser.add_argument("--location", default="US")
    args = parser.parse_args()
    run(args.project, args.dataset, args.location)


if __name__ == "__main__":
    main()
