#!/bin/bash
# Port Forward Script (Background)

set -e

NAMESPACE="music-charts"
API_PORT=8000
DASHBOARD_PORT=8501
PID_FILE="port-forward.pids"

# Colors
if ! command -v kubectl &> /dev/null; then
    echo "kubectl not installed"
    exit 1
fi

if [ -f "$PID_FILE" ]; then
    OLD_PIDS=$(cat $PID_FILE)
    if ps -p $OLD_PIDS > /dev/null 2>&1; then
        echo "port forward already running (pids: $OLD_PIDS)"
        echo "stop with: ./k8s/stop-port-forward.sh"
        exit 1
    else
        rm -f $PID_FILE
    fi
fi

if ! kubectl get namespace $NAMESPACE &> /dev/null; then
    echo "namespace not found"
    exit 1
fi

echo "start port forward (bg)"
echo "======================="

# Start API port forward
echo "forward api: localhost:$API_PORT -> api:$API_PORT"
kubectl port-forward svc/api $API_PORT:$API_PORT -n $NAMESPACE > /tmp/api-port-forward.log 2>&1 &
API_PID=$!

sleep 1

# Start Dashboard port forward
echo "forward dashboard: localhost:$DASHBOARD_PORT -> dashboard:$DASHBOARD_PORT"
kubectl port-forward svc/dashboard $DASHBOARD_PORT:$DASHBOARD_PORT -n $NAMESPACE > /tmp/dashboard-port-forward.log 2>&1 &
DASHBOARD_PID=$!

# Save PIDs to file
echo "$API_PID $DASHBOARD_PID" > $PID_FILE

sleep 2

if ps -p $API_PID > /dev/null && ps -p $DASHBOARD_PID > /dev/null; then
    echo ""
    echo "port forward started in bg"
    echo ""
    echo "access:"
    echo "   api:       http://localhost:$API_PORT"
    echo "   dashboard: http://localhost:$DASHBOARD_PORT"
    echo ""
    echo "pids file: $PID_FILE"
    echo "logs:"
    echo "   api:       /tmp/api-port-forward.log"
    echo "   dashboard: /tmp/dashboard-port-forward.log"
    echo ""
    echo "stop with: ./k8s/stop-port-forward.sh"
else
    echo "port forward failed"
    kill $API_PID $DASHBOARD_PID 2>/dev/null || true
    rm -f $PID_FILE
    exit 1
fi

