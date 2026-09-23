"""
Configuration and environment variables
"""

import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ---- App ----
    APP_NAME: str = "LUCOST AI"
    ENV: str = os.getenv("ENV", "development")
    DEBUG: bool = ENV == "development"
    
    # ---- Database ----
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/lucost")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # ---- Auth ----
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    FIREBASE_PROJECT_ID: str = os.getenv("FIREBASE_PROJECT_ID", "")
    FIREBASE_PRIVATE_KEY: str = os.getenv("FIREBASE_PRIVATE_KEY", "")
    FIREBASE_CLIENT_EMAIL: str = os.getenv("FIREBASE_CLIENT_EMAIL", "")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-super-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # ---- Payment Processors ----
    LEMON_SQUEEZY_API_KEY: str = os.getenv("LEMON_SQUEEZY_API_KEY", "")
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
    FASTSPRING_API_KEY: str = os.getenv("FASTSPRING_API_KEY", "")
    PAYSTACK_SECRET_KEY: str = os.getenv("PAYSTACK_SECRET_KEY", "")
    FLUTTERWAVE_SECRET_KEY: str = os.getenv("FLUTTERWAVE_SECRET_KEY", "")
    
    # ---- GPU / Rendering ----
    RUNPOD_API_KEY: str = os.getenv("RUNPOD_API_KEY", "")
    RUNPOD_ENDPOINT_ID: str = os.getenv("RUNPOD_ENDPOINT_ID", "")
    PULID_API_KEY: str = os.getenv("PULID_API_KEY", "")
    
    # ---- Storage ----
    S3_ACCESS_KEY: str = os.getenv("S3_ACCESS_KEY", "")
    S3_SECRET_KEY: str = os.getenv("S3_SECRET_KEY", "")
    S3_BUCKET: str = os.getenv("S3_BUCKET", "lucost-videos")
    S3_REGION: str = os.getenv("S3_REGION", "us-east-1")
    
    R2_ACCESS_KEY: str = os.getenv("R2_ACCESS_KEY", "")
    R2_SECRET_KEY: str = os.getenv("R2_SECRET_KEY", "")
    R2_BUCKET: str = os.getenv("R2_BUCKET", "lucost-videos")
    R2_ACCOUNT_ID: str = os.getenv("R2_ACCOUNT_ID", "")
    
    STORAGE_PROVIDER: str = os.getenv("STORAGE_PROVIDER", "r2")  # "s3" or "r2"
    
    # ---- Admin ----
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@lucost.ai")
    ADMIN_PASSWORD_HASH: str = os.getenv("ADMIN_PASSWORD_HASH", "")
    
    # ---- Encryption ----
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "default-key-change-in-production")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

# ---- Tier definitions (locked) ----
TIERS = {
    "tier_1": {
        "name": "Quick Clips",
        "price_usd": 21.00,
        "strike_price_usd": 35.00,
        "generations_per_month": 20,
        "max_duration_seconds": 300,  # 5 minutes
        "max_duration_label": "5 min"
    },
    "tier_2": {
        "name": "Medium Form",
        "price_usd": 35.00,
        "strike_price_usd": 50.00,
        "generations_per_month": 15,
        "max_duration_seconds": 780,  # 13 minutes
        "max_duration_label": "15 min"
    },
    "tier_3": {
        "name": "Long Form",
        "price_usd": 75.00,
        "strike_price_usd": 95.00,
        "generations_per_month": 10,
        "max_duration_seconds": 1620,  # 27 minutes
        "max_duration_label": "30 min"
    }
}

STYLES = [
    "Narration Anime",
    "Narration Drama",
    "Drama",
    "Drama Anime",
    "CGI Idol",
    "Cinematic 3D",
    "Others"
]

ASPECT_RATIOS = ["9:16", "1:1", "16:9"]

# ---- Cost model (per-tier baseline) ----
GPU_COST_PER_HOUR = 0.35
TIER_BASE_COST = {
    "tier_1": 11.43,  # 5-min video
    "tier_2": 25.71,  # 15-min video
    "tier_3": 34.29   # 30-min video
}

TRIAL_GENERATIONS = 2
TRIAL_DURATION_SECONDS = 30
