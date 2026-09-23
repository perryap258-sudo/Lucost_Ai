"""
Complete API routers: authentication, generation, gallery, admin, webhooks
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List
import uuid
import json
import requests

from .models_db import (
    User, Job, Subscription, AdminUser, APISettings, GPUSettings,
    PricingTier, Whitelist, FraudLog, ContentUpload, JobStatus,
    get_db
)
from config import settings, TIERS, STYLES

# ==========================================
# AUTH ROUTER - User & Admin Authentication
# ==========================================

auth_router = APIRouter()

class LoginRequest:
    email: str
    password: str

class SignupRequest:
    email: str
    password: str

@auth_router.post("/login/user")
async def login_user(email: str, password: str, db: Session = Depends(get_db)):
    """
    User login - uses Firebase
    Frontend calls: POST /api/auth/login/user
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return {
        "user_id": user.id,
        "email": user.email,
        "subscription_tier": user.subscription_tier,
        "trials_remaining": user.trials_remaining,
        "firebase_token": "token_from_firebase"  # In production, Firebase SDK handles this
    }

@auth_router.post("/login/admin")
async def login_admin(email: str, password: str, db: Session = Depends(get_db)):
    """
    Admin/Manager login - uses Supabase
    Frontend calls: POST /api/auth/login/admin
    """
    admin = db.query(AdminUser).filter(AdminUser.email == email).first()
    if not admin:
        raise HTTPException(status_code=401, detail="Invalid admin credentials")
    
    return {
        "admin_id": admin.id,
        "email": admin.email,
        "role": admin.role,
        "supabase_token": "token_from_supabase"
    }

@auth_router.post("/signup")
async def signup_user(email: str, password: str, db: Session = Depends(get_db)):
    """
    User registration
    Frontend calls: POST /api/auth/signup
    """
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = User(
        id=str(uuid.uuid4()),
        email=email,
        subscription_tier="trial",
        trials_remaining=2
    )
    db.add(new_user)
    db.commit()
    
    return {
        "user_id": new_user.id,
        "email": new_user.email,
        "message": "Account created successfully"
    }

# ==========================================
# GENERATE ROUTER - Video Generation
# ==========================================

generate_router = APIRouter()

class GenerateRequest:
    user_id: str
    script: str
    style: str
    aspect_ratio: str
    characters: List[dict]  # [{name, photo_url, voice_url, variations}]
    music: dict  # {url, volume}

