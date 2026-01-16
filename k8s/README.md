# Kubernetes Deployment Guide

Guide to deploy Music Charts Tracking on Kubernetes.

## Prerequisites

1. Kubernetes cluster (1.24+)
   - minikube/kind or cloud
   - kubectl working

2. Docker images
   - build and push, or use local images

3. Required parts
   - ingress controller (optional)
   - storageclass for PV

## Architecture

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

## Quick Start

### Option 1: run script

```bash
chmod +x k8s/deploy.sh
./k8s/deploy.sh
```

### Option 2: manual steps

1. Create namespace
   ```bash
   kubectl apply -f k8s/namespace.yaml
   ```

2. Create secrets and configmaps
   ```bash
   kubectl apply -f k8s/secrets.yaml
   kubectl apply -f k8s/configmaps.yaml
   ```

3. Deploy databases
   ```bash
   kubectl apply -f k8s/postgres/
   kubectl apply -f k8s/mongodb/
   kubectl apply -f k8s/redis/
   ```

4. Wait for databases
   ```bash
   kubectl wait --for=condition=ready pod -l app=postgres -n music-charts --timeout=120s
   kubectl wait --for=condition=ready pod -l app=mongodb -n music-charts --timeout=120s
   kubectl wait --for=condition=ready pod -l app=redis -n music-charts --timeout=60s
   ```

5. Deploy app
   ```bash
   kubectl apply -f k8s/api/
   kubectl apply -f k8s/dashboard/
   ```

6. Deploy ingress (optional)
   ```bash
   kubectl apply -f k8s/ingress/
   ```

## Building and Pushing Docker Images

Build and push images before deploy.

### Local dev (minikube/kind)

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

### Prod (registry)

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

## Verification

### Check deploy status

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

### View logs

```bash
# API logs
kubectl logs -f deployment/api -n music-charts

# Dashboard logs
kubectl logs -f deployment/dashboard -n music-charts

# Database logs
kubectl logs -f statefulset/postgres -n music-charts
kubectl logs -f statefulset/mongodb -n music-charts
```

### Test connect

**Option 1: port forward scripts**

```bash
# Interactive mode (press Ctrl+C to stop)
./k8s/port-forward.sh

# Background mode (runs in background)
./k8s/port-forward-background.sh

# Stop background port forwarding
./k8s/stop-port-forward.sh
```

**Option 2: manual port forward**

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

## Configuration

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

## Security Considerations

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

## Persistent Storage

StatefulSets (PostgreSQL, MongoDB, Redis) use PersistentVolumeClaims:
- PostgreSQL: 10Gi
- MongoDB: 20Gi
- Redis: 5Gi

Ensure your cluster has a StorageClass configured:
```bash
kubectl get storageclass
```

## Updating Deployment

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

## Restarting After Docker Restart

When Docker Desktop restarts, Kubernetes pods don't automatically come back. Use these scripts:

### Full Restart (Recommended)

```bash
# Full redeployment (checks status, redeploys if needed)
./k8s/restart.sh
```

This script:
- Checks if cluster is accessible
- Verifies pod status
- Redeploys everything if pods are missing/not running
- Waits for services to be ready

### Quick Restart (If Deployments Exist)

```bash
# Fast restart of existing pods
./k8s/quick-start.sh
```

This script:
- Restarts deployments (triggers pod recreation)
- Deletes StatefulSet pods (they auto-recreate)
- Faster than full redeployment

### Manual Restart

```bash
# Restart specific deployments
kubectl rollout restart deployment/api -n music-charts
kubectl rollout restart deployment/dashboard -n music-charts

# Restart StatefulSets (delete pods, they auto-recreate)
kubectl delete pod -l app=postgres -n music-charts
kubectl delete pod -l app=mongodb -n music-charts
kubectl delete pod -l app=redis -n music-charts

# Wait for pods to be ready
kubectl wait --for=condition=ready pod -l app=postgres -n music-charts --timeout=120s
kubectl wait --for=condition=ready pod -l app=mongodb -n music-charts --timeout=120s
```

If the namespace or deployments are completely gone, use `./k8s/deploy.sh` instead.

## Stopping/Cleanup

### Stop Deployment (Recommended)

```bash
# Interactive script with options
./k8s/stop.sh
```

This script provides options to:
1. **Scale down to 0 replicas** (stops pods, keeps data) - Best for temporary shutdown
2. **Delete entire namespace** (removes everything including data) - Full cleanup
3. **Delete specific components** (API, Dashboard, or databases only)

### Manual Commands

```bash
# Scale down to 0 (stops pods, keeps data)
kubectl scale deployment api --replicas=0 -n music-charts
kubectl scale deployment dashboard --replicas=0 -n music-charts
kubectl scale statefulset postgres --replicas=0 -n music-charts
kubectl scale statefulset mongodb --replicas=0 -n music-charts
kubectl scale statefulset redis --replicas=0 -n music-charts

# Delete everything (removes all data)
kubectl delete namespace music-charts

# Or delete selectively
kubectl delete -f k8s/api/
kubectl delete -f k8s/dashboard/
kubectl delete -f k8s/postgres/
kubectl delete -f k8s/mongodb/
kubectl delete -f k8s/redis/
```

**Important Notes:**
- **Scaling to 0**: Pods stop, but all data and configurations are preserved. Use this for temporary shutdown.
- **Deleting namespace**: Removes everything including persistent volumes (unless they have reclaim policy "Retain"). Use this for full cleanup.

## Troubleshooting

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

## Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [StatefulSets](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/)
- [ConfigMaps and Secrets](https://kubernetes.io/docs/concepts/configuration/)
- [Horizontal Pod Autoscaler](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)

## Production Best Practices

1. **Monitoring**: Set up Prometheus and Grafana
2. **Logging**: Use centralized logging (ELK, Loki)
3. **Backups**: Schedule regular database backups
4. **Disaster Recovery**: Test restore procedures
5. **CI/CD**: Automate deployments via GitOps
6. **Health Checks**: Monitor liveness and readiness
7. **Resource Management**: Set appropriate limits
8. **Network Policies**: Implement security policies

