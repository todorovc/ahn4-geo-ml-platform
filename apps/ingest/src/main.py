import csv
import io
import os
import re
import sys
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urlparse

import boto3
import requests

AWS_REGION = os.getenv("AWS_REGION", "eu-west-1")
RAW_BUCKET = os.getenv("RAW_BUCKET", "geo-ml-ahn")
RAW_PREFIX = os.getenv("RAW_PREFIX", "raw/ahn4/dsm").strip("/")
AHN_TILE_LIST_URL = os.getenv("AHN_TILE_LIST_URL", "")
AHN_TILE_URLS = os.getenv("AHN_TILE_URLS", "")
MAX_TILES = int(os.getenv("MAX_TILES", "0"))
OVERWRITE = os.getenv("OVERWRITE", "false").lower() == "true"
TIMEOUT_SECONDS = int(os.getenv("DOWNLOAD_TIMEOUT_SECONDS", "600"))

@dataclass(frozen=True)
class Tile:
    tile_id: str
    url: str


def safe_tile_id(url: str, fallback: str) -> str:
    name = os.path.basename(urlparse(url).path) or fallback
    name = re.sub(r"\.(tif|tiff|zip)$", "", name, flags=re.I)
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", name)[:160]


def tiles_from_csv(url: str) -> Iterable[Tile]:
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    reader = csv.DictReader(io.StringIO(resp.text))
    for i, row in enumerate(reader):
        tile_url = row.get("url") or row.get("download_url") or row.get("href")
        if not tile_url:
            continue
        tile_id = row.get("tile_id") or row.get("id") or row.get("name") or safe_tile_id(tile_url, f"tile_{i}")
        yield Tile(tile_id=safe_tile_id(tile_id, f"tile_{i}"), url=tile_url)


def tiles_from_env() -> Iterable[Tile]:
    for i, tile_url in enumerate([u.strip() for u in AHN_TILE_URLS.split(",") if u.strip()]):
        yield Tile(tile_id=safe_tile_id(tile_url, f"tile_{i}"), url=tile_url)


def s3_exists(s3, key: str) -> bool:
    try:
        s3.head_object(Bucket=RAW_BUCKET, Key=key)
        return True
    except Exception:
        return False


def upload_stream(s3, tile: Tile) -> None:
    ext = os.path.splitext(urlparse(tile.url).path)[1].lower() or ".tif"
    key = f"{RAW_PREFIX}/{tile.tile_id}{ext}"
    if not OVERWRITE and s3_exists(s3, key):
        print(f"skip existing s3://{RAW_BUCKET}/{key}")
        return
    with requests.get(tile.url, stream=True, timeout=TIMEOUT_SECONDS) as resp:
        resp.raise_for_status()
        s3.upload_fileobj(resp.raw, RAW_BUCKET, key)
    print(f"uploaded {tile.tile_id} -> s3://{RAW_BUCKET}/{key}")


def main() -> int:
    tiles = list(tiles_from_csv(AHN_TILE_LIST_URL)) if AHN_TILE_LIST_URL else list(tiles_from_env())
    if MAX_TILES > 0:
        tiles = tiles[:MAX_TILES]
    if not tiles:
        raise RuntimeError("Set AHN_TILE_LIST_URL to a CSV with url/download_url/href, or AHN_TILE_URLS to comma-separated tile URLs")
    s3 = boto3.client("s3", region_name=AWS_REGION)
    for tile in tiles:
        upload_stream(s3, tile)
    print({"uploaded_or_skipped": len(tiles)})
    return 0

if __name__ == "__main__":
    sys.exit(main())
