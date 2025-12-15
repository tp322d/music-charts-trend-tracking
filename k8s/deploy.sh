#!/bin/bash
# Kubernetes Deployment Script for Music Charts Tracking
# This script deploys the entire application to Kubernetes

set -e

echo "🚀 Starting Kubernetes Deployment for Music Charts Tracking"
echo "============================================================"

# Check if images need to be loaded
echo ""
echo "📦 Docker Image Check"
echo "--------------------"
if ! docker images | grep -q "music-charts-api"; then
    echo "⚠️  API image not found. Building..."
    docker build -t music-charts-api:latest ./api
    echo "✅ API image built"
else
    echo "✅ API image found locally"
fi

if ! docker images | grep -q "music-charts-dashboard"; then
    echo "⚠️  Dashboard image not found. Building..."
    docker build -t music-charts-dashboard:latest ./dashboard
    echo "✅ Dashboard image built"
else
    echo "✅ Dashboard image found locally"
fi

# Try to detect Kubernetes type and load images
if command -v minikube &> /dev/null && minikube status &> /dev/null; then
    echo "🔵 Detected Minikube - Loading images..."
    minikube image load music-charts-api:latest || echo "⚠️  Failed to load API image into Minikube"
    minikube image load music-charts-dashboard:latest || echo "⚠️  Failed to load Dashboard image into Minikube"
elif command -v kind &> /dev/null; then
    CLUSTER=$(kind get clusters 2>/dev/null | head -1)
    if [ ! -z "$CLUSTER" ]; then
        echo "🔵 Detected Kind - Loading images into cluster: $CLUSTER..."
        kind load docker-image music-charts-api:latest --name $CLUSTER || echo "⚠️  Failed to load API image into Kind"
        kind load docker-image music-charts-dashboard:latest --name $CLUSTER || echo "⚠️  Failed to load Dashboard image into Kind"
    else
        echo "ℹ️  Kind not found or no clusters running. Assuming Docker Desktop or remote cluster."
    fi
else
    echo "ℹ️  Minikube/Kind not detected. Assuming Docker Desktop or remote cluster."
    echo "   For Docker Desktop: Images are automatically available"
    echo "   For remote clusters: Make sure images are pushed to your container registry"
fi
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl is not installed. Please install kubectl first.${NC}"
    exit 1
fi

# Check if we can connect to cluster
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}❌ Cannot connect to Kubernetes cluster. Please check your kubeconfig.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ kubectl is available and cluster is accessible${NC}"
echo ""

# Step 1: Create namespace
echo -e "${YELLOW}Step 1/8: Creating namespace...${NC}"
kubectl apply -f k8s/namespace.yaml
echo -e "${GREEN}✅ Namespace created${NC}"
echo ""

# Step 2: Create secrets
echo -e "${YELLOW}Step 2/8: Creating secrets...${NC}"
kubectl apply -f k8s/secrets.yaml
echo -e "${GREEN}✅ Secrets created${NC}"
echo ""

# Step 3: Create configmaps
echo -e "${YELLOW}Step 3/8: Creating configmaps...${NC}"
kubectl apply -f k8s/configmaps.yaml
echo -e "${GREEN}✅ ConfigMaps created${NC}"
echo ""

# Step 4: Deploy PostgreSQL
echo -e "${YELLOW}Step 4/8: Deploying PostgreSQL...${NC}"
kubectl apply -f k8s/postgres/
echo -e "${GREEN}✅ PostgreSQL deployment initiated${NC}"

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres -n music-charts --timeout=120s || {
    echo -e "${YELLOW}⚠️  PostgreSQL might still be starting. Continuing...${NC}"
}
echo ""

# Step 5: Deploy MongoDB
echo -e "${YELLOW}Step 5/8: Deploying MongoDB...${NC}"
kubectl apply -f k8s/mongodb/
echo -e "${GREEN}✅ MongoDB deployment initiated${NC}"

# Wait for MongoDB to be ready
echo "Waiting for MongoDB to be ready..."
kubectl wait --for=condition=ready pod -l app=mongodb -n music-charts --timeout=120s || {
    echo -e "${YELLOW}⚠️  MongoDB might still be starting. Continuing...${NC}"
}
echo ""

# Step 6: Deploy Redis
echo -e "${YELLOW}Step 6/8: Deploying Redis...${NC}"
kubectl apply -f k8s/redis/
echo -e "${GREEN}✅ Redis deployment initiated${NC}"

# Wait for Redis to be ready
echo "Waiting for Redis to be ready..."
kubectl wait --for=condition=ready pod -l app=redis -n music-charts --timeout=60s || {
    echo -e "${YELLOW}⚠️  Redis might still be starting. Continuing...${NC}"
}
echo ""

# Step 7: Deploy API and Dashboard
echo -e "${YELLOW}Step 7/8: Deploying API and Dashboard...${NC}"
kubectl apply -f k8s/api/
kubectl apply -f k8s/dashboard/
echo -e "${GREEN}✅ API and Dashboard deployments initiated${NC}"

# Wait for API to be ready
echo "Waiting for API to be ready..."
kubectl wait --for=condition=available deployment/api -n music-charts --timeout=180s || {
    echo -e "${YELLOW}⚠️  API might still be starting. Check status with: kubectl get pods -n music-charts${NC}"
}

# Wait for Dashboard to be ready
echo "Waiting for Dashboard to be ready..."
kubectl wait --for=condition=available deployment/dashboard -n music-charts --timeout=120s || {
    echo -e "${YELLOW}⚠️  Dashboard might still be starting. Check status with: kubectl get pods -n music-charts${NC}"
}
echo ""

# Step 8: Deploy Ingress (optional)
echo -e "${YELLOW}Step 8/8: Deploying Ingress...${NC}"
kubectl apply -f k8s/ingress/ || {
    echo -e "${YELLOW}⚠️  Ingress deployment skipped (might need ingress controller)${NC}"
}
echo ""

# Display status
echo -e "${GREEN}============================================================"
echo "✅ Deployment Complete!"
echo "============================================================${NC}"
echo ""
echo "📊 Deployment Status:"
kubectl get all -n music-charts
echo ""
echo "📝 Useful Commands:"
echo "  View pods:           kubectl get pods -n music-charts"
echo "  View services:       kubectl get svc -n music-charts"
echo "  View logs (API):     kubectl logs -f deployment/api -n music-charts"
echo "  View logs (Dashboard): kubectl logs -f deployment/dashboard -n music-charts"
echo "  Port forward (both): ./k8s/port-forward.sh"
echo "  Port forward (bg):   ./k8s/port-forward-background.sh"
echo "  Stop port forward:   ./k8s/stop-port-forward.sh"
echo "  Delete all:          kubectl delete namespace music-charts"
echo ""

