#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
PYTHON_BIN="${PYTHON_BIN:-python3}"
"$PYTHON_BIN" -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip pyinstaller "mido>=1.3,<2" "python-rtmidi>=1.5,<2" "pytest>=8,<10"
PYTHONPATH="$(pwd)/editor" python -m pytest tests -q
python -m PyInstaller --noconfirm --clean --windowed --onedir --name XGW-Next --hidden-import mido.backends.rtmidi --collect-submodules mido.backends --collect-submodules rtmidi --paths editor editor/app.py
echo "Application: $(pwd)/dist/XGW-Next.app"
