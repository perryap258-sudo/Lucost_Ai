"""
Database models (SQLAlchemy ORM) and database initialization
"""

from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum

# ---- Database setup ----
from .config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ---- Enums ----
class SubscriptionTier(str, enum.Enum):
    TRIAL = "trial"
    TIER_1 = "tier_1"
    TIER_2 = "tier_2"
    TIER_3 = "tier_3"

class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"

class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"
    MANAGER = "manager"

class FraudAttemptType(str, enum.Enum):
    NON_SUBSCRIBER = "non_subscriber"
    WHITELIST_ABUSE = "whitelist_abuse"

# ---- Models ----

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True)
    firebase_uid = Column(String, unique=True, nullable=True)
    subscription_tier = Column(String, default="trial")
    trials_remaining = Column(Integer, default=2)
    is_whitelisted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    subscriptions = relationship("Subscription", back_populates="user")
    jobs = relationship("Job", back_populates="user")

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    tier = Column(String)  # tier_1, tier_2, tier_3
    gens_used = Column(Integer, default=0)
    gens_allowed = Column(Integer)  # 20, 15, or 10
    renews_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    payment_provider = Column(String)  # lemon_squeezy, stripe, paystack, etc.
    external_subscription_id = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="subscriptions")

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    status = Column(String, default="queued")  # queued, processing, done, failed
    script = Column(Text)
    style = Column(String)
    aspect_ratio = Column(String, default="9:16")
    characters = Column(Text)  # JSON string of cast
    music = Column(Text)  # JSON string of music
    video_url = Column(String, nullable=True)
    runpod_job_id = Column(String, nullable=True)
    gpu_count_used = Column(Integer, nullable=True)
    estimated_cost = Column(Float, nullable=True)
    actual_cost = Column(Float, nullable=True)
    has_watermark = Column(Boolean, default=False)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="jobs")

class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True)
    supabase_uid = Column(String, unique=True)
    password_hash = Column(String)
    role = Column(String)  # admin, manager
    is_active = Column(Boolean, default=True)
    requires_2fa = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class APISettings(Base):
    __tablename__ = "api_settings"

    id = Column(String, primary_key=True)
    service = Column(String, unique=True, index=True)  # lemon_squeezy, stripe, runpod, etc.
    key_encrypted = Column(Text)
    is_enabled = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class GPUSettings(Base):
    __tablename__ = "gpu_settings"

    id = Column(String, primary_key=True)
    tier = Column(String, unique=True, index=True)  # tier_1, tier_2, tier_3
    gpu_count = Column(Integer)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PricingTier(Base):
    __tablename__ = "pricing_tiers"

    id = Column(String, primary_key=True)
    tier = Column(String, unique=True, index=True)
    name = Column(String)
    price_usd = Column(Float)
    strike_price_usd = Column(Float, nullable=True)
    gens_per_month = Column(Integer)
    max_duration_seconds = Column(Integer)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Whitelist(Base):
    __tablename__ = "whitelist"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class FraudLog(Base):
    __tablename__ = "fraud_logs"

    id = Column(String, primary_key=True)
    email = Column(String, index=True)
    attempt_type = Column(String)  # non_subscriber, whitelist_abuse
    details = Column(Text)  # JSON details
    attempts_count = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ContentUpload(Base):
    __tablename__ = "content_uploads"

    id = Column(String, primary_key=True)
    content_type = Column(String)  # logo, ad_video, style_preview, feature_clip, bg_reel, avatar
    slot_number = Column(Integer)  # 1-10 for ads, 1-7 for styles, etc.
    file_url = Column(String)
    file_size = Column(Integer)
    uploaded_by = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PaymentEvent(Base):
    __tablename__ = "payment_events"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    event_type = Column(String)  # subscription_created, subscription_renewed, subscription_cancelled
    provider = Column(String)  # lemon_squeezy, stripe, paystack, etc.
    external_event_id = Column(String)
    amount_usd = Column(Float, nullable=True)
    status = Column(String)  # pending, completed, failed
    details = Column(Text)  # JSON
    created_at = Column(DateTime, default=datetime.utcnow)

# ---- Initialize database ----
def init_db():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
