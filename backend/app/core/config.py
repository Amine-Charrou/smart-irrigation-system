# 🌱 Smart Irrigation System - Configuration
# Gestion centralisée de la configuration avec Pydantic Settings

from pydantic import BaseSettings, validator, AnyHttpUrl
from typing import List, Optional, Dict, Any
from functools import lru_cache
import os
from pathlib import Path

class Settings(BaseSettings):
    """
    Configuration de l'application avec validation Pydantic
    Les variables peuvent être surchargées par des variables d'environnement
    """
    
    # =============================================================================
    # 💫 APPLICATION
    # =============================================================================
    APP_NAME: str = "Smart Irrigation System"
    VERSION: str = "2.0.0"
    DESCRIPTION: str = "Système d'irrigation intelligente avec IoT"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    TESTING: bool = False
    
    # URLs
    BACKEND_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:3000"
    API_V1_PREFIX: str = "/api/v1"
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080"
    ]
    
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]
    
    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # =============================================================================
    # 🔐 SÉCURITÉ & AUTHENTIFICATION
    # =============================================================================
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    SESSION_MAX_AGE: int = 1800  # 30 minutes
    
    # Validation du secret en production
    @validator("SECRET_KEY")
    def validate_secret_key(cls, v: str, values: Dict[str, Any]) -> str:
        if values.get("ENVIRONMENT") == "production" and len(v) < 32:
            raise ValueError("SECRET_KEY doit faire au moins 32 caractères en production")
        return v
    
    # =============================================================================
    # 🗄️ BASE DE DONNÉES
    # =============================================================================
    DATABASE_URL: str = "postgresql://irrigation_user:secure_password@localhost:5432/irrigation_db"
    DATABASE_TEST_URL: str = "sqlite:///./test.db"
    
    # Pool de connexions
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    
    # =============================================================================
    # 🔄 REDIS
    # =============================================================================
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600  # 1 heure
    REDIS_SESSION_TTL: int = 1800  # 30 minutes
    
    # =============================================================================
    # 📡 MQTT & IoT
    # =============================================================================
    MQTT_BROKER: str = "localhost"
    MQTT_PORT: int = 1883
    MQTT_USERNAME: Optional[str] = None
    MQTT_PASSWORD: Optional[str] = None
    MQTT_KEEPALIVE: int = 60
    MQTT_QOS: int = 1
    
    # Topics MQTT
    MQTT_TOPIC_PREFIX: str = "irrigation"
    MQTT_TOPIC_SENSORS: str = "sensors"
    MQTT_TOPIC_ACTUATORS: str = "actuators"
    MQTT_TOPIC_STATUS: str = "status"
    
    @property
    def mqtt_topics(self) -> Dict[str, str]:
        prefix = self.MQTT_TOPIC_PREFIX
        return {
            "sensors": f"{prefix}/{self.MQTT_TOPIC_SENSORS}/+/+",
            "actuators": f"{prefix}/{self.MQTT_TOPIC_ACTUATORS}/+/+",
            "status": f"{prefix}/{self.MQTT_TOPIC_STATUS}/+"
        }
    
    # =============================================================================
    # 🌡️ API MÉTÉO
    # =============================================================================
    WEATHER_API_KEY: Optional[str] = None
    WEATHER_API_URL: str = "https://api.openweathermap.org/data/2.5"
    WEATHER_UPDATE_INTERVAL: int = 3600  # 1 heure
    
    # =============================================================================
    # 📧 EMAIL
    # =============================================================================
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: str = "Smart Irrigation <noreply@irrigation.com>"
    SMTP_TLS: bool = True
    
    # =============================================================================
    # 📋 LOGGING
    # =============================================================================
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json | text
    LOG_FILE: Optional[str] = "logs/irrigation.log"
    
    # =============================================================================
    # 📈 MONITORING
    # =============================================================================
    PROMETHEUS_ENABLED: bool = False
    PROMETHEUS_PORT: int = 9090
    
    SENTRY_DSN: Optional[str] = None
    
    # =============================================================================
    # 🔧 CONFIGURATION MÉTIER
    # =============================================================================
    
    # Irrigation
    DEFAULT_IRRIGATION_DURATION: int = 30  # minutes
    MIN_IRRIGATION_INTERVAL: int = 60      # minutes
    MAX_IRRIGATION_DURATION: int = 120     # minutes
    
    # Alertes
    ALERT_CHECK_INTERVAL: int = 300        # secondes (5 min)
    ALERT_COOLDOWN: int = 1800            # secondes (30 min)
    
    # Climat
    OPTIMAL_VPD_MIN: float = 0.8          # kPa
    OPTIMAL_VPD_MAX: float = 1.2          # kPa
    CRITICAL_TEMP_MIN: float = 10.0       # °C
    CRITICAL_TEMP_MAX: float = 35.0       # °C
    
    # Capteurs
    SENSOR_TIMEOUT: int = 300             # secondes (5 min)
    SENSOR_RETRY_ATTEMPTS: int = 3
    
    # =============================================================================
    # 📁 CHEMINS
    # =============================================================================
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    LOG_DIR: Path = BASE_DIR / "logs"
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    STATIC_DIR: Path = BASE_DIR / "static"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Créer répertoires si nécessaire
        self.LOG_DIR.mkdir(exist_ok=True)
        self.UPLOAD_DIR.mkdir(exist_ok=True)
        self.STATIC_DIR.mkdir(exist_ok=True)
    
    # =============================================================================
    # 🔧 MÉTHODES UTILITAIRES
    # =============================================================================
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"
    
    @property
    def is_testing(self) -> bool:
        return self.TESTING or self.ENVIRONMENT == "testing"
    
    def get_database_url(self) -> str:
        """Retourne l'URL de base de données selon l'environnement"""
        if self.is_testing:
            return self.DATABASE_TEST_URL
        return self.DATABASE_URL
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# =============================================================================
# 💫 INSTANCE GLOBALE
# =============================================================================

@lru_cache()
def get_settings() -> Settings:
    """
    Factory pour obtenir une instance de configuration (cachée)
    """
    return Settings()

# Instance globale
settings = get_settings()

# =============================================================================
# 📁 CONFIGURATION ENVIRONNEMENT SPECIFIQUE
# =============================================================================

class DevelopmentSettings(Settings):
    """Configuration développement"""
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"

class ProductionSettings(Settings):
    """Configuration production"""
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    PROMETHEUS_ENABLED: bool = True

class TestingSettings(Settings):
    """Configuration tests"""
    ENVIRONMENT: str = "testing"
    TESTING: bool = True
    DATABASE_URL: str = "sqlite:///./test.db"
    
# Factory pour obtenir la configuration selon l'environnement
def get_settings_by_env() -> Settings:
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionSettings()
    elif env == "testing":
        return TestingSettings()
    else:
        return DevelopmentSettings()