#!/bin/bash
# Port Forward Script (Background Mode)
# Starts port forwarding in background and saves PIDs to file

set -e

NAMESPACE="music-charts"
API_PORT=8000
DASHBOARD_PORT=8501
PID_FILE="port-forward.pids"

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

# Check if already running
if [ -f "$PID_FILE" ]; then
    OLD_PIDS=$(cat $PID_FILE)
    if ps -p $OLD_PIDS > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Port forwarding already running (PIDs: $OLD_PIDS)${NC}"
        echo "   Stop with: ./k8s/stop-port-forward.sh"
        exit 1
    else
        rm -f $PID_FILE
    fi
fi

# Check if namespace exists
if ! kubectl get namespace $NAMESPACE &> /dev/null; then
    echo -e "${RED}❌ Namespace '$NAMESPACE' does not exist.${NC}"
    exit 1
fi

echo -e "${GREEN}🚀 Starting Port Forwarding (Background Mode)${NC}"
echo "============================================================"

# Start API port forward
echo -e "${GREEN}🔌 Forwarding API:${NC} localhost:$API_PORT -> api:$API_PORT"
kubectl port-forward svc/api $API_PORT:$API_PORT -n $NAMESPACE > /tmp/api-port-forward.log 2>&1 &
API_PID=$!

sleep 1

# Start Dashboard port forward
echo -e "${GREEN}🔌 Forwarding Dashboard:${NC} localhost:$DASHBOARD_PORT -> dashboard:$DASHBOARD_PORT"
kubectl port-forward svc/dashboard $DASHBOARD_PORT:$DASHBOARD_PORT -n $NAMESPACE > /tmp/dashboard-port-forward.log 2>&1 &
DASHBOARD_PID=$!

# Save PIDs to file
echo "$API_PID $DASHBOARD_PID" > $PID_FILE

sleep 2

# Verify they're running
if ps -p $API_PID > /dev/null && ps -p $DASHBOARD_PID > /dev/null; then
    echo ""
    echo -e "${GREEN}✅ Port forwarding started in background!${NC}"
    echo ""
    echo "📊 Access your services:"
    echo -e "   ${YELLOW}API:${NC}       http://localhost:$API_PORT"
    echo -e "   ${YELLOW}Dashboard:${NC} http://localhost:$DASHBOARD_PORT"
    echo ""
    echo "📝 PIDs saved to: $PID_FILE"
    echo "📋 Logs:"
    echo "   API:       /tmp/api-port-forward.log"
    echo "   Dashboard: /tmp/dashboard-port-forward.log"
    echo ""
    echo "🛑 Stop with: ./k8s/stop-port-forward.sh"
else
    echo -e "${RED}❌ Failed to start port forwarding${NC}"
    kill $API_PID $DASHBOARD_PID 2>/dev/null || true
    rm -f $PID_FILE
    exit 1
fi

