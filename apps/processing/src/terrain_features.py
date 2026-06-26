import numpy as np
import pandas as pd


def compute_slope_aspect(arr, pixel_size=0.5):
    gy, gx = np.gradient(arr, pixel_size)
    slope = np.sqrt(gx ** 2 + gy ** 2)
    aspect = np.arctan2(-gy, gx)
    return slope, aspect


def compute_relief(arr):
    return np.nanmax(arr) - np.nanmin(arr)


def compute_roughness(arr):
    return np.nanstd(arr)


def window_summary(window, slope_window, aspect_window):
    return {
        "mean_elevation": float(np.nanmean(window)),
        "min_elevation": float(np.nanmin(window)),
        "max_elevation": float(np.nanmax(window)),
        "std_elevation": float(np.nanstd(window)),
        "mean_slope": float(np.nanmean(slope_window)),
        "max_slope": float(np.nanmax(slope_window)),
        "mean_aspect": float(np.nanmean(aspect_window)),
        "relief": float(compute_relief(window)),
        "roughness": float(compute_roughness(window)),
    }


def build_grid_features(arr, slope, aspect, grid_size_pixels=100):
    rows = []
    h, w = arr.shape
    for r in range(0, h, grid_size_pixels):
        for c in range(0, w, grid_size_pixels):
            window = arr[r:r + grid_size_pixels, c:c + grid_size_pixels]
            slope_window = slope[r:r + grid_size_pixels, c:c + grid_size_pixels]
            aspect_window = aspect[r:r + grid_size_pixels, c:c + grid_size_pixels]
            if window.size == 0:
                continue
            record = window_summary(window, slope_window, aspect_window)
            record["grid_row"] = r
            record["grid_col"] = c
            rows.append(record)
    return pd.DataFrame(rows)
