#!/bin/bash
cd "$(dirname "$0")"
echo "rebuilding site..."
./venv/bin/python -m ivygen build
echo "deploying site..."
sshpass -p "REDACTED" rsync -avp output/* root@168.235.86.185:/var/www/ivysly.com/public_html --delete
