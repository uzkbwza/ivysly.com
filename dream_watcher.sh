#!/bin/bash
cd "$(dirname "$0")"

while true; do
    echo "Starting dream_watcher.py ..."
    python dream_watcher.py
    echo "dream_watcher.py exited. Restarting in 5 seconds..."
    sleep 5
done
