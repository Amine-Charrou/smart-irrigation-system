# 🌱 Smart Irrigation System - Backend Dockerfile
# FastAPI backend optimisé pour production

FROM python:3.11-slim as base

# Métadonnées
LABEL maintainer="Smart Irrigation Team"
LABEL description="Smart Irrigation System - FastAPI Backend"
LABEL version="2.0.0"

# Variables build
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=2.0.0

# Variables d'environnement
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# =============================================================================
# 💫 STAGE 1: DÉPENDANCES SYSTÈME
# =============================================================================
FROM base as system-deps

# Installer dépendances système
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# =============================================================================
# 🐍 STAGE 2: DÉPENDANCES PYTHON
# =============================================================================
FROM system-deps as python-deps

# Upgrade pip
RUN pip install --upgrade pip setuptools wheel

# Copier requirements
WORKDIR /tmp
COPY requirements.txt .

# Installer dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# =============================================================================
# 🔐 STAGE 3: UTILISATEUR & SÉCURITÉ
# =============================================================================
FROM python-deps as security

# Créer utilisateur non-root
RUN groupadd -r irrigation && useradd -r -g irrigation irrigation

# Créer répertoires avec permissions
RUN mkdir -p /app /app/logs /app/uploads \
    && chown -R irrigation:irrigation /app

# =============================================================================
# 🚀 STAGE 4: APPLICATION
# =============================================================================
FROM security as application

# Passer à l'utilisateur non-root
USER irrigation

# Répertoire de travail
WORKDIR /app

# Copier code application
COPY --chown=irrigation:irrigation . .

# Variables d'environnement finales
ENV PATH="/home/irrigation/.local/bin:$PATH"
ENV ENVIRONMENT=production

# Exposition port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Point d'entrée
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# =============================================================================
# 👩‍💻 ALTERNATIVE DÉVELOPPEMENT
# =============================================================================
FROM application as development

# Mode développement
USER root
RUN pip install --no-cache-dir debugpy pytest-xdist
USER irrigation

# Variables dev
ENV ENVIRONMENT=development
ENV DEBUG=true

# Commande développement avec hot reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "/app"]

# =============================================================================
# 🔄 VOLUME MOUNTS POUR DÉVELOPPEMENT
# =============================================================================
# docker run -v $(pwd):/app -p 8000:8000 backend:dev