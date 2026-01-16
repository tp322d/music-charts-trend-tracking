#!/bin/bash
# Port Forward Script

set -e

NAMESPACE="music-charts"
API_PORT=8000
DASHBOARD_PORT=8501

# Colors
if ! command -v kubectl &> /dev/null; then
    echo "kubectl not installed"
    exit 1
fi

if ! kubectl get namespace $NAMESPACE &> /dev/null; then
    echo "namespace not found"
    echo "deploy first: ./k8s/deploy.sh"
    exit 1
fi

if ! kubectl get svc api -n $NAMESPACE &> /dev/null; then
    echo "api service not found"
    exit 1
fi

if ! kubectl get svc dashboard -n $NAMESPACE &> /dev/null; then
    echo "dashboard service not found"
    exit 1
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "stop port forward"
    kill $API_PID $DASHBOARD_PID 2>/dev/null || true
    wait $API_PID $DASHBOARD_PID 2>/dev/null || true
    echo "port forward stopped"
    exit 0
}

# Trap SIGINT and SIGTERM
trap cleanup SIGINT SIGTERM

echo "start port forward"
echo "====================="
echo ""
echo "forward from namespace: $NAMESPACE"
echo ""

# Start API port forward in background
echo "forward api: localhost:$API_PORT -> api:$API_PORT"
kubectl port-forward svc/api $API_PORT:$API_PORT -n $NAMESPACE > /dev/null 2>&1 &
API_PID=$!

# Small delay to ensure first port forward starts
sleep 1

# Start Dashboard port forward in background
echo "forward dashboard: localhost:$DASHBOARD_PORT -> dashboard:$DASHBOARD_PORT"
kubectl port-forward svc/dashboard $DASHBOARD_PORT:$DASHBOARD_PORT -n $NAMESPACE > /dev/null 2>&1 &
DASHBOARD_PID=$!

# Wait a moment to ensure both are running
sleep 2

if ps -p $API_PID > /dev/null && ps -p $DASHBOARD_PID > /dev/null; then
    echo ""
    echo "port forward ok"
    echo ""
    echo "access:"
    echo "   api:       http://localhost:$API_PORT"
    echo "   dashboard: http://localhost:$DASHBOARD_PORT"
    echo ""
    echo "   api health:  http://localhost:$API_PORT/health"
    echo "   api docs:    http://localhost:$API_PORT/docs"
    echo ""
    echo "press ctrl+c to stop"
    echo ""
    
    # Wait for both processes
    wait $API_PID $DASHBOARD_PID
else
    echo "port forward failed"
    cleanup
    exit 1
fi

