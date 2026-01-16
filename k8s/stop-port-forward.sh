#!/bin/bash
# Stop Port Forward Script

PID_FILE="port-forward.pids"

# Colors
if [ ! -f "$PID_FILE" ]; then
    echo "no pid file found"
    echo "port forward maybe not running"
    exit 0
fi

PIDS=$(cat $PID_FILE)
echo "stop port forward (pids: $PIDS)"

# Kill processes
for PID in $PIDS; do
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID 2>/dev/null && echo "stopped $PID" || echo "stop failed $PID"
    else
        echo "process $PID not running"
    fi
done

# Cleanup
rm -f $PID_FILE
echo "port forward stopped"

