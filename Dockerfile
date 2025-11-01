# 🌱 Smart Irrigation System - Dockerfile Multi-stage
# Build optimisé pour production avec sécurité renforcée

# =============================================================================
# 🏗️ STAGE 1: Build Frontend React
# =============================================================================
FROM node:18-alpine AS frontend-builder

# Métadonnées
LABEL maintainer="Smart Irrigation Team"
LABEL description="Smart Irrigation System - Frontend Build Stage"
LABEL version="2.0.0"

# Variables build
ARG REACT_APP_API_URL=http://localhost:8000
ARG REACT_APP_WS_URL=ws://localhost:8000
ARG NODE_ENV=production

# Sécurité: utilisateur non-root
RUN addgroup -g 1001 -S nodejs
RUN adduser -S frontend -u 1001

# Répertoire de travail
WORKDIR /app

# Copier package files
COPY frontend/package*.json ./

# Installer dépendances avec cache optimisé
RUN npm ci --only=production --cache /tmp/.npm

# Copier code source
COPY frontend/ ./

# Variables d'environnement
ENV REACT_APP_API_URL=$REACT_APP_API_URL
ENV REACT_APP_WS_URL=$REACT_APP_WS_URL
ENV NODE_ENV=$NODE_ENV
ENV GENERATE_SOURCEMAP=false

# Build production optimisé
RUN npm run build

# Nettoyer cache
RUN npm cache clean --force

# =============================================================================
# 🐍 STAGE 2: Build Backend Python
# =============================================================================
FROM python:3.11-slim AS backend-builder

# Métadonnées
LABEL maintainer="Smart Irrigation Team"
LABEL description="Smart Irrigation System - Backend Build Stage"
LABEL version="2.0.0"

# Variables build
ARG ENVIRONMENT=production
ARG BUILD_DATE
ARG VCS_REF

# Installer dépendances système
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Créer utilisateur non-root
RUN useradd --create-home --shell /bin/bash app

# Répertoire de travail
WORKDIR /app

# Copier requirements
COPY backend/requirements.txt ./

# Installer dépendances Python
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copier code source
COPY backend/ ./

# Variables d'environnement
ENV ENVIRONMENT=$ENVIRONMENT
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# =============================================================================
# 🚀 STAGE 3: Production Runtime
# =============================================================================
FROM nginx:alpine AS production

# Métadonnées finales
LABEL maintainer="Smart Irrigation Team"
LABEL description="Smart Irrigation System - Production Container"
LABEL version="2.0.0"
LABEL build-date=$BUILD_DATE
LABEL vcs-ref=$VCS_REF

# Installer Python et dépendances runtime
RUN apk add --no-cache \
    python3 \
    py3-pip \
    supervisor \
    curl \
    bash \
    postgresql-client \
    redis \
    && rm -rf /var/cache/apk/*

# Créer structure de répertoires
RUN mkdir -p /app/frontend /app/backend /app/logs /var/log/supervisor

# Copier build frontend depuis stage 1
COPY --from=frontend-builder /app/build /app/frontend/build

# Copier backend depuis stage 2
COPY --from=backend-builder /app /app/backend
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# Copier configurations
COPY nginx.conf /etc/nginx/nginx.conf
COPY config/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Scripts de démarrage
COPY scripts/entrypoint.sh /app/entrypoint.sh
COPY scripts/healthcheck.sh /app/healthcheck.sh
RUN chmod +x /app/entrypoint.sh /app/healthcheck.sh

# Variables d'environnement
ENV PYTHONPATH=/app/backend
ENV PYTHONUNBUFFERED=1
ENV NGINX_ENVSUBST_TEMPLATE_DIR=/etc/nginx/templates
ENV NGINX_ENVSUBST_OUTPUT_DIR=/etc/nginx

# Exposition des ports
EXPOSE 80 443 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD /app/healthcheck.sh

# Point d'entrée
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]

# =============================================================================
# 🐳 ALTERNATIVE: Développement avec Docker Compose
# =============================================================================
# Utiliser docker-compose.yml pour développement
# Ce Dockerfile est optimisé pour production avec build multi-stage