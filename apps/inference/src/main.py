import os
from typing import Dict, List

import mlflow.pyfunc
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

MODEL_URI = os.getenv("MODEL_URI", "models:/ahn4-terrain-risk/Production")
FEATURE_COLUMNS = [
    "mean_elevation", "min_elevation", "max_elevation", "std_elevation",
    "mean_slope", "max_slope", "mean_aspect", "relief", "roughness",
]

app = FastAPI(title="AHN4 Terrain Risk Inference", version="0.1.0")
_model = None

class FeatureVector(BaseModel):
    mean_elevation: float
    min_elevation: float
    max_elevation: float
    std_elevation: float = Field(ge=0)
    mean_slope: float
    max_slope: float
    mean_aspect: float
    relief: float
    roughness: float

class PredictRequest(BaseModel):
    rows: List[FeatureVector]

@app.on_event("startup")
def load_model() -> None:
    global _model
    _model = mlflow.pyfunc.load_model(MODEL_URI)

@app.get("/healthz")
def healthz() -> Dict[str, str]:
    return {"status": "ok", "model_uri": MODEL_URI}

@app.post("/predict")
def predict(req: PredictRequest) -> Dict[str, object]:
    if _model is None:
        raise HTTPException(status_code=503, detail="model is not loaded")
    df = pd.DataFrame([r.dict() for r in req.rows], columns=FEATURE_COLUMNS)
    preds = _model.predict(df)
    return {"predictions": [int(x) if float(x).is_integer() else float(x) for x in preds]}
