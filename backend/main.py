from fastapi import FastAPI

from app.routers.participants import router as participants_router

app = FastAPI(title="NDIS CRM API", version="0.1.0")

app.include_router(participants_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok"}
