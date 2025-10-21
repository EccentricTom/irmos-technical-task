# load the contents of "midspan_data.csv" into the "midspan_data" table in a postgresql database
import argparse

import pandas as pd
from sqlalchemy import (
    create_engine,
    text,
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument(
        "--db", required=True
    )  # e.g. postgresql+psycopg://user:pw@db:5432/irmosdb
    ap.add_argument("--table", default="midspan_data")
    ap.add_argument("--mode", choices=["replace", "append"], default="replace")
    args = ap.parse_args()

    # Read + normalize
    df = pd.read_csv(args.csv).rename(
        columns={
            "time": "time",
            "Fat_cycle_bot": "stress_cycle",
            "Pos_na": "pos_na",
        }
    )
    df["time"] = pd.to_datetime(df["time"], utc=True, errors="coerce")
    df["stress_cycle"] = pd.to_numeric(df["stress_cycle"], errors="coerce")
    df["pos_na"] = pd.to_numeric(df["pos_na"], errors="coerce")
    df = df.dropna(subset=["time"]).sort_values("time")

    engine = create_engine(args.db, future=True)

    ddl = f"""
    CREATE TABLE IF NOT EXISTS {args.table} (
      time TIMESTAMPTZ NOT NULL,
      stress_cycle DOUBLE PRECISION,
      pos_na DOUBLE PRECISION
    );"""
    idx = f"CREATE INDEX IF NOT EXISTS idx_{args.table}_time ON {args.table} (time);"

    with engine.begin() as conn:
        conn.execute(text(ddl))
        if args.mode == "replace":
            conn.execute(text(f"TRUNCATE TABLE {args.table};"))
        # No dtype= → no Pylance error
        df.to_sql(
            args.table,
            conn,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=10_000,
        )
        conn.execute(text(idx))

    print(f"Loaded {len(df)} rows into '{args.table}' ({args.mode}).")


if __name__ == "__main__":
    main()
