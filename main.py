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

# ---- CORS middleware ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://localhost:3000",
        os.getenv("FRONTEND_URL", "http://localhost:8000")
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Include routers ----
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(generate_router, prefix="/api/generate", tags=["generate"])
app.include_router(gallery_router, prefix="/api/gallery", tags=["gallery"])
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])
app.include_router(webhooks_router, prefix="/api/webhooks", tags=["webhooks"])

# ---- Health check ----
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
    return FileResponse("landing.html")

@app.get("/dashboard", response_class=FileResponse)
async def serve_dashboard():
    return FileResponse("dashboard.html")

@app.get("/admin", response_class=FileResponse)
async def serve_admin():
    return FileResponse("admin.html")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("ENV") == "development"
    )
