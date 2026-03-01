from fastapi import FastAPI

app = FastAPI(title="NDIS CRM API", version="0.1.0")


@app.get("/health")
async def health_check():
    return {"status": "ok"}
