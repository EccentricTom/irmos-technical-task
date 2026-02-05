# test_script.py
# Showcase the Bridge Health API: fetch processed (and optionally raw) data and plot.

import argparse
import requests
import pandas as pd
import matplotlib.pyplot as plt


def fetch_bridge_health_data(
    api_url: str, *, raw: bool, freq: str, smooth_method: str, span: int
) -> dict:
    params = {
        "raw": str(raw).lower(),  # FastAPI parses "true"/"false"
        "freq": freq,
        "smooth_method": smooth_method,
        "span": span,
    }
    r = requests.get(f"{api_url.rstrip('/')}/bridge-data/", params=params, timeout=15)
    r.raise_for_status()
    return r.json()


def to_dataframe(payload: dict) -> pd.DataFrame:
    if not payload or "_time" not in payload:
        return pd.DataFrame(columns=["time", "stress_cycle", "pos_na"]).set_index(
            "time"
        )
    df = pd.DataFrame(
        {
            "time": pd.to_datetime(payload["_time"], utc=True, errors="coerce"),
            "stress_cycle": payload["stress_cycle"],
            "pos_na": payload["pos_na"],
        }
    ).dropna(subset=["time"])
    return df.set_index("time").sort_index()


def plot_data(
    processed: pd.DataFrame, raw: pd.DataFrame | None = None, title_suffix: str = ""
):
    fig, axes = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
    ax1, ax2 = axes

    if raw is not None and not raw.empty:
        raw["stress_cycle"].plot(
            ax=ax1, color="#bbb", alpha=0.6, label="stress_cycle (raw)"
        )
        raw["pos_na"].plot(ax=ax2, color="#bbb", alpha=0.6, label="pos_na (raw)")

    if not processed.empty:
        processed["stress_cycle"].plot(
            ax=ax1, color="#2563eb", lw=1.8, label="stress_cycle (processed)"
        )
        processed["pos_na"].plot(
            ax=ax2, color="#ea580c", lw=1.8, label="pos_na (processed)"
        )

    ax1.set_title(f"Bridge Stress Cycle {title_suffix}")
    ax2.set_title(f"Bridge pos_na {title_suffix}")
    for ax in axes:
        ax.grid(True, alpha=0.3)
        ax.legend(loc="best")
        ax.set_xlabel("time")
    plt.tight_layout()
    plt.show()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default="http://localhost:8000", help="API base URL")
    ap.add_argument(
        "--freq", default="15min", help="Resample frequency, e.g. 5min, 15min, 1H"
    )
    ap.add_argument(
        "--smooth", default="ema", choices=["ema", "rolling"], help="Smoothing method"
    )
    ap.add_argument("--span", type=int, default=5, help="EMA span (only for ema)")
    ap.add_argument(
        "--overlay-raw", action="store_true", help="Overlay raw data for comparison"
    )
    args = ap.parse_args()

    try:
        processed_json = fetch_bridge_health_data(
            args.api,
            raw=False,
            freq=args.freq,
            smooth_method=args.smooth,
            span=args.span,
        )
        processed_df = to_dataframe(processed_json)

        raw_df = None
        if args.overlay_raw:
            raw_json = fetch_bridge_health_data(
                args.api,
                raw=True,
                freq=args.freq,
                smooth_method=args.smooth,
                span=args.span,
            )
            raw_df = to_dataframe(raw_json)

        suffix = f"(freq={args.freq}, smooth={args.smooth}, span={args.span})"
        plot_data(processed_df, raw_df, title_suffix=suffix)

    except requests.HTTPError as e:
        print(f"HTTP error: {e.response.status_code} → {e.response.text}")
    except requests.RequestException as e:
        print(f"Request failed: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
