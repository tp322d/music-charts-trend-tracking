#!/bin/bash
set -e

echo "start deploy"
echo "==========="

echo ""
echo "image check"
echo "-----------"
if ! docker images | grep -q "music-charts-api"; then
    echo "api image not found, build"
    docker build -t music-charts-api:latest ./api
    echo "api image built"
else
    echo "api image ok"
fi

if ! docker images | grep -q "music-charts-dashboard"; then
    echo "dashboard image not found, build"
    docker build -t music-charts-dashboard:latest ./dashboard
    echo "dashboard image built"
else
    echo "dashboard image ok"
fi

if command -v minikube &> /dev/null && minikube status &> /dev/null; then
    echo "minikube found, load images"
    minikube image load music-charts-api:latest || echo "load api image failed"
    minikube image load music-charts-dashboard:latest || echo "load dashboard image failed"
elif command -v kind &> /dev/null; then
    CLUSTER=$(kind get clusters 2>/dev/null | head -1)
    if [ ! -z "$CLUSTER" ]; then
        echo "kind found, load images: $CLUSTER"
        kind load docker-image music-charts-api:latest --name $CLUSTER || echo "load api image failed"
        kind load docker-image music-charts-dashboard:latest --name $CLUSTER || echo "load dashboard image failed"
    else
        echo "kind not found or no cluster"
    fi
else
    echo "minikube/kind not found"
    echo "docker desktop: images ready"
    echo "remote cluster: push images first"
fi
echo ""

if ! command -v kubectl &> /dev/null; then
    echo "kubectl not installed"
    exit 1
fi

if ! kubectl cluster-info &> /dev/null; then
    echo "cannot connect to cluster"
    exit 1
fi

echo "kubectl ok"
echo ""

echo "step 1 create namespace"
kubectl apply -f k8s/namespace.yaml
echo "namespace done"
echo ""

echo "step 2 create secrets"
kubectl apply -f k8s/secrets.yaml
echo "secrets done"
echo ""

echo "step 3 create configmaps"
kubectl apply -f k8s/configmaps.yaml
echo "configmaps done"
echo ""

echo "step 4 deploy postgres"
kubectl apply -f k8s/postgres/
echo "postgres deploy start"

echo "wait postgres ready"
kubectl wait --for=condition=ready pod -l app=postgres -n music-charts --timeout=120s || {
    echo "postgres still starting, continue"
}
echo ""

echo "step 5 deploy mongodb"
kubectl apply -f k8s/mongodb/
echo "mongodb deploy start"

echo "wait mongodb ready"
kubectl wait --for=condition=ready pod -l app=mongodb -n music-charts --timeout=120s || {
    echo "mongodb still starting, continue"
}
echo ""

echo "step 6 deploy redis"
kubectl apply -f k8s/redis/
echo "redis deploy start"

echo "wait redis ready"
kubectl wait --for=condition=ready pod -l app=redis -n music-charts --timeout=60s || {
    echo "redis still starting, continue"
}
echo ""

echo "step 7 deploy api and dashboard"
kubectl apply -f k8s/api/
kubectl apply -f k8s/dashboard/
echo "api and dashboard deploy start"

echo "wait api ready"
kubectl wait --for=condition=available deployment/api -n music-charts --timeout=180s || {
    echo "api still starting, check pods"
}

echo "wait dashboard ready"
kubectl wait --for=condition=available deployment/dashboard -n music-charts --timeout=120s || {
    echo "dashboard still starting, check pods"
}
echo ""

echo "step 8 deploy ingress"
kubectl apply -f k8s/ingress/ || {
    echo "ingress skip or need controller"
}
echo ""

echo "==========="
echo "deploy done"
echo "==========="
echo ""
echo "status:"
kubectl get all -n music-charts
echo ""
echo "help:"
echo "  pods:      kubectl get pods -n music-charts"
echo "  services:  kubectl get svc -n music-charts"
echo "  logs api:  kubectl logs -f deployment/api -n music-charts"
echo "  logs dash: kubectl logs -f deployment/dashboard -n music-charts"
echo "  port fw:   ./k8s/port-forward.sh"
echo "  port bg:   ./k8s/port-forward-background.sh"
echo "  stop fw:   ./k8s/stop-port-forward.sh"
echo "  stop:      ./k8s/stop.sh"
echo "  restart:   ./k8s/restart.sh"
echo "  delete:    kubectl delete namespace music-charts"
echo ""

