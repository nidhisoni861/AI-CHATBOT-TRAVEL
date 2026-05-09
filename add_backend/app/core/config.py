"""Central configuration for Wanderly backend"""
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables at module import time
project_root = Path(__file__).resolve().parents[3]
env_path = project_root / "backend_fine_tuning" / ".env"

if env_path.exists():
    load_dotenv(env_path, override=False)
    print(f"[CONFIG] Loaded environment from: {env_path}")
else:
    print(f"[CONFIG] No .env file found at: {env_path}")

# Export all environment variables so os.getenv() works everywhere
if env_path.exists():
    with open(env_path, 'r') as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key.strip()] = value.strip()
    
    print("[CONFIG] Environment variables loaded successfully")

def get_api_key(service_name: str) -> str:
    """Get API key for a specific service"""
    return os.getenv(service_name, "")

def is_service_enabled(service_name: str) -> bool:
    """Check if a service is enabled"""
    return bool(get_api_key(service_name))
