# A basic FastAPI app that has a single endpoint to retrieve bridge health data.

from fastapi import FastAPI, Query

# Initialize FastAPI app
app = FastAPI(title="Bridge Health API", version="0.1")

# helper function to downsample data
def downsample_data(data: dict, factor: int) -> dict:
    downsampled_data = {}
    for key, values in data.items():
        downsampled_data[key] = values[::factor]
    return downsampled_data

# Helper function to remove outliers from data
def remove_outliers(data: dict, threshold: float) -> dict:
    cleaned_data = {}
    for key, values in data.items():
        cleaned_data[key] = [v for v in values if abs(v) <= threshold]
    return cleaned_data

#Helper function to smooth data using rolling window calculations
def smooth_data(data: dict, window_size: int) -> dict:
    smoothed_data = {}
    for key, values in data.items():
        smoothed_values = []
        for i in range(len(values)):
            start_index = max(0, i - window_size // 2)
            end_index = min(len(values), i + window_size // 2 + 1)
            window = values[start_index:end_index]
            smoothed_values.append(sum(window) / len(window))
        smoothed_data[key] = smoothed_values
    return smoothed_data

# Endpoint to retrieve bridge health data from the database
@app.get("/bridge-health")
def get_bridge_health():
    bridge_health_data = {
        "_time": ["2023-01-01T00:00:00Z", "2023-01-01T01:00:00Z"],
        "stress_cycle": [100, 150],
        "pos_na": [0.5, 0.7],
    }
    return bridge_health_data