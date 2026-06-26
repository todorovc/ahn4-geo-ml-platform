import os, io, requests, boto3, pandas as pd
AWS_REGION=os.getenv("AWS_REGION","eu-west-1")
RAW_BUCKET=os.getenv("RAW_BUCKET","geo-ml-ahn")
RAW_PREFIX=os.getenv("RAW_PREFIX","raw/ahn4/dsm")
AHN_TILE_LIST_URL=os.getenv("AHN_TILE_LIST_URL","")
def main():
    if not AHN_TILE_LIST_URL:
        raise RuntimeError("AHN_TILE_LIST_URL is required")
    s3=boto3.client("s3", region_name=AWS_REGION)
    resp=requests.get(AHN_TILE_LIST_URL, timeout=60)
    resp.raise_for_status()
    df=pd.read_csv(io.StringIO(resp.text))
    for _, row in df.head(5).iterrows():
        tile_url=row.get("url")
        tile_id=row.get("tile_id","unknown_tile")
        if not tile_url:
            continue
        file_resp=requests.get(tile_url, timeout=300)
        file_resp.raise_for_status()
        s3.put_object(Bucket=RAW_BUCKET, Key=f"{RAW_PREFIX}/{tile_id}.tif", Body=file_resp.content)
        print(f"uploaded {tile_id}")
if __name__ == "__main__":
    main()
