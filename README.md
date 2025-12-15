# Music Charts Trend Tracking API

A containerized REST API service that tracks daily music chart data from streaming platforms, providing historical analysis and trend insights.

## 📋 Prerequisites

- **Docker and Docker Compose** (for local development)
- **Kubernetes cluster** (for production deployment)
- **kubectl** (for Kubernetes deployment)

## 🏗️ Architecture

### System Overview

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Ingress   │ (Optional - for external access)
└──────┬──────┘
       │
       ├──────────────┬──────────────┐
       ▼              ▼              ▼
┌──────────┐    ┌──────────┐   ┌──────────┐
│   API    │    │ Dashboard│   │ WebSocket│
│  FastAPI │    │Streamlit │   │   (WS)   │
└────┬─────┘    └─────┬────┘   └──────────┘
     │                │
     ├────────┬───────┼────────┬─────────┐
     ▼        ▼       ▼        ▼         ▼
┌────────┐┌────────┐┌────────┐┌──────┐┌──────┐
│Postgres││ MongoDB││Timescale││ Redis││      │
│        ││ (NoSQL)││   DB    ││      ││      │
└────────┘└────────┘└────────┘└──────┘└──────┘
```

### Components

- **API (FastAPI)**: RESTful API with OAuth2 authentication, handles chart data operations
- **Dashboard (Streamlit)**: Web-based visualization interface
- **PostgreSQL**: Relational database for user management and authentication
- **MongoDB**: NoSQL database for flexible chart data storage
- **TimescaleDB**: Time-series database for analytics (configured but optional)
- **Redis**: Caching and rate limiting

### Data Flow

1. External APIs (iTunes Charts) → API Service → MongoDB (chart entries)
2. User requests → API Service → PostgreSQL (authentication) → MongoDB (data retrieval)
3. API → Dashboard (Streamlit) for visualization
4. WebSocket connections for real-time updates

## 🚀 Setup

### Local Development (Docker Compose)

1. **Start all services**
   ```bash
   docker-compose up -d
   ```

2. **Verify services are running**
   ```bash
   docker-compose ps
   # All services should show "Up" status
   ```

3. **Check API health**
   ```bash
   curl http://localhost:8000/health
   # Should return: {"status":"healthy","service":"music-charts-api"}
   ```

4. **Access services**
   - **API Documentation**: http://localhost:8000/docs
   - **Dashboard**: http://localhost:8501
   - **API**: http://localhost:8000

5. **Create a user** (via API or Dashboard)
   ```bash
   curl -X POST "http://localhost:8000/api/v1/auth/register" \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","email":"admin@example.com","password":"admin123","role":"admin"}'
   ```

### Environment Variables

For Docker Compose, environment variables are configured in `compose.yml`. For Kubernetes, see the deployment section below.

Key variables:
- `DATABASE_URL`: PostgreSQL connection string
- `MONGODB_URL`: MongoDB connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: JWT signing key (minimum 32 characters)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time

## 🚢 Deployment

### Kubernetes Deployment

#### Quick Start (Automated)

```bash
chmod +x k8s/deploy.sh
./k8s/deploy.sh
```

This script will:
1. Build Docker images
2. Create Kubernetes namespace
3. Deploy secrets and configmaps
4. Deploy databases (PostgreSQL, MongoDB, Redis)
5. Deploy API and Dashboard
6. Wait for all pods to be ready

#### Manual Deployment

1. **Build Docker images**
   ```bash
   docker build -t music-charts-api:latest ./api
   docker build -t music-charts-dashboard:latest ./dashboard
   ```

2. **Load images into cluster** (for local clusters)
   ```bash
   # Docker Desktop Kubernetes (automatic)
   # Minikube
   minikube image load music-charts-api:latest
   minikube image load music-charts-dashboard:latest
   # Kind
   kind load docker-image music-charts-api:latest --name <cluster-name>
   kind load docker-image music-charts-dashboard:latest --name <cluster-name>
   ```

   **For production**: Push to container registry and update image names in deployment YAMLs

3. **Create namespace**
   ```bash
   kubectl apply -f k8s/namespace.yaml
   ```

4. **Create secrets and configmaps**
   ```bash
   kubectl apply -f k8s/secrets.yaml
   kubectl apply -f k8s/configmaps.yaml
   ```

5. **Deploy databases**
   ```bash
   kubectl apply -f k8s/postgres/
   kubectl apply -f k8s/mongodb/
   kubectl apply -f k8s/redis/
   ```

6. **Wait for databases to be ready**
   ```bash
   kubectl wait --for=condition=ready pod -l app=postgres -n music-charts --timeout=180s
   kubectl wait --for=condition=ready pod -l app=mongodb -n music-charts --timeout=180s
   kubectl wait --for=condition=ready pod -l app=redis -n music-charts --timeout=120s
   ```

7. **Deploy application**
   ```bash
   kubectl apply -f k8s/api/
   kubectl apply -f k8s/dashboard/
   ```

8. **Deploy ingress** (optional)
   ```bash
   kubectl apply -f k8s/ingress/
   ```

#### Access Services in Kubernetes

Since services use `ClusterIP` type, use port-forwarding for local access:

```bash
# Option 1: Use the port-forward script
chmod +x k8s/port-forward.sh
./k8s/port-forward.sh

# Option 2: Manual port-forward
kubectl port-forward svc/api 8000:8000 -n music-charts
kubectl port-forward svc/dashboard 8501:8501 -n music-charts
```

Then access:
- **API**: http://localhost:8000/docs
- **Dashboard**: http://localhost:8501

#### Verify Deployment

```bash
# Check all resources
kubectl get all -n music-charts

# Check pod status
kubectl get pods -n music-charts

# View logs
kubectl logs -f deployment/api -n music-charts
kubectl logs -f deployment/dashboard -n music-charts
```

#### Cleanup

```bash
kubectl delete namespace music-charts
```

## 📁 Project Structure

```
.
├── api/                    # FastAPI application
│   ├── app/
│   │   ├── core/          # Configuration and dependencies
│   │   ├── database/      # Database connections
│   │   ├── models/        # SQLAlchemy models
│   │   ├── routers/       # API endpoints
│   │   ├── schemas/       # Pydantic schemas
│   │   └── services/      # Business logic
│   ├── Dockerfile
│   └── requirements.txt
├── dashboard/              # Streamlit dashboard
│   ├── dashboard.py
│   ├── Dockerfile
│   └── requirements.txt
├── k8s/                    # Kubernetes manifests
│   ├── api/
│   ├── dashboard/
│   ├── postgres/
│   ├── mongodb/
│   ├── redis/
│   ├── deploy.sh
│   └── port-forward.sh
├── compose.yml             # Docker Compose configuration
└── README.md
```

## 🔐 Security

- OAuth2 JWT authentication
- Password hashing with bcrypt
- Role-based access control (Admin, Editor, Viewer)
- Environment variables for sensitive data
- Input validation on all endpoints
