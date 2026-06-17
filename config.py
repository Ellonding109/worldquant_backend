import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'wq_brain.db')
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', os.urandom(32).hex())
    
    # Default API Endpoints (can be changed via UI)
    DEFAULT_ENDPOINTS = {
        'base_url': 'https://api.worldquantbrain.com',
        'operators': '/operators',
        'data_sets': '/data-sets',
        'data_fields': '/data-fields',
        'simulations': '/simulations',
        'alphas': '/alphas'
    }
    
    # Session settings
    SESSION_TIMEOUT = 3600  # 1 hour
    AUTO_REFRESH_THRESHOLD = 300  # Refresh if < 5 mins left
    MAX_RETRIES = 2
    REQUEST_TIMEOUT = 15