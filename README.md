# 🌱 Smart Irrigation System - MVP Complet

Système d'irrigation intelligente moderne avec interface React, authentification, API REST et intégration IoT pour serres maraîchères - Hackathon Agadir 2025

## 🎯 Objectifs

- **Calcul automatique** des besoins en eau (FAO-56)
- **Interface React moderne** avec authentification
- **API REST complète** avec WebSocket temps réel
- **Gestion IoT** des capteurs et actionneurs
- **Contrôle intelligent** du climat (VPD, ouvrants, ombrage) 
- **Économie d'eau** cible: **20-25%** vs baseline
- **Déploiement Docker** production-ready

## 📋 Fonctionnalités

### 🔐 Authentification & Sécurité
- Login/logout avec JWT tokens
- Gestion des rôles (Admin, Agriculteur, Observateur)
- Sécurisation API avec middleware
- Session management

### 📊 Dashboard Temps Réel
- KPIs temps réel (économie eau, VPD, ETc)
- Graphiques interactifs avec Chart.js
- Notifications push WebSocket
- Vue mobile responsive

### 🌱 Gestion Irrigation
- Calcul ET0/ETc selon FAO-56 (Penman-Monteith)
- Bilan hydrique temps réel par secteur
- Système semi-automatique avec confirmation
- Programmation horaires d'irrigation

### 🌡️ Contrôle Climat
- Calcul VPD et règles intelligentes
- Alertes climat (température, humidité, radiation)
- Contrôle automatique ouvrants/ombrage
- Historique conditions climatiques

### 📡 Intégration IoT
- Communication MQTT avec capteurs
- Gestion débitmètres et électrovannes
- Monitoring état équipements
- Configuration capteurs à distance

### 📈 Analytics & Reporting
- Historique complet événements
- Exports CSV/Excel/PDF
- Rapports automatiques
- Statistiques consommation

## 🏗️ Architecture

```
smart-irrigation-system/
├── 🐳 docker-compose.yml           # Orchestration containers
├── 📋 .env.example                 # Variables environnement
├── 🔧 nginx.conf                   # Configuration reverse proxy
│
├── 🖥️ frontend/                    # React Frontend
│   ├── 📦 package.json
│   ├── 🐳 Dockerfile
│   ├── ⚙️ src/
│   │   ├── 🔐 components/auth/
│   │   ├── 📊 components/dashboard/
│   │   ├── 🌱 components/irrigation/
│   │   ├── 🌡️ components/climate/
│   │   ├── 📱 components/mobile/
│   │   └── 🎨 styles/
│   └── 🏗️ public/
│
├── 🚀 backend/                     # FastAPI Backend
 │   ├── 📋 requirements.txt
│   ├── 🐳 Dockerfile
│   ├── 🔧 app/
│   │   ├── 🔐 auth/                # JWT authentification
│   │   ├── 📊 api/                 # Routes API REST
│   │   ├── 🌱 core/                # Moteurs calcul (FAO-56, VPD)
│   │   ├── 📡 iot/                 # Intégration IoT/MQTT
│   │   ├── 🗄️ database/            # Models & ORM
│   │   ├── ⚡ websocket/           # Communication temps réel
│   │   └── 🧪 tests/
│   └── 📋 alembic/                 # Migrations DB
│
├── 📡 iot-bridge/                  # Service IoT
│   ├── 🐳 Dockerfile
│   ├── 📋 requirements.txt
│   ├── 📡 mqtt_client.py
│   ├── 📊 sensor_manager.py
│   └── 🔧 device_controller.py
│
├── 🗄️ database/
│   ├── 🐘 init.sql                 # Schema initial
│   └── 📊 seed_data.sql           # Données test
│
├── 📋 k8s/                        # Kubernetes (optionnel)
│   ├── ⚙️ configmaps/
│   ├── 🔧 deployments/
│   └── 🔗 services/
│
└── 📖 docs/
    ├── 🏗️ ARCHITECTURE.md
    ├── 🚀 DEPLOYMENT.md
    ├── 📡 IOT_INTEGRATION.md
    └── 👥 USER_GUIDE.md
```

## 🚀 Installation & Déploiement

### Prérequis
- Docker & Docker Compose
- Node.js 18+ (développement)
- Python 3.11+ (développement)

### 🐳 Déploiement Docker (Recommandé)

1. **Cloner le projet**
```bash
git clone https://github.com/Amine-Charrou/smart-irrigation-system.git
cd smart-irrigation-system
```

2. **Configuration environnement**
```bash
cp .env.example .env
# Éditer .env avec vos paramètres
```

3. **Lancer avec Docker Compose**
```bash
docker-compose up -d
```

4. **Initialiser la base de données**
```bash
docker-compose exec backend python -m alembic upgrade head
docker-compose exec backend python scripts/seed_data.py
```

5. **Accéder à l'application**
- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### 👩‍💻 Développement Local

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm start
```

## 🔧 Configuration

### Variables d'environnement
```env
# Base de données
DATABASE_URL=postgresql://user:pass@postgres:5432/irrigation

# JWT
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# MQTT
MQTT_BROKER=mosquitto
MQTT_PORT=1883
MQTT_USERNAME=admin
MQTT_PASSWORD=password

# Redis (Cache & Sessions)
REDIS_URL=redis://redis:6379/0
```

### 📡 Configuration IoT
```json
{
  "sectors": [
    {
      "id": 1,
      "name": "Secteur Tomates",
      "area": 1000,
      "sensors": {
        "soil_moisture": "topic/sector1/soil",
        "temperature": "topic/sector1/temp",
        "humidity": "topic/sector1/hum"
      },
      "actuators": {
        "valve": "topic/sector1/valve",
        "ventilation": "topic/sector1/vent"
      }
    }
  ]
}
```

## 📊 Utilisation

### 1. Connexion
- Créer un compte ou se connecter
- Choisir son rôle (Admin/Agriculteur)

### 2. Configuration Initiale
- Paramétrer les secteurs de serre
- Configurer les capteurs IoT
- Définir les seuils d'alerte

### 3. Dashboard
- Visualiser KPIs temps réel
- Monitoring des secteurs
- Alertes et notifications

### 4. Irrigation
- Consulter recommandations automatiques
- Confirmer ou programmer irrigations
- Suivre historique consommation

### 5. Climat
- Surveiller conditions VPD
- Contrôler ouvrants/ombrage
- Recevoir alertes climatiques

## 🧪 Tests

```bash
# Tests backend
cd backend
pytest app/tests/ -v --cov=app

# Tests frontend
cd frontend
npm test
```

## 📈 Monitoring & Logs

- **Logs**: `docker-compose logs -f [service]`
- **Métriques**: Prometheus + Grafana (optionnel)
- **Santé**: Health checks intégrés

## 🔒 Sécurité

- Authentification JWT avec refresh tokens
- HTTPS obligatoire en production
- Rate limiting API
- Validation inputs avec Pydantic
- CORS configuré

## 🤝 Contribution

1. Fork le projet
2. Créer une branche (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Commit (`git commit -m 'Ajouter fonctionnalité'`)
4. Push (`git push origin feature/nouvelle-fonctionnalite`)
5. Ouvrir une Pull Request

## 📄 Licence

MIT License - voir [LICENSE](LICENSE)

## 👥 Équipe

Développé pour le **Hackathon Agadir 2025**

---

**🎯 Objectif**: Révolutionner l'irrigation des serres Souss-Massa avec 20-25% d'économie d'eau  
**📊 Status**: MVP Production-Ready  
**🐳 Déploiement**: Docker & Kubernetes  
**🔄 Version**: 2.0.0