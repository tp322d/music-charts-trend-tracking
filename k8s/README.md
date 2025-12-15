# Kubernetes Deployment Guide

Complete guide for deploying the Music Charts Tracking application to Kubernetes.

## 📋 Prerequisites

1. **Kubernetes Cluster** (1.24+)
   - Minikube, Kind, or cloud provider (GKE, EKS, AKS)
   - kubectl configured and connected

2. **Docker Images**
   - Build and push images to a container registry
   - Or use local images (for minikube/kind)

3. **Required Components**
   - Ingress Controller (optional, for external access)
   - StorageClass (for persistent volumes)

## 🏗️ Architecture

```
┌─────────────┐
│   Ingress   │ (Optional - nginx ingress)
└──────┬──────┘
       │
       ├──────────────┬──────────────┐
       ▼              ▼              ▼
┌──────────┐    ┌──────────┐   ┌──────────┐
│   API    │    │ Dashboard│   │          │
│  (3 pods)│    │ (2 pods) │   │          │
│ FastAPI  │    │Streamlit │   │          │
└────┬─────┘    └─────┬────┘   └──────────┘
     │                │
     ├────────┬───────┼────────┬─────────┐
     ▼        ▼       ▼        ▼         ▼
┌────────┐┌────────┐┌────────┐┌──────┐┌──────┐
│Postgres││ MongoDB││        ││ Redis││      │
│Stateful││Stateful││        ││Stateful││      │
│  (1)   ││  (1)   ││        ││  (1) ││      │
└────────┘└────────┘└────────┘└──────┘└──────┘
```

## 🚀 Quick Start

### Option 1: Automated Deployment (Recommended)

```bash
chmod +x k8s/deploy.sh
./k8s/deploy.sh
```

### Option 2: Manual Deployment

1. **Create Namespace**
   ```bash
   kubectl apply -f k8s/namespace.yaml
   ```

2. **Create Secrets and ConfigMaps**
   ```bash
   kubectl apply -f k8s/secrets.yaml
   kubectl apply -f k8s/configmaps.yaml
   ```

3. **Deploy Databases**
   ```bash
   kubectl apply -f k8s/postgres/
   kubectl apply -f k8s/mongodb/
   kubectl apply -f k8s/redis/
   ```

4. **Wait for Databases**
   ```bash
   kubectl wait --for=condition=ready pod -l app=postgres -n music-charts --timeout=120s
   kubectl wait --for=condition=ready pod -l app=mongodb -n music-charts --timeout=120s
   kubectl wait --for=condition=ready pod -l app=redis -n music-charts --timeout=60s
   ```

5. **Deploy Application**
   ```bash
   kubectl apply -f k8s/api/
   kubectl apply -f k8s/dashboard/
   ```

6. **Deploy Ingress (Optional)**
   ```bash
   kubectl apply -f k8s/ingress/
   ```

## 📦 Building and Pushing Docker Images

Before deploying, you need to build and push your Docker images:

### For Local Development (Minikube/Kind)

```bash
# Build locally
docker build -t music-charts-api:latest ./api
docker build -t music-charts-dashboard:latest ./dashboard

# For Minikube
minikube image load music-charts-api:latest
minikube image load music-charts-dashboard:latest

# For Kind
kind load docker-image music-charts-api:latest
kind load docker-image music-charts-dashboard:latest
```

### For Production (Container Registry)

```bash
# Set your registry
REGISTRY="your-registry.io/music-charts"

# Build and tag
docker build -t ${REGISTRY}/api:latest ./api
docker build -t ${REGISTRY}/dashboard:latest ./dashboard

# Push
docker push ${REGISTRY}/api:latest
docker push ${REGISTRY}/dashboard:latest

# Update deployments
sed -i "s|image: music-charts-api:latest|image: ${REGISTRY}/api:latest|g" k8s/api/deployment.yaml
sed -i "s|image: music-charts-dashboard:latest|image: ${REGISTRY}/dashboard:latest|g" k8s/dashboard/deployment.yaml
```

## 🔍 Verification

### Check Deployment Status

```bash
# View all resources
kubectl get all -n music-charts

# Check pods
kubectl get pods -n music-charts

# Check services
kubectl get svc -n music-charts

# Check ingress
kubectl get ingress -n music-charts
```

### View Logs

```bash
# API logs
kubectl logs -f deployment/api -n music-charts

# Dashboard logs
kubectl logs -f deployment/dashboard -n music-charts

# Database logs
kubectl logs -f statefulset/postgres -n music-charts
kubectl logs -f statefulset/mongodb -n music-charts
```

### Test Connectivity

**Option 1: Automatic Port Forwarding (Recommended)**

```bash
# Interactive mode (press Ctrl+C to stop)
./k8s/port-forward.sh

# Background mode (runs in background)
./k8s/port-forward-background.sh

# Stop background port forwarding
./k8s/stop-port-forward.sh
```

**Option 2: Manual Port Forwarding**

