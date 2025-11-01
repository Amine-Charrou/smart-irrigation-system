# 🌱 Smart Irrigation System - Application FastAPI principale
# Point d'entrée avec middleware, routes, et WebSocket

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

import structlog
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from app.core.config import settings
from app.core.database import engine, Base
from app.core.logging import setup_logging
from app.core.cache import redis_client
from app.api import router as api_router
from app.websocket.manager import WebSocketManager
from app.iot.mqtt_client import MQTTClient
from app.core.scheduler import start_scheduler

# Configuration logging
setup_logging()
logger = structlog.get_logger()

# Instances globales
websocket_manager = WebSocketManager()
mqtt_client = MQTTClient()

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Gestionnaire de cycle de vie de l'application
    Gère l'initialisation et la fermeture des services
    """
    logger.info("Démarrage de l'application Smart Irrigation")
    
    try:
        # 🗄️ Initialisation base de données
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Base de données initialisée")
        
        # 🔄 Connexion Redis
        await redis_client.ping()
        logger.info("✅ Redis connecté")
        
        # 📡 Initialisation MQTT
        await mqtt_client.connect()
        logger.info("✅ MQTT connecté")
        
        # 🕰️ Démarrage scheduler
        await start_scheduler()
        logger.info("✅ Scheduler démarré")
        
        logger.info("🚀 Application démarrée avec succès")
        yield
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du démarrage: {e}")
        raise
    
    finally:
        # Nettoyage des ressources
        logger.info("Arrêt de l'application...")
        
        try:
            await mqtt_client.disconnect()
            await redis_client.close()
            logger.info("✅ Ressources libérées")
        except Exception as e:
            logger.error(f"⚠️ Erreur lors de l'arrêt: {e}")

# =============================================================================
# 🚀 CREATION APPLICATION FASTAPI
# =============================================================================
app = FastAPI(
    title="Smart Irrigation System API",
    description="🌱 API REST pour système d'irrigation intelligente avec authentification JWT et intégration IoT",
    version="2.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan
)

# =============================================================================
# 🔒 MIDDLEWARE DE SÉCURITÉ
# =============================================================================

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Page-Count"]
)

# Trusted hosts
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )

# Sessions
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    max_age=settings.SESSION_MAX_AGE,
    same_site="lax",
    https_only=not settings.DEBUG
)

# =============================================================================
# 📊 MIDDLEWARE MONITORING
# =============================================================================

# Prometheus metrics
if settings.PROMETHEUS_ENABLED:
    instrumentator = Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        should_respect_env_var=True,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/health", "/metrics"],
        env_var_name="ENABLE_METRICS",
        inprogress_name="http_requests_inprogress",
        inprogress_labels=True
    )
    instrumentator.instrument(app).expose(app)

# Middleware de logging des requêtes
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """
    Middleware pour logger les requêtes HTTP avec temps de réponse
    """
    start_time = time.time()
    
    # Exécuter la requête
    response = await call_next(request)
    
    # Calculer temps de traitement
    process_time = time.time() - start_time
    
    # Logger les informations
    logger.info(
        "HTTP Request",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        process_time=round(process_time, 4),
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent", "")
    )
    
    # Ajouter header temps de réponse
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

# =============================================================================
# 📡 GESTIONNAIRES D'EXCEPTIONS
# =============================================================================

@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc: Exception):
    logger.error(
        "Internal Server Error",
        error=str(exc),
        url=str(request.url),
        method=request.method
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "Une erreur interne s'est produite",
            "request_id": getattr(request.state, "request_id", None)
        }
    )

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "Ressource non trouvée",
            "path": str(request.url.path)
        }
    )

# =============================================================================
# 🗺️ ROUTES
# =============================================================================

# Routes API
app.include_router(
    api_router,
    prefix="/api/v1",
    tags=["API v1"]
)

# WebSocket pour temps réel
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket, client_id: str):
    await websocket_manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket_manager.handle_message(client_id, data)
    except Exception as e:
        logger.error(f"Erreur WebSocket: {e}")
    finally:
        await websocket_manager.disconnect(client_id)

# =============================================================================
# 🩺 ENDPOINTS SYSTÈME
# =============================================================================

@app.get("/health")
async def health_check():
    """
    Vérification de santé du système
    """
    try:
        # Vérifier Redis
        await redis_client.ping()
        redis_status = "OK"
    except Exception:
        redis_status = "ERROR"
    
    return {
        "status": "OK",
        "version": "2.0.0",
        "services": {
            "database": "OK",  # TODO: vérifier DB
            "redis": redis_status,
            "mqtt": "OK" if mqtt_client.is_connected else "ERROR"
        },
        "timestamp": time.time()
    }

@app.get("/")
async def root():
    """
    Point d'entrée API avec informations de base
    """
    return {
        "message": "🌱 Smart Irrigation System API",
        "version": "2.0.0",
        "docs": "/docs" if settings.DEBUG else None,
        "status": "active"
    }

# Servir fichiers statiques (si nécessaire)
if settings.DEBUG:
    app.mount("/static", StaticFiles(directory="static"), name="static")

# =============================================================================
# 🔧 POINT D'ENTRÉE DEVELOPPEMENT
# =============================================================================
if __name__ == "__main__":
    import uvicorn
    
    logger.info("Démarrage en mode développement")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["app"],
        log_level="info"
    )