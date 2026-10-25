#!/bin/bash

clear

echo ""
echo "============================================================"
echo "  Literate Lamp - Starting Application"
echo "============================================================"
echo ""

# ============================================================
# GO TO SCRIPT DIRECTORY
# ============================================================

cd "$(dirname "$0")"

# ============================================================
# CHECK PYTHON VENV
# ============================================================

if [ ! -d "venv" ]; then
    echo "ERROR: Virtual environment not found!"
    echo ""
    echo "Run setup-python.sh first."
    echo ""
    read -p "Press Enter to continue..."
    exit 1
fi

# Activate venv
source venv/bin/activate

if [ $? -ne 0 ]; then
    echo "Failed to activate virtual environment"
    echo ""
    read -p "Press Enter to continue..."
    exit 1
fi

echo "[OK] Python environment ready"
echo ""

# ============================================================
# CREATE .ENV IF NOT EXISTS
# ============================================================

if [ ! -f ".env" ]; then

    echo "Creating .env..."

    cat > .env << EOF
# Auto generated
# Managed by GUI
EOF

    echo "[OK] .env created"
    echo ""
fi

# ============================================================
# CHECK NODE.JS
# ============================================================

if ! command -v node >/dev/null 2>&1; then
    echo "ERROR: Node.js not installed"
    echo ""
    echo "Install Node.js:"
    echo "https://nodejs.org/"
    echo ""
    read -p "Press Enter to continue..."
    exit 1
fi

echo "[OK] Node.js detected"
echo ""

# ============================================================
# CHECK FRONTEND
# ============================================================

if [ ! -d "frontend" ]; then
    echo "ERROR: frontend folder not found"
    echo ""
    read -p "Press Enter to continue..."
    exit 1
fi

cd frontend

# ============================================================
# INSTALL FRONTEND DEPENDENCIES
# ============================================================

if [ ! -d "node_modules" ]; then

    echo "Installing frontend dependencies..."
    echo ""

    npm install

    if [ $? -ne 0 ]; then
        echo ""
        echo "Failed to install frontend dependencies"
        cd ..
        read -p "Press Enter to continue..."
        exit 1
    fi
fi

cd ..

echo "[OK] Frontend ready"
echo ""

# ============================================================
# START BACKEND
# ============================================================

echo "Starting backend..."

gnome-terminal -- bash -c "
cd backend
source ../venv/bin/activate
python -m uvicorn main:app --reload --port 8000
exec bash
" 2>/dev/null &

# fallback kalau gnome-terminal tidak ada
if [ $? -ne 0 ]; then
    xterm -e "
cd backend
source ../venv/bin/activate
python -m uvicorn main:app --reload --port 8000
bash
" &
fi

sleep 3

# ============================================================
# START FRONTEND
# ============================================================

echo "Starting frontend..."

gnome-terminal -- bash -c "
cd frontend
npm run dev
exec bash
" 2>/dev/null &

if [ $? -ne 0 ]; then
    xterm -e "
cd frontend
npm run dev
bash
" &
fi

sleep 2

# ============================================================
# OPEN BROWSER
# ============================================================

xdg-open http://localhost:5173 >/dev/null 2>&1 &

echo ""
echo "============================================================"
echo "  Literate Lamp Running"
echo "============================================================"
echo ""
echo "Backend  : http://localhost:8000"
echo "Frontend : http://localhost:5173"
echo ""

read -p "Press Enter to exit..."
