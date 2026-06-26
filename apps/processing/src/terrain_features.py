import numpy as np

def compute_basic_terrain_features(arr, pixel_size=0.5):
    gy, gx = np.gradient(arr, pixel_size)
    slope = np.sqrt(gx**2 + gy**2)
    aspect = np.arctan2(-gy, gx)
    return slope, aspect
