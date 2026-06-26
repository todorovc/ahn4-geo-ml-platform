import os, tempfile, boto3, rasterio, pandas as pd
from terrain_features import compute_basic_terrain_features
AWS_REGION=os.getenv("AWS_REGION","eu-west-1")
RAW_BUCKET=os.getenv("RAW_BUCKET","geo-ml-ahn")
RAW_PREFIX=os.getenv("RAW_PREFIX","raw/ahn4/dsm")
FEATURE_PREFIX=os.getenv("FEATURE_PREFIX","features/terrain_grid")
def main():
    s3=boto3.client("s3", region_name=AWS_REGION)
    objs=s3.list_objects_v2(Bucket=RAW_BUCKET, Prefix=RAW_PREFIX)
    for obj in objs.get("Contents", [])[:3]:
        key=obj["Key"]
        with tempfile.NamedTemporaryFile(suffix=".tif") as f:
            s3.download_file(RAW_BUCKET, key, f.name)
            with rasterio.open(f.name) as src:
                arr=src.read(1)
                slope, aspect=compute_basic_terrain_features(arr)
                df=pd.DataFrame({"mean_elevation":[float(arr.mean())],"mean_slope":[float(slope.mean())],"mean_aspect":[float(aspect.mean())],"source_key":[key]})
                out_key=f"{FEATURE_PREFIX}/{key.split('/')[-1].replace('.tif','.parquet')}"
                with tempfile.NamedTemporaryFile(suffix=".parquet") as out:
                    df.to_parquet(out.name, index=False)
                    s3.upload_file(out.name, RAW_BUCKET, out_key)
                    print(f"uploaded features for {key}")
if __name__ == "__main__":
    main()
