# Music Charts Trend Tracking API

Simple API that tracks daily music chart data. It stores history and shows trends.

## Prerequisites

- Docker and Docker Compose (local)
- Kubernetes cluster (prod)
- kubectl (for k8s)

## Architecture

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

- API (FastAPI): REST API + auth
- Dashboard (Streamlit): UI
- PostgreSQL: users/auth
- MongoDB: chart data
- TimescaleDB: optional analytics
- Redis: cache/rate limit

### Data Flow

1. iTunes → API → MongoDB (chart entries)
2. User requests → API → Postgres auth → MongoDB data
3. API → Dashboard for charts
4. WebSocket for live updates

## Setup

### Local Development (Docker Compose)

1. **Start all services**
   ```bash
   docker-compose up -d
   ```

2. **Check services**
   ```bash
   docker-compose ps
   # expect "Up"
   ```

3. **Check API health**
   ```bash
   curl http://localhost:8000/health
   # expect {"status":"healthy","service":"music-charts-api"}
   ```

4. **Open services**
   - **API Documentation**: http://localhost:8000/docs
   - **Dashboard**: http://localhost:8501
   - **API**: http://localhost:8000

5. **Create a user** (API or Dashboard)
   ```bash
   curl -X POST "http://localhost:8000/api/v1/auth/register" \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","email":"admin@example.com","password":"admin123","role":"admin"}'
   ```

### Environment Variables

For Docker Compose, env vars are in `compose.yml`. For Kubernetes, see deploy section.

Key variables:
- `DATABASE_URL`: PostgreSQL connection string
- `MONGODB_URL`: MongoDB connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: JWT signing key (minimum 32 characters)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time

## Deployment

### Kubernetes Deployment

#### Quick Start (Automated)

```bash
chmod +x k8s/deploy.sh
./k8s/deploy.sh
```

Script does:
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

2. **Load images into cluster** (local only)
   ```bash
   # Docker Desktop Kubernetes (automatic)
   # Minikube
   minikube image load music-charts-api:latest
   minikube image load music-charts-dashboard:latest
   # Kind
   kind load docker-image music-charts-api:latest --name <cluster-name>
   kind load docker-image music-charts-dashboard:latest --name <cluster-name>
   ```

   For prod: push to registry and update image names in YAMLs

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

Services are `ClusterIP`, use port-forward for local access:

```bash
# Option 1: Use the port-forward script
chmod +x k8s/port-forward.sh
./k8s/port-forward.sh

# Option 2: Manual port-forward
kubectl port-forward svc/api 8000:8000 -n music-charts
kubectl port-forward svc/dashboard 8501:8501 -n music-charts
```

Then open:
- **API**: http://localhost:8000/docs
- **Dashboard**: http://localhost:8501

#### Verify Deployment

```bash
# all resources
kubectl get all -n music-charts

# pod status
kubectl get pods -n music-charts

# logs
kubectl logs -f deployment/api -n music-charts
kubectl logs -f deployment/dashboard -n music-charts
```

#### Cleanup

```bash
kubectl delete namespace music-charts
```

## Project Structure

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

## Security

- OAuth2 JWT
- bcrypt passwords
- roles (admin/editor/viewer)
- secrets in env vars
- input validation
