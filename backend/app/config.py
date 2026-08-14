import os
from pydantic import BaseModel, Field
from typing import List

class Settings(BaseModel):
    APP_NAME: str = "NEXUS Community Development Intelligence Backend"
    ENV: str = os.getenv("ENV", "development")
    
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "nexus_db")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "db")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
    
    REDIS_HOST: str = os.getenv("REDIS_HOST", "redis" if os.getenv("DOCKER_CONTAINER") else "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_URL: str = os.getenv("REDIS_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}/0")
    
    PLANETARY_COMPUTER_STAC_URL: str = "https://planetarycomputer.microsoft.com/api/stac/v1"
    
    # CORS Configuration
    CORS_ALLOWED_ORIGINS: List[str] = [
        origin.strip() for origin in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000").split(",") if origin.strip()
    ]
    
    # AOI Safety Boundaries & Spatial Resource Protection
    NEXUS_MAX_AOI_AREA_KM2: float = float(os.getenv("NEXUS_MAX_AOI_AREA_KM2", "25000.0"))
    NEXUS_MAX_AOI_WIDTH_KM: float = float(os.getenv("NEXUS_MAX_AOI_WIDTH_KM", "200.0"))
    NEXUS_MAX_AOI_HEIGHT_KM: float = float(os.getenv("NEXUS_MAX_AOI_HEIGHT_KM", "200.0"))
    NEXUS_MAX_RASTER_PIXELS: int = int(os.getenv("NEXUS_MAX_RASTER_PIXELS", "250000000")) # 250M pixels cap

settings = Settings()
