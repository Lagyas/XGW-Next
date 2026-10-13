#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
PYTHON_BIN="${PYTHON_BIN:-python3}"
"$PYTHON_BIN" -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip pyinstaller "mido>=1.3,<2" "python-rtmidi>=1.5,<2"
python -m unittest discover -s tests -v
python -m PyInstaller --noconfirm --clean --windowed --onedir --name XGW-Next --paths editor editor/app.py
echo "Application: $(pwd)/dist/XGW-Next.app"
