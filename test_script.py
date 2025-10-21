# This script showcases how the API is utilised.
# It gets the bridge health data from the api and visualises it
# This imitates a frontend experience of fetching data from the API

import requests
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np


def fetch_bridge_health_data(api_url: str, params: dict) -> dict:
    response = requests.get(f"{api_url}/bridge-data/", params=params)
    response.raise_for_status()
    return response.json()

def plot_stress_cycle(data: dict):
    times = pd.to_datetime(data["_time"])
    stress_cycles = data["stress_cycle"]

    plt.figure(figsize=(10, 5))
    plt.plot(times, stress_cycles, marker='o')
    plt.title("Bridge Stress Cycle Over Time")
    plt.xlabel("Time")
    plt.ylabel("Stress Cycle")
    plt.grid(True)
    plt.show()

def plot_pos_na(data: dict):
    times = pd.to_datetime(data["_time"])
    pos_na = data["pos_na"]

    plt.figure(figsize=(10, 5))
    plt.plot(times, pos_na, marker='o', color='orange')
    plt.title("Bridge Position NA Over Time")
    plt.xlabel("Time")
    plt.ylabel("Position NA")
    plt.grid(True)
    plt.show()


if __name__ == "__main__":
    api_url = "http://localhost:8000"
    params = {
        "frequency": "15min",
        "smooth_data": "ema",
        "downsample_factor": 5
    }
    data = fetch_bridge_health_data(api_url, params)
    plot_stress_cycle(data)
    plot_pos_na(data)