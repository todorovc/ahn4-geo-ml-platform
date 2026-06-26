import os
import tempfile
import boto3
import pandas as pd
import rasterio
from terrain_features import compute_slope_aspect, build_grid_features

AWS_REGION = os.getenv("AWS_REGION", "eu-west-1")
RAW_BUCKET = os.getenv("RAW_BUCKET", "geo-ml-ahn")
RAW_PREFIX = os.getenv("RAW_PREFIX", "raw/ahn4/dsm")
PROCESSED_PREFIX = os.getenv("PROCESSED_PREFIX", "processed/ahn4/dsm-features")
FEATURE_PREFIX = os.getenv("FEATURE_PREFIX", "features/terrain_grid")
GRID_SIZE_METERS = int(os.getenv("GRID_SIZE_METERS", "50"))
TILE_ID_FILTER = os.getenv("TILE_ID_FILTER", "")


def write_raster_like(src, array, out_path):
    profile = src.profile.copy()
    profile.update(dtype="float32", count=1, compress="lzw")
    with rasterio.open(out_path, "w", **profile) as dst:
        dst.write(array.astype("float32"), 1)


def main():
    s3 = boto3.client("s3", region_name=AWS_REGION)
    objs = s3.list_objects_v2(Bucket=RAW_BUCKET, Prefix=RAW_PREFIX)
    contents = objs.get("Contents", [])
    if TILE_ID_FILTER:
        contents = [o for o in contents if TILE_ID_FILTER in o["Key"]]

    for obj in contents[:5]:
        key = obj["Key"]
        tile_name = key.split("/")[-1].replace(".tif", "")
        with tempfile.NamedTemporaryFile(suffix=".tif") as src_file, \
             tempfile.NamedTemporaryFile(suffix="_slope.tif") as slope_file, \
             tempfile.NamedTemporaryFile(suffix="_aspect.tif") as aspect_file, \
             tempfile.NamedTemporaryFile(suffix=".parquet") as feature_file:

            s3.download_file(RAW_BUCKET, key, src_file.name)

            with rasterio.open(src_file.name) as src:
                arr = src.read(1).astype("float32")
                nodata = src.nodata
                if nodata is not None:
                    arr[arr == nodata] = float("nan")

                pixel_size = abs(src.transform.a)
                grid_size_pixels = max(1, int(GRID_SIZE_METERS / pixel_size))

                slope, aspect = compute_slope_aspect(arr, pixel_size=pixel_size)
                write_raster_like(src, slope, slope_file.name)
                write_raster_like(src, aspect, aspect_file.name)

                features = build_grid_features(arr, slope, aspect, grid_size_pixels=grid_size_pixels)
                features["tile_name"] = tile_name
                features["source_key"] = key
                features.to_parquet(feature_file.name, index=False)

            s3.upload_file(slope_file.name, RAW_BUCKET, f"{PROCESSED_PREFIX}/{tile_name}_slope.tif")
            s3.upload_file(aspect_file.name, RAW_BUCKET, f"{PROCESSED_PREFIX}/{tile_name}_aspect.tif")
            s3.upload_file(feature_file.name, RAW_BUCKET, f"{FEATURE_PREFIX}/{tile_name}.parquet")
            print(f"processed {tile_name}")


if __name__ == "__main__":
    main()
