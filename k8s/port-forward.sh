#!/bin/bash
# Port Forward Script for Music Charts Tracking
# Automatically forwards API and Dashboard services to localhost

set -e

NAMESPACE="music-charts"
API_PORT=8000
DASHBOARD_PORT=8501

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl is not installed.${NC}"
    exit 1
fi

# Check if namespace exists
if ! kubectl get namespace $NAMESPACE &> /dev/null; then
    echo -e "${RED}❌ Namespace '$NAMESPACE' does not exist.${NC}"
    echo "   Deploy first with: ./k8s/deploy.sh"
    exit 1
fi

# Check if services exist
if ! kubectl get svc api -n $NAMESPACE &> /dev/null; then
    echo -e "${RED}❌ API service not found in namespace '$NAMESPACE'.${NC}"
    exit 1
fi

if ! kubectl get svc dashboard -n $NAMESPACE &> /dev/null; then
    echo -e "${RED}❌ Dashboard service not found in namespace '$NAMESPACE'.${NC}"
    exit 1
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Stopping port forwarding...${NC}"
    kill $API_PID $DASHBOARD_PID 2>/dev/null || true
    wait $API_PID $DASHBOARD_PID 2>/dev/null || true
    echo -e "${GREEN}✅ Port forwarding stopped${NC}"
    exit 0
}

# Trap SIGINT and SIGTERM
trap cleanup SIGINT SIGTERM

echo -e "${GREEN}🚀 Starting Port Forwarding${NC}"
echo "============================================================"
echo ""
echo -e "📡 Forwarding services from namespace: ${YELLOW}$NAMESPACE${NC}"
echo ""

# Start API port forward in background
echo -e "${GREEN}🔌 Forwarding API:${NC} localhost:$API_PORT -> api:$API_PORT"
kubectl port-forward svc/api $API_PORT:$API_PORT -n $NAMESPACE > /dev/null 2>&1 &
API_PID=$!

# Small delay to ensure first port forward starts
sleep 1

# Start Dashboard port forward in background
echo -e "${GREEN}🔌 Forwarding Dashboard:${NC} localhost:$DASHBOARD_PORT -> dashboard:$DASHBOARD_PORT"
kubectl port-forward svc/dashboard $DASHBOARD_PORT:$DASHBOARD_PORT -n $NAMESPACE > /dev/null 2>&1 &
DASHBOARD_PID=$!

# Wait a moment to ensure both are running
sleep 2

# Verify both port forwards are running
if ps -p $API_PID > /dev/null && ps -p $DASHBOARD_PID > /dev/null; then
    echo ""
    echo -e "${GREEN}✅ Port forwarding active!${NC}"
    echo ""
    echo "📊 Access your services:"
    echo -e "   ${YELLOW}API:${NC}       http://localhost:$API_PORT"
    echo -e "   ${YELLOW}Dashboard:${NC} http://localhost:$DASHBOARD_PORT"
    echo ""
    echo -e "   API Health:      http://localhost:$API_PORT/health"
    echo -e "   API Docs:        http://localhost:$API_PORT/docs"
    echo ""
    echo -e "${YELLOW}Press Ctrl+C to stop port forwarding...${NC}"
    echo ""
    
    # Wait for both processes
    wait $API_PID $DASHBOARD_PID
else
    echo -e "${RED}❌ Failed to start port forwarding${NC}"
    cleanup
    exit 1
fi