```bash
# Port forward to test locally
kubectl port-forward svc/api 8000:8000 -n music-charts &
kubectl port-forward svc/dashboard 8501:8501 -n music-charts &

# Test API
curl http://localhost:8000/health

# Access dashboard
open http://localhost:8501
```

**Access URLs:**
- API: http://localhost:8000
- API Health: http://localhost:8000/health
- API Docs: http://localhost:8000/docs
- Dashboard: http://localhost:8501

## ⚙️ Configuration

### Environment Variables

All configuration is managed through:
- **ConfigMaps**: Non-sensitive configuration
- **Secrets**: Sensitive data (passwords, keys)

### Resource Limits

Default resource allocation:

| Component | Requests | Limits |
|-----------|----------|--------|
| API | 256Mi / 250m | 512Mi / 500m |
| Dashboard | 256Mi / 250m | 512Mi / 500m |
| PostgreSQL | 512Mi / 500m | 1Gi / 1000m |
| MongoDB | 1Gi / 500m | 2Gi / 2000m |
| Redis | 128Mi / 100m | 256Mi / 200m |

Adjust in respective deployment files if needed.

### Scaling

The API includes Horizontal Pod Autoscaler (HPA):
- Min replicas: 3
- Max replicas: 10
- CPU target: 70%
- Memory target: 80%

View HPA status:
```bash
kubectl get hpa -n music-charts
```

## 🔐 Security Considerations

### Production Checklist

1. **Change Default Secrets**
   - Update `k8s/secrets.yaml` with strong passwords
   - Use a secrets management tool (Vault, Sealed Secrets)

2. **Update SECRET_KEY**
   - Generate a strong secret key (min 32 chars)
   - Use: `openssl rand -hex 32`

3. **Enable TLS**
   - Configure cert-manager for automatic certificates
   - Update ingress annotations

4. **Network Policies**
   - Implement network policies to restrict traffic
   - Only allow necessary connections

5. **RBAC**
   - Use service accounts with minimal permissions
   - Avoid default service accounts

6. **Image Security**
   - Scan images for vulnerabilities
   - Use private registries
   - Enable image pull secrets if needed

## 🗄️ Persistent Storage

StatefulSets (PostgreSQL, MongoDB, Redis) use PersistentVolumeClaims:
- PostgreSQL: 10Gi
- MongoDB: 20Gi
- Redis: 5Gi

Ensure your cluster has a StorageClass configured:
```bash
kubectl get storageclass
```

## 🔄 Updating Deployment

### Rolling Update

```bash
# Update image
kubectl set image deployment/api api=music-charts-api:v2.0.0 -n music-charts

# Or edit deployment
kubectl edit deployment/api -n music-charts
```

### Rolling Back

```bash
# View rollout history
kubectl rollout history deployment/api -n music-charts

# Rollback to previous version
kubectl rollout undo deployment/api -n music-charts
```

## 🧹 Cleanup

### Delete Deployment

```bash
# Delete everything
kubectl delete namespace music-charts

# Or delete selectively
kubectl delete -f k8s/api/
kubectl delete -f k8s/dashboard/
kubectl delete -f k8s/postgres/
kubectl delete -f k8s/mongodb/
kubectl delete -f k8s/redis/
kubectl delete -f k8s/secrets.yaml
kubectl delete -f k8s/configmaps.yaml
kubectl delete -f k8s/namespace.yaml
```

**Note:** Deleting the namespace removes all resources including persistent volumes (unless they have reclaim policy "Retain").

## 🐛 Troubleshooting

### Pods Not Starting

```bash
# Describe pod to see events
kubectl describe pod <pod-name> -n music-charts

# Check logs
kubectl logs <pod-name> -n music-charts

# Common issues:
# - Image pull errors: Check image name and registry
# - Init container errors: Check database connectivity
# - Resource constraints: Check resource limits
```

### Database Connection Issues

```bash
# Test database connectivity from API pod
kubectl exec -it deployment/api -n music-charts -- bash
# Inside pod:
# psql $DATABASE_URL
# mongosh $MONGODB_URL
```

### Service Discovery

```bash
# Test DNS resolution
kubectl run -it --rm debug --image=busybox --restart=Never -n music-charts -- nslookup postgres
kubectl run -it --rm debug --image=busybox --restart=Never -n music-charts -- nslookup mongodb
```

### Performance Issues

```bash
# Check resource usage
kubectl top pods -n music-charts
kubectl top nodes

# Check HPA status
kubectl describe hpa api-hpa -n music-charts
```

## 📚 Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [StatefulSets](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/)
- [ConfigMaps and Secrets](https://kubernetes.io/docs/concepts/configuration/)
- [Horizontal Pod Autoscaler](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)

## 🎯 Production Best Practices

1. **Monitoring**: Set up Prometheus and Grafana
2. **Logging**: Use centralized logging (ELK, Loki)
3. **Backups**: Schedule regular database backups
4. **Disaster Recovery**: Test restore procedures
5. **CI/CD**: Automate deployments via GitOps
6. **Health Checks**: Monitor liveness and readiness
7. **Resource Management**: Set appropriate limits
8. **Network Policies**: Implement security policies

