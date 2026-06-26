from fastapi import FastAPI
app = FastAPI(title="AHN4 Inference API")
@app.get("/health")
def health():
    return {"status": "ok"}
