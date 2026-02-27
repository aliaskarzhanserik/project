#!/usr/bin/env bash
set -e

# Simple launcher for macOS: creates venv, installs deps, initializes DB, starts server and opens browser
PORT=${PORT:-5001}

echo "Starting PDD site launcher..."

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required. Install Python 3 and retry." >&2
  exit 1
fi

if [ ! -d "venv" ]; then
  echo "Creating virtualenv..."
  python3 -m venv venv
fi

echo "Activating virtualenv and installing requirements..."
. venv/bin/activate
pip3 install --upgrade pip || true
pip3 install -r requirements.txt

if [ ! -f data/database.db ]; then
  echo "Initializing database..."
  python3 app/init_db.py
fi

echo "Starting Flask server on port $PORT (logs -> server.log)"
export PORT=$PORT
nohup python3 app/app.py > server.log 2>&1 &
sleep 1

echo "Opening browser..."
open "http://localhost:$PORT"

echo "Done. Visit http://localhost:$PORT"