@generate_router.post("/")
async def submit_generation(
    user_id: str,
    script: str,
    style: str,
    aspect_ratio: str = "9:16",
    characters: str = "[]",
    music: str = "{}",
    db: Session = Depends(get_db)
):
    """
    Submit video generation job
    Frontend calls: POST /api/generate with form data
    
    Returns: {job_id, status, message}
    """
    
    # ---- Validate user ----
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # ---- Validate required fields ----
    if not script or not style or not characters or characters == "[]":
        raise HTTPException(
            status_code=400,
            detail="Missing required: script, style, and at least 1 character with name, photo, voice"
        )
    
    # ---- Check for whitelist (free unlimited) ----
    is_whitelisted = db.query(Whitelist).filter(Whitelist.email == user.email).first()
    
    # ---- Check trial or subscription ----
    can_generate = False
    has_watermark = False
    
    if is_whitelisted:
        can_generate = True
    elif user.subscription_tier == "trial":
        if user.trials_remaining > 0:
            can_generate = True
            has_watermark = True
            user.trials_remaining -= 1
    else:
        # Paid subscription - check gens remaining
        sub = db.query(Subscription).filter(
            Subscription.user_id == user.id,
            Subscription.is_active == True
        ).first()
        
        if sub and sub.gens_used < sub.gens_allowed:
            can_generate = True
            sub.gens_used += 1
        else:
            # Log fraud attempt
            log_fraud(db, user.email, "non_subscriber", f"Attempted generation without valid subscription")
            raise HTTPException(status_code=403, detail="No subscriptions or generations remaining")
    
    if not can_generate:
        log_fraud(db, user.email, "non_subscriber", "Attempted generation without valid tier")
        raise HTTPException(status_code=403, detail="Not eligible for generation")
    
    # ---- Validate duration (script word count proxy) ----
    words = len(script.split())
    tier_map = {
        "trial": 30,  # 30 seconds
        "tier_1": 300,  # 5 minutes
        "tier_2": 900,  # 15 minutes
        "tier_3": 1800  # 30 minutes
    }
    max_seconds = tier_map.get(user.subscription_tier, 30)
    est_seconds = (words / 30) * 30  # ~30 words per 30 seconds
    
    if est_seconds > max_seconds:
        raise HTTPException(
            status_code=400,
            detail=f"Script too long. Est. {est_seconds:.0f}sec, max {max_seconds}sec for your tier"
        )
    
    # ---- Create job ----
    job = Job(
        id=str(uuid.uuid4()),
        user_id=user.id,
        status="processing",
        script=script,
        style=style,
        aspect_ratio=aspect_ratio,
        characters=characters,
        music=music,
        has_watermark=has_watermark
    )
    
    # ---- Get GPU count from admin settings ----
    gpu_setting = db.query(GPUSettings).filter(
        GPUSettings.tier == user.subscription_tier
    ).first()
    gpu_count = gpu_setting.gpu_count if gpu_setting else 8
    job.gpu_count_used = gpu_count
    
    db.add(job)
    db.commit()
    
    # ---- Send to RunPod queue (simulated here) ----
    # In production, this would call RunPod API
    # For now, just mark as processing and simulate completion after delay
    
    return {
        "job_id": job.id,
        "status": "processing",
        "message": "Generation might take time — you can leave, generation will still continue and be sent to your Gallery."
    }

# ==========================================
# GALLERY ROUTER - Jobs & Videos
# ==========================================

gallery_router = APIRouter()

@gallery_router.get("/")
async def get_gallery(user_id: str, db: Session = Depends(get_db)):
    """
    Get all jobs for a user
    Frontend calls: GET /api/gallery?user_id=xyz
    """
    jobs = db.query(Job).filter(Job.user_id == user_id).order_by(Job.created_at.desc()).all()
    
    return {
        "jobs": [
            {
                "id": job.id,
                "status": job.status,
                "script_preview": job.script[:50] + "..." if len(job.script) > 50 else job.script,
                "style": job.style,
                "video_url": job.video_url,
                "watermark": job.has_watermark,
                "created_at": job.created_at.isoformat(),
                "completed_at": job.completed_at.isoformat() if job.completed_at else None
            }
            for job in jobs
        ]
    }

