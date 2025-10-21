# load the contents of "midspan_data.csv" into the "midspan_data" table in a postgresql database

import pandas as pd
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    insert,
    select,
)
from sqlalchemy.orm import Session

metadata = MetaData()

features = Table(
    "features",
    metadata,
    Column("timestamp", DateTime()),
    Column("Fat_cycle_bot", Float()),
    Column("Pos_na", Float())
)

Index("idx_timestamp", features.c.timestamp)

def make_engine(db_url: str):
    return create_engine(db_url, future=True, pool_pre_ping=True)

def init_db(engine):
    metadata.create_all(engine)

def insert_features(engine, rows: list(dict), features: Table):
    with Session(engine) as s:
        s.execute(insert(features), rows)
        s.commit()



def load_csv_to_db(csv_file, db_connection_string, table_name):
    # Read the CSV file into a DataFrame
    df = pd.read_csv(csv_file)

    # Create a database engine
    engine = create_engine(db_connection_string)

    # Load the DataFrame into the database table
    df.to_sql(table_name, engine, if_exists='replace', index=False)

    print(f"Data from {csv_file} has been loaded into the {table_name} table.")