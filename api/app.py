# A basic FastAPI app that has a single endpoint to retrieve bridge health data.

from fastapi import FastAPI, Query, HTTPException
from dotenv import load_dotenv
import os
import numpy as np
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text, inspect
from typing import cast
from settings import get_settings

# Initialize FastAPI app
app = FastAPI(title="Bridge Health API", version="0.1")

# ---- DB ----
def _engine():
    s = get_settings()
    if s.is_sqlite:
        db_path = s.resolved_db_path
        if db_path is None or not db_path.exists():
            raise RuntimeError(f"SQLite file not found: {db_path}")

    return create_engine(
        s.resolved_db_url,
        future=True,
        pool_pre_ping=True,
        connect_args={"check_same_thread": False},
    )
def retrieve_db_data() -> pd.DataFrame:
    """Read raw rows from DB and return a DataFrame with a UTC DatetimeIndex."""
    s = get_settings()
    eng = _engine()
    try:
        query = text(
            f"SELECT time, stress_cycle, pos_na "
            f"FROM {s.table_name} "
            f"ORDER BY time"
        )
        with eng.connect() as conn:
            df = pd.read_sql(query, conn, parse_dates=["time"])
        if df.empty:
            return df
    except Exception as e:
        schemas = inspect(eng).get_schema_names()
        msg = f"Could not connect/read DB. Schemas: {schemas}"
        raise HTTPException(status_code=500, detail=f"Database error: {e}\n\n{msg}")

    df["time"] = pd.to_datetime(df["time"], utc=True)
    df = df.set_index("time").sort_index()
    df["stress_cycle"] = pd.to_numeric(df["stress_cycle"], errors="coerce")
    df["pos_na"] = pd.to_numeric(df["pos_na"], errors="coerce")
    return df.dropna(subset=["stress_cycle", "pos_na"])

# ---- Processing helpers (DF in -> DF out) ----
def hampel(series: pd.Series, k: int = 7, nsigma: float = 3.0) -> pd.Series:
    """Robust outlier clipping using a Hampel-like MAD threshold."""
    med = series.rolling(window=k, center=True, min_periods=1).median()
    mad = (series - med).abs().rolling(window=k, center=True, min_periods=1).median()
    thresh = nsigma * 1.4826 * mad
    return series.clip(lower=(med - thresh), upper=(med + thresh))

def remove_outliers(df: pd.DataFrame, k: int = 7, nsigma: float = 3.0) -> pd.DataFrame:
    out = df.copy()
    out["stress_cycle"] = hampel(out["stress_cycle"], k=k, nsigma=nsigma)
    out["pos_na"] = hampel(out["pos_na"], k=k, nsigma=nsigma)
    return out

def downsample_time(df: pd.DataFrame, freq: str = "15min") -> pd.DataFrame:
    """Time-based downsampling with a robust aggregator."""
    if df.empty:
        return df
    # Validate freq early
    from pandas.tseries.frequencies import to_offset
    try:
        to_offset(freq)
    except Exception:
        raise HTTPException(status_code=422, detail=f"Invalid freq '{freq}'. Try 5min, 15min, 1H.")
    # Median is robust; drop all-empty bins afterwards
    agg = df.resample(freq, origin="start_day").median()
    return agg.dropna(how="all")

def smooth(df: pd.DataFrame, method: str = "ema", span: int = 5) -> pd.DataFrame:
    """EMA or rolling-median smoothing on downsampled data."""
    if df.empty:
        return df
    out = df.copy()
    method = (method or "ema").lower()
    if method == "ema":
        out["stress_cycle"] = out["stress_cycle"].ewm(span=span, adjust=False).mean()
        out["pos_na"] = out["pos_na"].ewm(span=span, adjust=False).mean()
    elif method == "rolling":
        out["stress_cycle"] = out["stress_cycle"].rolling(window=3, center=True, min_periods=1).median()
        out["pos_na"] = out["pos_na"].rolling(window=3, center=True, min_periods=1).median()
    else:
        raise HTTPException(status_code=422, detail="smooth must be 'ema' or 'rolling'")
    # Optional: drop leading NaNs if any
    return out.dropna(how="all")

def df_to_payload(df: pd.DataFrame) -> dict:
    idx = cast(pd.DatetimeIndex, df.index)          # tell Pylance the real type
    times = [ts.isoformat() for ts in idx.to_pydatetime()]
    return {
        "_time": times,
        "stress_cycle": df["stress_cycle"].astype(float).tolist(),
        "pos_na": df["pos_na"].astype(float).tolist(),
    }


@app.get("/bridge-data/")
def bridge_data(
    raw: bool = Query(False, description="Return raw data (no processing) if true"),
    freq: str = Query("15min", description="Resample frequency like '15min', '1H'"),
    smooth_method: str = Query("ema", description="'ema' or 'rolling'"),
    span: int = Query(5, ge=1, le=60, description="EMA span (only for ema)"),
):
    df = retrieve_db_data()
    if df.empty:
        return {"_time": [], "stress_cycle": [], "pos_na": []}

    if raw:
        return df_to_payload(df)

    # Processed: outlier removal -> downsample -> smooth
    df_clean = remove_outliers(df, k=7, nsigma=3.0)
    df_down = downsample_time(df_clean, freq=freq)
    df_smooth = smooth(df_down, method=smooth_method, span=span)
    return df_to_payload(df_smooth)

@app.get("/debug/config")
def debug_config():
    """
    Dev-only endpoint: confirms resolved paths and DB visibility.
    Enable with ENABLE_DEBUG_ENDPOINT=true in .env
    """
    s = get_settings()
    if not s.enable_debug_endpoint:
        raise HTTPException(status_code=404, detail="Not found")

    db_exists = s.resolved_db_path.exists() if s.resolved_db_path else None

    return {
        "project_root": str(s.project_root),
        "db_url_raw": s.db_url,
        "db_url_resolved": s.resolved_db_url,
        "db_path_exists": db_exists,
        "table_name": s.table_name,
    }