from sqlalchemy import create_engine, text, inspect
import os
from dotenv import load_dotenv
import pandas as pd

load_dotenv()


def _engine():
    db_url = os.getenv("DB_URL")
    if not db_url:
        raise RuntimeError("DB_URL is not set")
    return create_engine(db_url, future=True, pool_pre_ping=True)

def main():
    eng = _engine()
    try:
        with eng.connect() as conn:
            schemas = inspect(eng).get_schema_names()
            print(f"Schemas in the database: {schemas}")
            with eng.connect() as conn:
                df = pd.read_sql(
                    text("SELECT time, stress_cycle, pos_na FROM midspan_data ORDER BY time"),
                    conn,
                    parse_dates=["time"],
                )
            print(df.head())
    except Exception as e:
        print(f"Could not connect to DB. Error: {e}")

if __name__ == "__main__":
    main()