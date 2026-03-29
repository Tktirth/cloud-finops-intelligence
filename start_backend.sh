#!/bin/bash
# ─────────────────────────────────────────────
# Cloud FinOps Intelligence — Backend Startup
# ─────────────────────────────────────────────
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"

echo "🚀 Cloud FinOps Intelligence Backend"
echo "======================================"

# Create venv if needed
if [ ! -d "$BACKEND_DIR/.venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv "$BACKEND_DIR/.venv"
fi

source "$BACKEND_DIR/.venv/bin/activate"
echo "📦 Installing dependencies (first run may take a few minutes)..."
pip install -q -r "$BACKEND_DIR/requirements.txt"

echo ""
echo "🔧 Starting FastAPI server on http://localhost:8000"
echo "   API docs: http://localhost:8000/docs"
echo "   (ML pipeline will run on startup — takes ~2-3 minutes)"
echo ""

cd "$BACKEND_DIR"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
