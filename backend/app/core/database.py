# 🌱 Smart Irrigation System - Configuration Base de Données
# SQLAlchemy avec support async et gestion des sessions

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import StaticPool
from sqlalchemy import event
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import structlog

from app.core.config import settings

logger = structlog.get_logger()

# =============================================================================
# 🔧 CONFIGURATION MOTEUR
# =============================================================================

# Configuration du moteur selon l'environnement
if settings.is_testing:
    # SQLite pour tests (synchrone converti en async)
    SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
    engine = create_async_engine(
        SQLALCHEMY_DATABASE_URL,
        echo=settings.DEBUG,
        poolclass=StaticPool,
        connect_args={
            "check_same_thread": False,
        },
    )
else:
    # PostgreSQL pour développement/production
    SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL.replace(
        "postgresql://", "postgresql+asyncpg://"
    )
    engine = create_async_engine(
        SQLALCHEMY_DATABASE_URL,
        echo=settings.DEBUG,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_pre_ping=True,  # Vérification santé connexions
        pool_recycle=3600,   # Recycler connexions après 1h
    )

# =============================================================================
# 🏗️ SESSION FACTORY
# =============================================================================

# Créateur de sessions async
SessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=True,
    autocommit=False
)

# =============================================================================
# 📊 MODÈLE DE BASE
# =============================================================================

# Classe de base pour tous les modèles
Base = declarative_base()

# =============================================================================
# 🔧 GESTIONNAIRE DE SESSIONS
# =============================================================================

@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Gestionnaire de contexte pour sessions de base de données
    Garantit la fermeture propre des sessions
    """
    async with SessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Erreur session DB: {e}")
            raise
        finally:
            await session.close()

# Dépendance FastAPI pour injection de session
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dépendance FastAPI pour obtenir une session de base de données
    """
    async with get_db_session() as session:
        yield session

# =============================================================================
# 🗺️ UTILITAIRES BASE DE DONNÉES
# =============================================================================

async def init_db() -> None:
    """
    Initialiser la base de données (créer toutes les tables)
    """
    try:
        async with engine.begin() as conn:
            # Importer tous les modèles pour s'assurer qu'ils sont enregistrés
            from app.models import *  # noqa
            
            # Créer toutes les tables
            await conn.run_sync(Base.metadata.create_all)
            
        logger.info("✅ Base de données initialisée avec succès")
        
    except Exception as e:
        logger.error(f"❌ Erreur initialisation DB: {e}")
        raise

async def drop_db() -> None:
    """
    Supprimer toutes les tables (ATTENTION: destructif!)
    """
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            
        logger.warning("⚠️ Base de données supprimée")
        
    except Exception as e:
        logger.error(f"❌ Erreur suppression DB: {e}")
        raise

async def reset_db() -> None:
    """
    Réinitialiser la base de données (supprimer et recréer)
    """
    await drop_db()
    await init_db()
    logger.info("🔄 Base de données réinitialisée")

# =============================================================================
# 📈 MONITORING DES CONNEXIONS
# =============================================================================

# Event listeners pour monitoring
@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """
    Configuration SQLite pour améliorer les performances
    """
    if "sqlite" in str(engine.url):
        cursor = dbapi_connection.cursor()
        # Activer les clés étrangères
        cursor.execute("PRAGMA foreign_keys=ON")
        # Journal mode WAL pour meilleures performances
        cursor.execute("PRAGMA journal_mode=WAL")
        # Synchronisation normale
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

@event.listens_for(engine.sync_engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    """
    Log des checkout de connexions
    """
    if settings.DEBUG:
        logger.debug("Connexion DB checkout")

@event.listens_for(engine.sync_engine, "checkin")
def receive_checkin(dbapi_connection, connection_record):
    """
    Log des checkin de connexions
    """
    if settings.DEBUG:
        logger.debug("Connexion DB checkin")

# =============================================================================
# 🧪 UTILITAIRES POUR TESTS
# =============================================================================

async def create_test_db() -> None:
    """
    Créer une base de données de test isolée
    """
    if not settings.is_testing:
        raise RuntimeError("create_test_db ne peut être utilisé qu'en mode test")
    
    await init_db()
    logger.info("🧪 Base de données de test créée")

async def cleanup_test_db() -> None:
    """
    Nettoyer la base de données de test
    """
    if not settings.is_testing:
        raise RuntimeError("cleanup_test_db ne peut être utilisé qu'en mode test")
    
    await drop_db()
    logger.info("🧪 Base de données de test nettoyée")

# =============================================================================
# 🔍 REQUÊTES UTILITAIRES
# =============================================================================

async def health_check_db() -> bool:
    """
    Vérifier la santé de la connexion base de données
    """
    try:
        async with get_db_session() as session:
            result = await session.execute("SELECT 1")
            return result.scalar() == 1
    except Exception as e:
        logger.error(f"Health check DB failed: {e}")
        return False

async def get_db_info() -> dict:
    """
    Obtenir des informations sur la base de données
    """
    try:
        async with get_db_session() as session:
            if "postgresql" in str(engine.url):
                result = await session.execute("SELECT version()")
                version = result.scalar()
            else:
                result = await session.execute("SELECT sqlite_version()")
                version = f"SQLite {result.scalar()}"
                
            return {
                "url": str(engine.url).split("@")[-1] if "@" in str(engine.url) else str(engine.url),
                "version": version,
                "pool_size": engine.pool.size() if hasattr(engine.pool, 'size') else None,
                "checked_out": engine.pool.checkedout() if hasattr(engine.pool, 'checkedout') else None
            }
    except Exception as e:
        logger.error(f"Impossible d'obtenir les infos DB: {e}")
        return {"error": str(e)}