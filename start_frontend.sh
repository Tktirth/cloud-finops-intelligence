#!/bin/bash
# ─────────────────────────────────────────────
# Cloud FinOps Intelligence — Frontend Startup
# ─────────────────────────────────────────────
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

echo "🎨 Cloud FinOps Intelligence Frontend"
echo "======================================"

cd "$FRONTEND_DIR"

if [ ! -d "node_modules" ]; then
    echo "📦 Installing npm dependencies..."
    npm install
fi

echo ""
echo "🌐 Starting React dev server on http://localhost:5173"
echo ""
npm run dev
