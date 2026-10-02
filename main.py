"""
LUCOST AI - FastAPI Backend
Complete production-ready video generation platform backend
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

load_dotenv()

# Import routers
from routers import auth_router, generate_router, gallery_router, admin_router, webhooks_router

# ---- Lifespan manager ----
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting LUCOST AI backend...")
    yield
    # Shutdown
    print("Shutting down LUCOST AI backend...")

# ---- Initialize FastAPI app ----
app = FastAPI(
    title="LUCOST AI Backend",
    description="AI-powered short-form video generation platform",
    version="1.0.0",
    lifespan=lifespan
)

# ---- CORS Middleware Configuration ----
# Dynamically pull production origins alongside local defaults
allowed_origins = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:3000",
]

env_frontend = os.getenv("FRONTEND_URL")
render_url = os.getenv("RENDER_EXTERNAL_URL")

if env_frontend:
    allowed_origins.append(env_frontend.rstrip("/"))
if render_url:
    allowed_origins.append(render_url.rstrip("/"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if os.getenv("ENV") != "development" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Include API Routers ----
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(generate_router, prefix="/api/generate", tags=["generate"])
app.include_router(gallery_router, prefix="/api/gallery", tags=["gallery"])
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])
app.include_router(webhooks_router, prefix="/api/webhooks", tags=["webhooks"])

# ---- Health Check Endpoint ----
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "LUCOST AI Backend",
        "version": "1.0.0"
    }

# ---- Serve Frontend Pages ----
@app.get("/", response_class=FileResponse)
async def serve_landing():
    if os.path.exists("landing.html"):
        return FileResponse("landing.html")
    raise HTTPException(status_code=404, detail="landing.html not found")

@app.get("/dashboard", response_class=FileResponse)
async def serve_dashboard():
    if os.path.exists("dashboard.html"):
        return FileResponse("dashboard.html")
    raise HTTPException(status_code=404, detail="dashboard.html not found")

@app.get("/admin", response_class=FileResponse)
async def serve_admin():
    if os.path.exists("admin.html"):
        return FileResponse("admin.html")
    raise HTTPException(status_code=404, detail="admin.html not found")

# ---- Mount Static Assets (Optional) ----
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("ENV") == "development"
    )
