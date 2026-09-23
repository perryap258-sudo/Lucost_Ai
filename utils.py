"""
Utility functions for encryption, validation, and common operations
"""

from cryptography.fernet import Fernet
from .config import settings
import base64
import hashlib
import re

# ---- Encryption ----

def get_cipher():
    """Get Fernet cipher for encryption"""
    key = settings.ENCRYPTION_KEY
    if isinstance(key, str):
        key = base64.urlsafe_b64encode(hashlib.sha256(key.encode()).digest())
    return Fernet(key)

def encrypt_key(api_key: str) -> str:
    """Encrypt API key"""
    cipher = get_cipher()
    return cipher.encrypt(api_key.encode()).decode()

def decrypt_key(encrypted_key: str) -> str:
    """Decrypt API key"""
    cipher = get_cipher()
    return cipher.decrypt(encrypted_key.encode()).decode()

# ---- Validation ----

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password: str) -> bool:
    """Validate password strength"""
    return len(password) >= 8

def validate_script(script: str) -> tuple:
    """Validate script and return word count and duration estimate"""
    words = len(script.split())
    # ~30 words = 30 seconds
    estimated_seconds = (words / 30) * 30
    return words, estimated_seconds

def validate_style(style: str) -> bool:
    """Validate style is one of the 7 approved styles"""
    valid_styles = [
        "Narration Anime",
        "Narration Drama",
        "Drama",
        "Drama Anime",
        "CGI Idol",
        "Cinematic 3D",
        "Others"
    ]
    return style in valid_styles

def validate_aspect_ratio(ratio: str) -> bool:
    """Validate aspect ratio"""
    valid_ratios = ["9:16", "1:1", "16:9"]
    return ratio in valid_ratios

# ---- Script Parsing ----

def parse_script(script: str) -> dict:
    """
    Parse script to extract:
    - Character names
    - Crowd descriptions
    - Actions/scenes
    - Duration estimate
    """
    scenes = []
    lines = script.split('\n')
    
    current_scene = {
        "actions": [],
        "characters": set(),
        "crowd_description": None
    }
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Simple parsing - in production, use NLP
        # Look for character names (capitalized words followed by :)
        if ':' in line:
            char_name = line.split(':')[0].strip()
            if char_name.isupper() and char_name.replace(' ', '').isalpha():
                current_scene["characters"].add(char_name)
        
        # Look for crowd references
        if 'crowd' in line.lower() or 'people' in line.lower() or 'background' in line.lower():
            current_scene["crowd_description"] = line
        
        current_scene["actions"].append(line)
    
    # Create scenes (5 seconds each ~1-2 lines)
    words = len(script.split())
    num_scenes = max(1, words // 15)  # ~15 words per scene
    duration_seconds = num_scenes * 5
    
    return {
        "num_scenes": num_scenes,
        "duration_seconds": duration_seconds,
        "characters": list(current_scene["characters"]),
        "crowd_description": current_scene["crowd_description"],
        "total_actions": len(current_scene["actions"])
    }

# ---- GPU Calculation ----

def calculate_gpu_needs(duration_seconds: int, tier: str) -> int:
    """
    Calculate GPU count needed based on duration and tier
    Tiers set this in admin dashboard, but here's the formula
    """
    # From spec: 5min→6-10 GPUs, 15min→20 GPUs, 30min→23 GPUs
    # Rough formula: GPUs = (duration / 30) * 23, min 4
    base_gpus = max(4, int((duration_seconds / 1800) * 23))
    return base_gpus

def estimate_cost(duration_seconds: int, tier: str, gpu_count: int) -> float:
    """
    Estimate GPU cost for rendering
    Cost = gpu_count * duration_in_hours * hourly_rate
    """
    GPU_COST_PER_HOUR = 0.35
    hours = duration_seconds / 3600
    estimated_cost = gpu_count * hours * GPU_COST_PER_HOUR
    return round(estimated_cost, 2)

# ---- Profit Calculation ----

def calculate_profit(revenue: float, gpu_cost: float, payment_fee: float = 0.05) -> dict:
    """Calculate profit margin"""
    payment_fee_amount = revenue * payment_fee
    profit = revenue - gpu_cost - payment_fee_amount
    margin_percent = (profit / revenue * 100) if revenue > 0 else 0
    
    return {
        "revenue": round(revenue, 2),
        "gpu_cost": round(gpu_cost, 2),
        "payment_fee": round(payment_fee_amount, 2),
        "profit": round(profit, 2),
        "margin_percent": round(margin_percent, 1)
    }
