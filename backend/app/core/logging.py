# 🌱 Smart Irrigation System - Configuration Logging
# Logging structuré avec Structlog et Rich pour développement

import sys
import logging
import structlog
from pathlib import Path
from rich.console import Console
from rich.logging import RichHandler
from typing import Any, Dict

from app.core.config import settings

def setup_logging() -> None:
    """
    Configuration du système de logging avec Structlog
    - JSON en production
    - Format riche en développement
    - Rotation des fichiers
    - Logs structurés
    """
    
    # Niveau de log
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Console pour développement
    console = Console()
    
    # =============================================================================
    # 📊 PROCESSEURS STRUCTLOG
    # =============================================================================
    
    shared_processors = [
        # Ajouter timestamp
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S.%f", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        # Ajouter informations contextuelles
        add_context_processor,
    ]
    
    if settings.LOG_FORMAT == "json":
        # Format JSON pour production
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer()
        ]
    else:
        # Format lisible pour développement
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True)
        ]
    
    # Configuration Structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # =============================================================================
    # 📋 HANDLERS
    # =============================================================================
    
    handlers = []
    
    # Handler console
    if settings.DEBUG:
        # Rich handler pour développement
        console_handler = RichHandler(
            console=console,
            show_time=True,
            show_path=True,
            rich_tracebacks=True,
            markup=True
        )
    else:
        # Handler console simple pour production
        console_handler = logging.StreamHandler(sys.stdout)
    
    console_handler.setLevel(log_level)
    handlers.append(console_handler)
    
    # Handler fichier si configuré
    if settings.LOG_FILE:
        log_file_path = Path(settings.LOG_FILE)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Handler avec rotation
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            log_file_path,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        
        # Format pour fichier
        if settings.LOG_FORMAT == "json":
            file_formatter = logging.Formatter('%(message)s')
        else:
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        file_handler.setFormatter(file_formatter)
        handlers.append(file_handler)
    
    # =============================================================================
    # 🔧 CONFIGURATION LOGGING STANDARD
    # =============================================================================
    
    # Configuration du logger racine
    logging.basicConfig(
        level=log_level,
        handlers=handlers,
        force=True
    )
    
    # Configurer les loggers spécifiques
    configure_specific_loggers(log_level)
    
    # Logger initial
    logger = structlog.get_logger()
    logger.info(
        "Logging configuré",
        level=settings.LOG_LEVEL,
        format=settings.LOG_FORMAT,
        file=settings.LOG_FILE,
        environment=settings.ENVIRONMENT
    )

def add_context_processor(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processeur pour ajouter du contexte aux logs
    """
    # Ajouter des informations contextuelles
    event_dict["service"] = "irrigation-backend"
    event_dict["version"] = settings.VERSION
    event_dict["environment"] = settings.ENVIRONMENT
    
    return event_dict

def configure_specific_loggers(log_level: int) -> None:
    """
    Configuration spécifique pour certains loggers
    """
    
    # SQLAlchemy - Réduire verbosité en production
    if settings.is_production:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    else:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    
    # Uvicorn
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    
    # FastAPI
    logging.getLogger("fastapi").setLevel(log_level)
    
    # MQTT
    logging.getLogger("paho.mqtt").setLevel(logging.WARNING)
    
    # HTTP clients
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    
    # Redis
    logging.getLogger("aioredis").setLevel(logging.WARNING)

# =============================================================================
# 🔧 UTILITAIRES LOGGING
# =============================================================================

def get_logger(name: str = None) -> structlog.BoundLogger:
    """
    Obtenir un logger Structlog
    """
    return structlog.get_logger(name)

def log_function_call(func_name: str, **kwargs) -> None:
    """
    Logger l'appel d'une fonction avec ses paramètres
    """
    logger = get_logger()
    logger.debug(
        "Function call",
        function=func_name,
        **{k: str(v)[:100] for k, v in kwargs.items()}  # Limiter taille
    )

def log_performance(operation: str, duration: float, **kwargs) -> None:
    """
    Logger les performances d'une opération
    """
    logger = get_logger()
    logger.info(
        "Performance metric",
        operation=operation,
        duration_ms=round(duration * 1000, 2),
        **kwargs
    )

# =============================================================================
# 🔧 DECORATEUR POUR LOGGING AUTOMATIQUE
# =============================================================================

from functools import wraps
import time
from typing import Callable, TypeVar, Union

T = TypeVar('T')

def log_calls(logger_name: str = None) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Décorateur pour logger automatiquement les appels de fonction
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            logger = get_logger(logger_name or func.__module__)
            start_time = time.time()
            
            logger.debug(
                "Function start",
                function=func.__name__,
                args_count=len(args),
                kwargs_keys=list(kwargs.keys())
            )
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                logger.debug(
                    "Function success",
                    function=func.__name__,
                    duration_ms=round(duration * 1000, 2)
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                logger.error(
                    "Function error",
                    function=func.__name__,
                    error=str(e),
                    duration_ms=round(duration * 1000, 2)
                )
                
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            logger = get_logger(logger_name or func.__module__)
            start_time = time.time()
            
            logger.debug(
                "Function start",
                function=func.__name__,
                args_count=len(args),
                kwargs_keys=list(kwargs.keys())
            )
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                logger.debug(
                    "Function success",
                    function=func.__name__,
                    duration_ms=round(duration * 1000, 2)
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                logger.error(
                    "Function error",
                    function=func.__name__,
                    error=str(e),
                    duration_ms=round(duration * 1000, 2)
                )
                
                raise
        
        # Retourner le bon wrapper selon si la fonction est async
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

# =============================================================================
# 🔒 MASQUAGE DONNÉES SENSIBLES
# =============================================================================

def mask_sensitive_data(data: dict) -> dict:
    """
    Masquer les données sensibles dans les logs
    """
    sensitive_keys = {
        'password', 'token', 'secret', 'key', 'auth',
        'credential', 'pass', 'pwd', 'api_key'
    }
    
    masked_data = {}
    for key, value in data.items():
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            masked_data[key] = "***masked***"
        elif isinstance(value, dict):
            masked_data[key] = mask_sensitive_data(value)
        else:
            masked_data[key] = value
    
    return masked_data