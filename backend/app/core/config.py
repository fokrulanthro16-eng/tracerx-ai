"""
TraceRx AI - Enterprise Configuration & Multi-Tenant Settings
"""

from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "TraceRx AI Enterprise"
    VERSION: str = "2.0.0-PROD"
    API_V1_STR: str = "/api/v1"
    APP_ENV: str = "production"

    # Multi-tenancy & Security
    DEFAULT_TENANT_ID: str = "tenant-who-global"
    SECRET_KEY: str = "tracerx-enterprise-jwt-super-secret-key-2026-prod"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Database (PostgreSQL / Supabase / SQLite fallback)
    DATABASE_URL: str = "sqlite:///./tracerx_enterprise.db"

    # Web3 / Smart Contract L2 Settings
    RPC_URL_POLYGON_AMOY: str = "https://rpc-amoy.polygon.technology"
    RPC_URL_BASE_SEPOLIA: str = "https://sepolia.base.org"
    ACTIVE_NETWORK: str = "polygonAmoy"
    CONTRACT_ADDRESS: str = "0x89205A3A3b2A69De6Dbf7f01ED13B2108B2c43e7"
    OPERATOR_PRIVATE_KEY: Optional[str] = None
    CHAIN_ID: int = 80002

    # GS1 Standards
    GS1_COMPANY_PREFIX: str = "0030001"
    DEFAULT_BIZ_LOCATION_GLN: str = "urn:epc:id:sgln:0030001.00001.0"

    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
        "extra": "ignore"
    }


settings = Settings()
