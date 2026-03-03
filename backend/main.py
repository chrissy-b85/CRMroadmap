from fastapi import FastAPI

from app.routers.invoices import router as invoices_router
from app.routers.participants import router as participants_router
from app.routers.plans import router as plans_router
from app.routers.providers import router as providers_router
from app.routers.support_categories import router as support_categories_router

app = FastAPI(title="NDIS CRM API", version="0.1.0")

app.include_router(participants_router, prefix="/api/v1")
app.include_router(plans_router, prefix="/api/v1")
app.include_router(invoices_router, prefix="/api/v1")
app.include_router(providers_router, prefix="/api/v1")
app.include_router(support_categories_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok"}
