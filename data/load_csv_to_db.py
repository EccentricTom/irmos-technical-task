# load the contents of "midspan_data.csv" into the "midspan_data" table in a postgresql database
import pandas as pd
from sqlalchemy import (
    create_engine,
    text,
)
from sqlalchemy.engine import Engine
from dotenv import load_dotenv
import os

load_dotenv()


def normalise_df(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df = df.rename(
        columns={"time": "time", "Fat_cycle_bot": "stress_cycle", "Pos_na": "pos_na"}
    )
    df["time"] = pd.to_datetime(df["time"], utc=True, errors="coerce")
    df["stress_cycle"] = pd.to_numeric(df["stress_cycle"], errors="coerce")
    df["pos_na"] = pd.to_numeric(df["pos_na"], errors="coerce")
    df = df.dropna(subset=["time"]).sort_values("time")
    return df


def write_df(df: pd.DataFrame, engine: Engine, table, mode):
    dialect = engine.dialect.name
    with engine.begin() as conn:
        if dialect == "sqlite":
            tosql_mode = "replace" if mode == "replace" else "append"
            df.to_sql(
                table,
                conn,
                if_exists=tosql_mode,
                index=False,
                method="multi",
                chunksize=10000,
            )
            conn.execute(
                text(f"CREATE INDEX IF NOT EXISTS idx{table}_time ON {table}(time);")
            )
        else:
            pass


def main():
    csv_path = os.getenv("CSV_PATH")
    db = os.getenv("DB_URL")
    table = os.getenv("TABLE_NAME")
    mode = os.getenv("MODE_DB")

    df = normalise_df(csv_path)
    engine = create_engine(db, future=True, pool_pre_ping=True)

    write_df(df, engine, table, mode)


if __name__ == "__main__":
    main()
