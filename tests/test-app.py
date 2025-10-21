# Test the functions in api.app.py
import pytest
from api.app import remove_outliers, smooth_data, calculate_outlier_threshold, downsample_data

def test_calculate_outlier_threshold():
    data = {
        "stress_cycle": [10, 12, 14, 1000, 16, 18],
        "pos_na": [0.1, 0.2, 0.15, 5.0, 0.18]
    }
    threshold_stress = calculate_outlier_threshold(data, "stress_cycle")
    threshold_pos_na = calculate_outlier_threshold(data, "pos_na")
    assert threshold_stress > 100  # Expecting a high threshold due to the outlier
    assert threshold_pos_na > 1.0   # Expecting a high threshold due to the outlier

def test_remove_outliers():
    data = {
        "_time": ["2023-01-01T00:00:00Z", "2023-01-01T01:00:00Z", "2023-01-01T02:00:00Z"],
        "stress_cycle": [10, 1000, 12],
        "pos_na": [0.1, 5.0, 0.15]
    }
    cleaned_data = remove_outliers(data)
    assert len(cleaned_data["stress_cycle"]) == 2  # One outlier removed
    assert len(cleaned_data["pos_na"]) == 2         # One outlier removed

def test_smooth_data():
    data = {
        "stress_cycle": [10, 20, 30, 40, 50],
        "pos_na": [1, 2, 3, 4, 5]
    }
    smoothed = smooth_data(data, window_size=3)
    assert smoothed["stress_cycle"][2] == pytest.approx(30.0)  # Average of 20,30,40
    assert smoothed["pos_na"][2] == pytest.approx(3.0)         # Average of 2,3,4

def test_downsample_data():
    data = {
        "stress_cycle": [10, 20, 30, 40, 50, 60],
        "pos_na": [1, 2, 3, 4, 5, 6]
    }
    downsampled = downsample_data(data, factor=2)
    assert downsampled["stress_cycle"] == [10, 30, 50]
    assert downsampled["pos_na"] == [1, 3, 5]