# A basic FastAPI app that has a single endpoint to retrieve bridge health data.

from fastapi import FastAPI, Query, HTTPException
from dotenv import load_dotenv
import os
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text

load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Bridge Health API", version="0.1")

# ---- DB ----
def _engine():
    db_url = os.getenv("DB_URL")
    if not db_url:
        raise RuntimeError("DB_URL is not set")
    return create_engine(db_url, future=True, pool_pre_ping=True)

def retrieve_db_data() -> pd.DataFrame:
    """Read raw rows from DB and return a DataFrame with a UTC DatetimeIndex."""
    eng = _engine()
    with eng.connect() as conn:
        df = pd.read_sql(
            text("SELECT time, stress_cycle, pos_na FROM midspan_data ORDER BY time"),
            conn,
            parse_dates=["time"],
        )
    if df.empty:
        return df
    # Ensure timezone-aware UTC index
    df["time"] = pd.to_datetime(df["time"], utc=True)
    df = df.set_index("time").sort_index()
    # Basic numeric hygiene
    df["stress_cycle"] = pd.to_numeric(df["stress_cycle"], errors="coerce")
    df["pos_na"] = pd.to_numeric(df["pos_na"], errors="coerce")
    df = df.dropna(subset=["stress_cycle", "pos_na"])
    return df

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
    """Convert DF with DatetimeIndex to the expected JSON payload."""
    return {
        "_time": [ts.isoformat() for ts in df.index.to_pydatetime()],
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