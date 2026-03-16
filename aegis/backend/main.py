from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from proxy.router import router as proxy_router
# from api.dashboard import router as dashboard_router
# from api.admin import router as admin_router

app = FastAPI(
    title="AEGIS — AI Governance Proxy Hub",
    description="An intelligent proxy layer that intercepts, inspects, and governs LLM traffic.",
    version="0.1.0",
)

# NOTE: All origins are permitted for hackathon development.
# Restrict `allow_origins` to specific domains before deploying to production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register the proxy router at root level so the path becomes /v1/chat/completions
app.include_router(proxy_router, prefix="", tags=["Proxy"])
# app.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
# app.include_router(admin_router, prefix="/admin", tags=["Admin"])


@app.get("/", tags=["Health"])
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "service": "AEGIS"}
