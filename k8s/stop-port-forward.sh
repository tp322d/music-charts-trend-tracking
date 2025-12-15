#!/bin/bash
# Stop Port Forwarding Script
# Stops background port forwarding processes

PID_FILE="port-forward.pids"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

if [ ! -f "$PID_FILE" ]; then
    echo -e "${YELLOW}⚠️  No port forwarding PIDs file found${NC}"
    echo "   Port forwarding may not be running in background mode"
    exit 0
fi

PIDS=$(cat $PID_FILE)
echo -e "${YELLOW}🛑 Stopping port forwarding (PIDs: $PIDS)...${NC}"

# Kill processes
for PID in $PIDS; do
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID 2>/dev/null && echo -e "${GREEN}✅ Stopped process $PID${NC}" || echo -e "${RED}❌ Failed to stop process $PID${NC}"
    else
        echo -e "${YELLOW}⚠️  Process $PID not running${NC}"
    fi
done

# Cleanup
rm -f $PID_FILE
echo -e "${GREEN}✅ Port forwarding stopped${NC}"