@gallery_router.get("/{job_id}")
async def get_job(job_id: str, db: Session = Depends(get_db)):
    """
    Get specific job details
    Frontend calls: GET /api/gallery/{job_id}
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "id": job.id,
        "status": job.status,
        "script": job.script,
        "style": job.style,
        "video_url": job.video_url,
        "watermark": job.has_watermark,
        "created_at": job.created_at.isoformat(),
        "completed_at": job.completed_at.isoformat() if job.completed_at else None
    }

# ==========================================
# ADMIN ROUTER - Dashboard APIs
# ==========================================

admin_router = APIRouter()

@admin_router.get("/overview")
async def get_overview(admin_id: str, db: Session = Depends(get_db)):
    """
    Admin dashboard overview
    Frontend calls: GET /api/admin/overview
    """
    total_users = db.query(User).count()
    total_jobs = db.query(Job).count()
    total_revenue = db.query(PaymentEvent).filter(PaymentEvent.status == "completed").count()
    
    return {
        "total_users": total_users,
        "total_jobs": total_jobs,
        "total_revenue": total_revenue,
        "revenue_amount": 0,  # Would calculate from actual payment events
        "profit": 0  # Would calculate from revenue - costs
    }

@admin_router.put("/settings/gpu")
async def update_gpu_settings(tier: str, gpu_count: int, db: Session = Depends(get_db)):
    """
    Update GPU allocation for tier
    Frontend calls: PUT /api/admin/settings/gpu?tier=tier_1&gpu_count=8
    """
    setting = db.query(GPUSettings).filter(GPUSettings.tier == tier).first()
    if setting:
        setting.gpu_count = gpu_count
    else:
        setting = GPUSettings(id=str(uuid.uuid4()), tier=tier, gpu_count=gpu_count)
        db.add(setting)
    
    db.commit()
    return {"tier": tier, "gpu_count": gpu_count, "message": "Updated"}

@admin_router.get("/settings/api-keys")
async def get_api_key_status(db: Session = Depends(get_db)):
    """
    Get API key status (names only, not actual keys)
    Frontend calls: GET /api/admin/settings/api-keys
    """
    services = [
        "lemon_squeezy", "stripe", "fastspring", "paystack", "flutterwave",
        "runpod", "s3", "r2", "firebase"
    ]
    
    status_list = []
    for service in services:
        setting = db.query(APISettings).filter(APISettings.service == service).first()
        status_list.append({
            "service": service,
            "is_set": setting is not None,
            "is_enabled": setting.is_enabled if setting else False
        })
    
    return {"services": status_list}

@admin_router.put("/settings/api-keys/{service}")
async def update_api_key(
    service: str,
    api_key: str,
    is_enabled: bool = True,
    db: Session = Depends(get_db)
):
    """
    Update API key for service
    Frontend calls: PUT /api/admin/settings/api-keys/{service}
    """
    from utils_encryption import encrypt_key
    
    setting = db.query(APISettings).filter(APISettings.service == service).first()
    if setting:
        setting.key_encrypted = encrypt_key(api_key)
        setting.is_enabled = is_enabled
    else:
        setting = APISettings(
            id=str(uuid.uuid4()),
            service=service,
            key_encrypted=encrypt_key(api_key),
            is_enabled=is_enabled
        )
        db.add(setting)
    
    db.commit()
    return {"service": service, "message": "API key updated"}

@admin_router.put("/settings/pricing")
async def update_pricing(tier: str, price_usd: float, strike_price_usd: float, db: Session = Depends(get_db)):
    """
    Update tier pricing
    Frontend calls: PUT /api/admin/settings/pricing?tier=tier_1&price_usd=21&strike_price_usd=35
    """
    pricing = db.query(PricingTier).filter(PricingTier.tier == tier).first()
    if pricing:
        pricing.price_usd = price_usd
        pricing.strike_price_usd = strike_price_usd
        db.commit()
        return {"tier": tier, "price_usd": price_usd, "strike_price_usd": strike_price_usd}
    
    raise HTTPException(status_code=404, detail="Tier not found")

@admin_router.post("/whitelist")
async def add_whitelist(email: str, db: Session = Depends(get_db)):
    """
    Add email to whitelist (free unlimited access)
    Frontend calls: POST /api/admin/whitelist?email=test@example.com
    """
    existing = db.query(Whitelist).filter(Whitelist.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already whitelisted")
    
    whitelist_entry = Whitelist(id=str(uuid.uuid4()), email=email)
    db.add(whitelist_entry)
    
    # Also mark user as whitelisted if exists
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.is_whitelisted = True
    
    db.commit()
    return {"email": email, "message": "Added to whitelist"}

@admin_router.delete("/whitelist/{email}")
async def remove_whitelist(email: str, db: Session = Depends(get_db)):
    """
    Remove email from whitelist
    Frontend calls: DELETE /api/admin/whitelist/{email}
    """
    whitelist_entry = db.query(Whitelist).filter(Whitelist.email == email).first()
    if whitelist_entry:
        db.delete(whitelist_entry)
        db.commit()
    
    return {"email": email, "message": "Removed from whitelist"}

@admin_router.get("/fraud-logs")
async def get_fraud_logs(db: Session = Depends(get_db)):
    """
    Get fraud detection logs
    Frontend calls: GET /api/admin/fraud-logs
    """
    logs = db.query(FraudLog).order_by(FraudLog.updated_at.desc()).limit(100).all()
    
    return {
        "logs": [
            {
                "id": log.id,
                "email": log.email,
                "type": log.attempt_type,
                "attempts": log.attempts_count,
                "created_at": log.created_at.isoformat()
            }
            for log in logs
        ]
    }

def log_fraud(db: Session, email: str, attempt_type: str, details: str):
    """Helper to log fraud attempts"""
    existing = db.query(FraudLog).filter(
        FraudLog.email == email,
        FraudLog.attempt_type == attempt_type
    ).first()
    
    if existing:
        existing.attempts_count += 1
        existing.updated_at = datetime.utcnow()
    else:
        fraud_log = FraudLog(
            id=str(uuid.uuid4()),
            email=email,
            attempt_type=attempt_type,
            details=json.dumps({"reason": details})
        )
        db.add(fraud_log)
    
    db.commit()

# ==========================================
# WEBHOOKS ROUTER - Payment Processing
# ==========================================

webhooks_router = APIRouter()

@webhooks_router.post("/lemon-squeezy")
async def lemon_squeezy_webhook(request: dict, db: Session = Depends(get_db)):
    """
    Lemon Squeezy payment webhook
    Frontend: no direct call, called by Lemon Squeezy servers
    """
    event_type = request.get("meta", {}).get("event_name")
    
    if event_type == "order:created":
        user_email = request.get("data", {}).get("attributes", {}).get("customer_email")
        user = db.query(User).filter(User.email == user_email).first()
        if user:
            user.subscription_tier = "tier_1"  # Default tier
            db.commit()
    
    return {"status": "received"}

@webhooks_router.post("/stripe")
async def stripe_webhook(request: dict, db: Session = Depends(get_db)):
    """Stripe payment webhook"""
    return {"status": "received"}

@webhooks_router.post("/paystack")
async def paystack_webhook(request: dict, db: Session = Depends(get_db)):
    """Paystack payment webhook"""
    return {"status": "received"}

# ==========================================
# CONTENT ROUTER - Admin Content Uploads
# ==========================================

content_router = APIRouter()

@content_router.post("/upload")
async def upload_content(
    content_type: str,
    slot_number: int,
    file_url: str,
    admin_id: str,
    db: Session = Depends(get_db)
):
    """
    Upload content (logo, ads, styles, etc.)
    Frontend calls: POST /api/content/upload with file and metadata
    """
    upload = ContentUpload(
        id=str(uuid.uuid4()),
        content_type=content_type,
        slot_number=slot_number,
        file_url=file_url,
        uploaded_by=admin_id
    )
    db.add(upload)
    db.commit()
    
    return {
        "id": upload.id,
        "content_type": content_type,
        "slot": slot_number,
        "file_url": file_url
    }

@content_router.get("/{content_type}")
async def get_content(content_type: str, db: Session = Depends(get_db)):
    """
    Get all content of a type (for frontend to display)
    Frontend calls: GET /api/content/ads (gets all 10 ads for carousel)
    """
    uploads = db.query(ContentUpload).filter(
        ContentUpload.content_type == content_type
    ).order_by(ContentUpload.slot_number).all()
    
    return {
        "content_type": content_type,
        "items": [
            {
                "slot": u.slot_number,
                "url": u.file_url,
                "created_at": u.created_at.isoformat()
            }
            for u in uploads
        ]
    }

# ==========================================
# Export routers for main.py
# ==========================================

router_list = [
    ("auth", auth_router),
    ("generate", generate_router),
    ("gallery", gallery_router),
    ("admin", admin_router),
    ("webhooks", webhooks_router),
    ("content", content_router)
]
