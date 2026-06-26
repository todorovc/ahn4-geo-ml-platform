import io
import os
import boto3
import pandas as pd
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split

AWS_REGION = os.getenv("AWS_REGION", "eu-west-1")
RAW_BUCKET = os.getenv("RAW_BUCKET", "geo-ml-ahn")
FEATURE_PREFIX = os.getenv("FEATURE_PREFIX", "features/terrain_grid")
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "")
EXPERIMENT_NAME = os.getenv("MLFLOW_EXPERIMENT", "ahn4-terrain-risk")

FEATURE_COLUMNS = [
    "mean_elevation",
    "min_elevation",
    "max_elevation",
    "std_elevation",
    "mean_slope",
    "max_slope",
    "mean_aspect",
    "relief",
    "roughness",
]


def synthetic_label(df: pd.DataFrame) -> pd.Series:
    return ((df["mean_elevation"] < 2.5) & (df["mean_slope"] < 0.15)).astype(int)


def load_feature_frames():
    s3 = boto3.client("s3", region_name=AWS_REGION)
    objs = s3.list_objects_v2(Bucket=RAW_BUCKET, Prefix=FEATURE_PREFIX)
    frames = []
    for obj in objs.get("Contents", []):
        key = obj["Key"]
        if not key.endswith(".parquet"):
            continue
        response = s3.get_object(Bucket=RAW_BUCKET, Key=key)
        frames.append(pd.read_parquet(io.BytesIO(response["Body"].read())))
    if not frames:
        raise RuntimeError("No feature parquet files found")
    return pd.concat(frames, ignore_index=True)


def main():
    if MLFLOW_TRACKING_URI:
        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(EXPERIMENT_NAME)

    df = load_feature_frames().dropna(subset=FEATURE_COLUMNS)
    df["label"] = synthetic_label(df)

    X = df[FEATURE_COLUMNS]
    y = df["label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    with mlflow.start_run():
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=8,
            random_state=42,
        )
        model.fit(X_train, y_train)
        preds = model.predict(X_test)

        accuracy = accuracy_score(y_test, preds)
        f1 = f1_score(y_test, preds)

        mlflow.log_param("model_type", "RandomForestClassifier")
        mlflow.log_param("n_estimators", 100)
        mlflow.log_param("max_depth", 8)
        mlflow.log_metric("accuracy", accuracy)
        mlflow.log_metric("f1", f1)
        mlflow.sklearn.log_model(model, artifact_path="model")

        print({"accuracy": accuracy, "f1": f1, "rows": len(df)})


if __name__ == "__main__":
    main()
