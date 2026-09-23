"""
LUCOST AI - FastAPI Backend
Complete production-ready video generation platform backend
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

load_dotenv()

# Import routers
from .routers import auth, generate, gallery, admin_router, webhooks

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
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(generate.router, prefix="/api/generate", tags=["generate"])
app.include_router(gallery.router, prefix="/api/gallery", tags=["gallery"])
app.include_router(admin_router.router, prefix="/api/admin", tags=["admin"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["webhooks"])

# ---- Health check ----
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "LUCOST AI Backend",
        "version": "1.0.0"
    }

# ---- Root endpoint (serves frontend) ----
@app.get("/")
async def root():
    return {
        "message": "LUCOST AI Backend",
        "docs": "/docs",
        "frontend": "/landing"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("ENV") == "development"
    )
